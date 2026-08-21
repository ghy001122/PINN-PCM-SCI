"""Transparent strong-form Q-POP PINN used by raw-time and KC methods."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

import torch
from torch import nn

from .kinetics_clock import (
    IdentityClock,
    PositiveGaussianClock,
    StructuralKineticsClockPINN,
    full_pullback,
    make_mlp,
)
from .qpop_physics import QPopParameters, dfermi, fermi
from .phase_hotspot import PhaseHotspotOutput, SharedPhaseHotspotRepresentation


FIELD_NAMES = ("eta", "mu", "gamma_e", "gamma_h", "phi", "temperature", "current")
PHA_METHODS = ("fourier_global", "pha_capacity", "pha_sampling", "pha_shared")


class _EtaField(nn.Module):
    def __init__(self, *, hidden_width: int, hidden_layers: int, initial: float) -> None:
        super().__init__()
        self.network = make_mlp(3, 1, hidden_width=hidden_width, hidden_layers=hidden_layers)
        self.scale = 1.6
        final = self.network[-1]
        assert isinstance(final, nn.Linear)
        nn.init.normal_(final.weight, mean=0.0, std=1.0e-2)
        nn.init.zeros_(final.bias)
        normalized_initial = float(initial / self.scale)
        if not -1.0 < normalized_initial < 1.0:
            raise ValueError("eta initial value must fit inside the bounded representation")
        self.register_buffer(
            "initial_latent",
            torch.atanh(torch.tensor(normalized_initial, dtype=torch.float64)),
        )

    def forward(self, coordinates: torch.Tensor) -> torch.Tensor:
        if coordinates.ndim != 2 or coordinates.shape[1] != 3:
            raise ValueError("eta coordinates must contain normalized x, y, and time")
        time = coordinates[:, 2:3]
        latent = self.initial_latent.to(coordinates) + time * self.network(coordinates)
        return self.scale * torch.tanh(latent)


class _PhysicalFields(nn.Module):
    def __init__(
        self,
        *,
        hidden_width: int,
        hidden_layers: int,
        parameters: QPopParameters,
    ) -> None:
        super().__init__()
        self.network = make_mlp(3, 6, hidden_width=hidden_width, hidden_layers=hidden_layers)
        self.mu_scale = 1.6
        self.gamma_scale = 20.0
        self.phi_scale = parameters.drive_voltage
        self.temperature_scale = 0.5
        self.temperature_center = parameters.substrate_temperature
        self.current_scale = max(
            abs(parameters.current_initial) * 5.0,
            abs(parameters.drive_voltage / parameters.resistor) * 5.0,
            1.0e-12,
        )
        initial = torch.tensor(
            [
                parameters.mu_initial / self.mu_scale,
                parameters.gamma_e_initial / self.gamma_scale,
                parameters.gamma_h_initial / self.gamma_scale,
                parameters.phi_initial / self.phi_scale,
                (parameters.temperature_initial - self.temperature_center)
                / self.temperature_scale,
                parameters.current_initial / self.current_scale,
            ]
        ).clamp(-0.999999, 0.999999)
        final = self.network[-1]
        assert isinstance(final, nn.Linear)
        nn.init.normal_(final.weight, mean=0.0, std=1.0e-3)
        with torch.no_grad():
            final.bias.copy_(torch.atanh(initial))

    def forward(self, coordinates: torch.Tensor) -> torch.Tensor:
        latent = torch.tanh(self.network(coordinates))
        return torch.stack(
            [
                self.mu_scale * latent[:, 0],
                self.gamma_scale * latent[:, 1],
                self.gamma_scale * latent[:, 2],
                self.phi_scale * latent[:, 3],
                self.temperature_center + self.temperature_scale * latent[:, 4],
                self.current_scale * latent[:, 5],
            ],
            dim=1,
        )


class QPopPINN(nn.Module):
    """Seven-unknown Q-POP model with a structural-only optional time clock."""

    def __init__(
        self,
        *,
        parameters: QPopParameters,
        horizon_ns: float,
        method: str,
        hidden_width: int,
        hidden_layers: int,
        clock_centers: tuple[float, ...] = (0.15, 0.35, 0.55, 0.75, 0.9),
        clock_width: float = 0.12,
        kappa_floor: float = 0.1,
    ) -> None:
        super().__init__()
        if method not in {"raw", "identity", "kc", *PHA_METHODS}:
            raise ValueError(
                "Q-POP PINN method must be raw, identity, kc, fourier_global, "
                "pha_capacity, pha_sampling, or pha_shared"
            )
        if horizon_ns <= 0.0:
            raise ValueError("training horizon must be positive")
        self.parameters_contract = parameters
        self.horizon_ns = float(horizon_ns)
        self.method = method
        self.eta_model = _EtaField(
            hidden_width=hidden_width,
            hidden_layers=hidden_layers,
            initial=parameters.eta_initial,
        )
        self.physical_model = _PhysicalFields(
            hidden_width=hidden_width,
            hidden_layers=hidden_layers,
            parameters=parameters,
        )
        if method in PHA_METHODS:
            self.phase_hotspot: SharedPhaseHotspotRepresentation | None = (
                SharedPhaseHotspotRepresentation(
                    parameters=parameters,
                    hidden_width=hidden_width,
                    hidden_layers=hidden_layers,
                )
            )
        else:
            self.phase_hotspot = None
        self.sampling_gain = 3.0
        if method == "kc":
            self.clock: nn.Module = PositiveGaussianClock(
                spatial_dim=2,
                centers=clock_centers,
                widths=(clock_width,) * len(clock_centers),
                kappa_floor=kappa_floor,
                hidden_width=max(4, hidden_width // 2),
            )
        else:
            self.clock = IdentityClock()
        self.architecture = StructuralKineticsClockPINN(
            clock=self.clock,
            eta_model=self.eta_model,
            physical_field_model=self.physical_model,
        )

    def forward(self, coordinates: torch.Tensor) -> torch.Tensor:
        if self.method in PHA_METHODS:
            return self.phase_hotspot_diagnostics(coordinates).fields
        output = self.architecture(coordinates)
        return torch.cat([output.eta, output.physical_fields], dim=1)

    def phase_hotspot_diagnostics(
        self, coordinates: torch.Tensor
    ) -> PhaseHotspotOutput:
        if self.method not in PHA_METHODS or self.phase_hotspot is None:
            raise ValueError("phase-hotspot diagnostics require a PHA method")
        base_fields = torch.cat(
            [self.eta_model(coordinates), self.physical_model(coordinates)], dim=1
        )
        return self.phase_hotspot(
            coordinates,
            base_fields,
            gate_capacity=self.method in {"pha_capacity", "pha_shared"},
        )

    def collocation_weights(self, coordinates: torch.Tensor) -> torch.Tensor:
        diagnostics = self.phase_hotspot_diagnostics(coordinates)
        if self.method in {"pha_sampling", "pha_shared"}:
            return 1.0 + self.sampling_gain * diagnostics.physical_gate
        return torch.ones_like(diagnostics.physical_gate)

    def select_interior(
        self, candidates: torch.Tensor, *, count: int
    ) -> torch.Tensor:
        if count <= 0 or count > candidates.shape[0]:
            raise ValueError("selected collocation count must fit the candidate pool")
        with torch.no_grad():
            weights = self.collocation_weights(candidates)[:, 0]
            indices = torch.topk(weights, k=count, largest=True, sorted=True).indices
        return candidates[indices]


@dataclass(frozen=True)
class FieldBundle:
    coordinates: torch.Tensor
    values: Mapping[str, torch.Tensor]
    gradients: Mapping[str, torch.Tensor]
    hessians: Mapping[str, torch.Tensor]


def _gradient(value: torch.Tensor, coordinates: torch.Tensor) -> torch.Tensor:
    result = torch.autograd.grad(
        value,
        coordinates,
        grad_outputs=torch.ones_like(value),
        create_graph=True,
        retain_graph=True,
        allow_unused=True,
    )[0]
    return torch.zeros_like(coordinates) if result is None else result


def _hessian(gradient: torch.Tensor, coordinates: torch.Tensor) -> torch.Tensor:
    return torch.stack(
        [_gradient(gradient[:, index : index + 1], coordinates) for index in range(3)],
        dim=1,
    )


def evaluate_fields(model: QPopPINN, coordinates: torch.Tensor) -> FieldBundle:
    q = coordinates
    if not q.requires_grad:
        q = coordinates.detach().clone().requires_grad_(True)
    scale = torch.tensor(
        [
            1.0 / model.parameters_contract.lx,
            1.0 / model.parameters_contract.ly,
            1.0 / model.horizon_ns,
        ],
        dtype=q.dtype,
        device=q.device,
    )
    if model.method in PHA_METHODS:
        fields = model.phase_hotspot_diagnostics(q).fields
        values = {}
        gradients = {}
        hessians = {}
        for index, name in enumerate(FIELD_NAMES):
            value = fields[:, index : index + 1]
            gradient_q = _gradient(value, q)
            hessian_q = _hessian(gradient_q, q)
            values[name] = value
            gradients[name] = gradient_q * scale
            hessians[name] = (
                hessian_q * scale[None, :, None] * scale[None, None, :]
            )
        return FieldBundle(q, values, gradients, hessians)
    if model.method == "raw":
        eta = model.eta_model(q)
        eta_gradient_q = _gradient(eta, q)
        eta_hessian_q = _hessian(eta_gradient_q, q)
    else:
        pullback = full_pullback(model.eta_model, model.clock, q)
        eta = pullback.value
        eta_gradient_q = pullback.physical_gradient
        eta_hessian_q = pullback.physical_hessian
    physical = model.physical_model(q)
    values: dict[str, torch.Tensor] = {"eta": eta}
    gradients: dict[str, torch.Tensor] = {"eta": eta_gradient_q * scale}
    hessians: dict[str, torch.Tensor] = {
        "eta": eta_hessian_q * scale[None, :, None] * scale[None, None, :]
    }
    for index, name in enumerate(FIELD_NAMES[1:]):
        value = physical[:, index : index + 1]
        gradient_q = _gradient(value, q)
        hessian_q = _hessian(gradient_q, q)
        values[name] = value
        gradients[name] = gradient_q * scale
        hessians[name] = hessian_q * scale[None, :, None] * scale[None, None, :]
    return FieldBundle(q, values, gradients, hessians)


def _physical_gradient(
    value: torch.Tensor, bundle: FieldBundle, model: QPopPINN
) -> torch.Tensor:
    scale = torch.tensor(
        [
            1.0 / model.parameters_contract.lx,
            1.0 / model.parameters_contract.ly,
            1.0 / model.horizon_ns,
        ],
        dtype=bundle.coordinates.dtype,
        device=bundle.coordinates.device,
    )
    return _gradient(value, bundle.coordinates) * scale


def _derived(
    model: QPopPINN, bundle: FieldBundle
) -> dict[str, torch.Tensor]:
    p = model.parameters_contract
    v = bundle.values
    electron_density = p.electron_density_of_states * fermi(v["gamma_e"])
    hole_density = p.hole_density_of_states * fermi(v["gamma_h"])
    electron_potential = (
        p.kb * v["temperature"] * v["gamma_e"]
        + p.chi * v["mu"].square() / 2.0
        - p.charge * v["phi"]
    )
    hole_potential = (
        p.kb * v["temperature"] * v["gamma_h"]
        + p.chi * v["mu"].square() / 2.0
        + p.charge * v["phi"]
    )
    grad_e = _physical_gradient(electron_potential, bundle, model)[:, :2]
    grad_h = _physical_gradient(hole_potential, bundle, model)[:, :2]
    mobility_e = torch.tensor(
        [p.electron_mobility_x, p.electron_mobility_y],
        dtype=grad_e.dtype,
        device=grad_e.device,
    )
    mobility_h = torch.tensor(
        [p.hole_mobility_x, p.hole_mobility_y],
        dtype=grad_h.dtype,
        device=grad_h.device,
    )
    electron_flux = -electron_density * (mobility_e / p.charge) * grad_e
    hole_flux = -hole_density * (mobility_h / p.charge) * grad_h
    return {
        "electron_density": electron_density,
        "hole_density": hole_density,
        "electron_flux": electron_flux,
        "hole_flux": hole_flux,
        "current_y": p.charge * (hole_flux[:, 1:2] - electron_flux[:, 1:2]),
    }


def interior_residuals(
    model: QPopPINN, coordinates: torch.Tensor
) -> dict[str, torch.Tensor]:
    bundle = evaluate_fields(model, coordinates)
    p = model.parameters_contract
    v, g, h = bundle.values, bundle.gradients, bundle.hessians
    derived = _derived(model, bundle)
    ne = derived["electron_density"]
    nh = derived["hole_density"]
    je = derived["electron_flux"]
    jh = derived["hole_flux"]
    div_je = _physical_gradient(je[:, 0:1], bundle, model)[:, 0:1] + _physical_gradient(
        je[:, 1:2], bundle, model
    )[:, 1:2]
    div_jh = _physical_gradient(jh[:, 0:1], bundle, model)[:, 0:1] + _physical_gradient(
        jh[:, 1:2], bundle, model
    )[:, 1:2]
    physical_xy = torch.stack(
        [bundle.coordinates[:, 0] * p.lx, bundle.coordinates[:, 1] * p.ly], dim=1
    )
    tcvar = p.tc_variance(physical_xy).unsqueeze(1)
    intrinsic = p.electron_density_of_states * fermi(
        -(p.chi * v["mu"].square() / 2.0) / (p.kb * v["temperature"])
    )
    electron_eq = p.electron_density_of_states * fermi(
        -(
            p.chi * v["mu"].square() / 2.0
            - p.charge * v["phi"]
        )
        / (p.kb * v["temperature"])
    )
    hole_eq = p.hole_density_of_states * fermi(
        -(
            p.chi * v["mu"].square() / 2.0
            + p.charge * v["phi"]
        )
        / (p.kb * v["temperature"])
    )
    reaction = p.recombination_rate * v["mu"].square() * (
        electron_eq * hole_eq - ne * nh
    )
    df_eta = p.dfb_deta(v["temperature"], v["eta"], v["mu"], tcvar)
    df_mu = p.dfb_dmu(v["temperature"], v["eta"], v["mu"], tcvar)
    lap_eta = h["eta"][:, 0, 0:1] + h["eta"][:, 1, 1:2]
    lap_mu = h["mu"][:, 0, 0:1] + h["mu"][:, 1, 1:2]
    lap_phi = h["phi"][:, 0, 0:1] + h["phi"][:, 1, 1:2]
    lap_temperature = h["temperature"][:, 0, 0:1] + h["temperature"][:, 1, 1:2]
    df_eta_zero_t = p.dfb_deta(
        torch.zeros_like(v["temperature"]), v["eta"], v["mu"], tcvar
    )
    df_mu_zero_t = p.dfb_dmu(
        torch.zeros_like(v["temperature"]), v["eta"], v["mu"], tcvar
    )
    internal_energy_rate = (
        df_eta_zero_t * g["eta"][:, 2:3]
        + df_mu_zero_t * g["mu"][:, 2:3]
    )
    flux_difference = jh - je
    joule = p.charge * (
        flux_difference[:, 0:1].square()
        / (ne * p.electron_mobility_x + nh * p.hole_mobility_x + 1.0e-30)
        + flux_difference[:, 1:2].square()
        / (ne * p.electron_mobility_y + nh * p.hole_mobility_y + 1.0e-30)
    )
    return {
        "eta": g["eta"][:, 2:3]
        + 2.0 * p.structural_mobility * df_eta
        - p.structural_mobility * p.structural_gradient * lap_eta,
        "mu": g["mu"][:, 2:3]
        + 2.0
        * p.electronic_mobility
        * (df_mu + p.chi * v["mu"] * (ne + nh - 2.0 * intrinsic))
        - p.electronic_mobility * p.electronic_gradient * lap_mu,
        "electron": p.electron_density_of_states
        * dfermi(v["gamma_e"])
        * g["gamma_e"][:, 2:3]
        + div_je
        - reaction,
        "hole": p.hole_density_of_states
        * dfermi(v["gamma_h"])
        * g["gamma_h"][:, 2:3]
        + div_jh
        - reaction,
        "poisson": -lap_phi - p.charge / p.permittivity * (nh - ne),
        "temperature": p.volumetric_heat_capacity * g["temperature"][:, 2:3]
        - joule
        + internal_energy_rate
        - p.thermal_conductivity * lap_temperature
        + p.heat_transfer / p.lz * (v["temperature"] - p.substrate_temperature),
        "current_uniform_x": g["current"][:, 0:1],
        "current_uniform_y": g["current"][:, 1:2],
    }


def initial_residuals(model: QPopPINN, spatial_coordinates: torch.Tensor) -> dict[str, torch.Tensor]:
    if spatial_coordinates.shape[1] != 2:
        raise ValueError("initial coordinates must have two normalized spatial columns")
    q = torch.cat(
        [spatial_coordinates, torch.zeros_like(spatial_coordinates[:, 0:1])], dim=1
    )
    values = evaluate_fields(model, q).values
    p = model.parameters_contract
    expected_phi = p.phi_initial * (1.0 - spatial_coordinates[:, 1:2])
    return {
        "ic_eta": values["eta"] - p.eta_initial,
        "ic_mu": values["mu"] - p.mu_initial,
        "ic_gamma_e": values["gamma_e"] - p.gamma_e_initial,
        "ic_gamma_h": values["gamma_h"] - p.gamma_h_initial,
        "ic_phi": values["phi"] - expected_phi,
        "ic_temperature": values["temperature"] - p.temperature_initial,
        "ic_current": values["current"] - p.current_initial,
    }


def boundary_residuals(
    model: QPopPINN, coordinates: torch.Tensor, *, side: str
) -> dict[str, torch.Tensor]:
    if side not in {"left", "right", "bottom", "top"}:
        raise ValueError("boundary side must be left, right, bottom, or top")
    bundle = evaluate_fields(model, coordinates)
    p = model.parameters_contract
    v, g = bundle.values, bundle.gradients
    derived = _derived(model, bundle)
    normal = {
        "left": (-1.0, 0.0),
        "right": (1.0, 0.0),
        "bottom": (0.0, -1.0),
        "top": (0.0, 1.0),
    }[side]
    n_eta = normal[0] * g["eta"][:, 0:1] + normal[1] * g["eta"][:, 1:2]
    n_mu = normal[0] * g["mu"][:, 0:1] + normal[1] * g["mu"][:, 1:2]
    n_temperature = normal[0] * g["temperature"][:, 0:1] + normal[1] * g[
        "temperature"
    ][:, 1:2]
    result = {
        "bc_eta_robin": n_eta - (p.eta_surrounding - v["eta"]) / p.effective_boundary_length,
        "bc_mu_robin": n_mu - (p.mu_surrounding - v["mu"]) / p.effective_boundary_length,
        "bc_temperature_insulated": n_temperature,
    }
    if side in {"left", "right"}:
        result.update(
            {
                "bc_electron_no_flux": normal[0] * derived["electron_flux"][:, 0:1],
                "bc_hole_no_flux": normal[0] * derived["hole_flux"][:, 0:1],
                "bc_phi_no_flux": normal[0] * g["phi"][:, 0:1],
            }
        )
    else:
        result.update(
            {
                "bc_gamma_e_equilibrium": p.kb * v["temperature"] * v["gamma_e"]
                + p.chi * v["mu"].square() / 2.0,
                "bc_gamma_h_equilibrium": p.kb * v["temperature"] * v["gamma_h"]
                + p.chi * v["mu"].square() / 2.0,
            }
        )
        if side == "top":
            result["bc_phi_top"] = v["phi"]
        else:
            physical_time = bundle.coordinates[:, 2:3] * model.horizon_ns
            result["bc_circuit_voltage"] = (
                v["phi"]
                + p.resistor * v["current"]
                - p.ramped_voltage(physical_time)
                + p.resistor * p.capacitor * g["phi"][:, 2:3]
            )
            result["bc_circuit_current"] = v["current"] - p.lx * p.lz * derived[
                "current_y"
            ]
    return result


def normalized_residual_loss(
    residuals: Mapping[str, torch.Tensor],
    scales: Mapping[str, float] | None = None,
) -> torch.Tensor:
    losses: list[torch.Tensor] = []
    for name, residual in residuals.items():
        if scales is None:
            scale = torch.sqrt(torch.mean(residual.detach().square())).clamp_min(1.0e-12)
        else:
            scale = torch.as_tensor(
                max(float(scales[name]), 1.0e-12),
                dtype=residual.dtype,
                device=residual.device,
            )
        losses.append(torch.mean((residual / scale).square()))
    return torch.stack(losses).mean()


def residual_scales(residuals: Mapping[str, torch.Tensor]) -> dict[str, float]:
    return {
        name: max(float(torch.sqrt(torch.mean(value.detach().square())).cpu()), 1.0e-12)
        for name, value in residuals.items()
    }
