"""Three-field strong-form PINN core for the PHK-V2.2R sprint.

The module deliberately depends on the frozen PHK-V2.1 physical contract but is
scientifically independent of its finite-volume implementation.  No reference
field is accepted by any model, residual, boundary, or collocation API in this
file.  Reference carriers are local evaluator inputs only.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Mapping, Sequence

import torch
from torch import nn

from .phk_benchmark import PhkPhysicalContract
from .phk_v21_benchmark import PhkV21CaseSpec


FIELD_NAMES = ("potential", "temperature", "phase")
POTENTIAL_TRANSFORM_LEGACY = "LEGACY_WAVEFORM_SIGMOID"
POTENTIAL_TRANSFORM_TOP_DIRICHLET_HARD_LIFT = "TOP_DIRICHLET_HARD_LIFT"
PHASE_TRANSFORM_LEGACY = "LEGACY_FIXED_LATENT_SCALE"
PHASE_TRANSFORM_JACOBIAN_NORMALIZED = "JACOBIAN_NORMALIZED_CAP_32"


class PhkV22RArm(str, Enum):
    """Predeclared representation/sampling arms."""

    STRONG_RAW = "STRONG_RAW"
    MF_ONLY = "MF_ONLY"
    SAMPLER_ONLY = "SAMPLER_ONLY"
    MF_PLUS_SAMPLER = "MF_PLUS_SAMPLER"
    STRICT_PHA_PROBE = "STRICT_PHA_PROBE"

    @property
    def uses_multifrequency(self) -> bool:
        return self in {
            PhkV22RArm.MF_ONLY,
            PhkV22RArm.MF_PLUS_SAMPLER,
            PhkV22RArm.STRICT_PHA_PROBE,
        }

    @property
    def uses_physics_sampler(self) -> bool:
        return self in {
            PhkV22RArm.SAMPLER_ONLY,
            PhkV22RArm.MF_PLUS_SAMPLER,
            PhkV22RArm.STRICT_PHA_PROBE,
        }


@dataclass(frozen=True)
class FrequencyBand:
    """Fixed axis-aligned Fourier frequencies in normalized coordinates."""

    band_id: str
    x: tuple[float, ...]
    z: tuple[float, ...]
    t: tuple[float, ...]

    @classmethod
    def band_a(cls) -> "FrequencyBand":
        return cls(
            band_id="BAND_A",
            x=(1.0, 2.0, 4.0, 8.0, 12.0, 24.0),
            z=(1.0, 2.0, 4.0, 8.0, 12.0, 24.0),
            t=(1.0, 2.0, 4.0, 8.0),
        )

    @classmethod
    def conservative(cls) -> "FrequencyBand":
        return cls(
            band_id="BAND_B_CONSERVATIVE",
            x=(1.0, 2.0, 4.0, 8.0, 12.0),
            z=(1.0, 2.0, 4.0, 8.0, 12.0),
            t=(1.0, 2.0, 4.0),
        )


@dataclass(frozen=True)
class PhkV22RPhysics:
    """Materialized continuous equations and boundary data for one PHK case."""

    x_min: float
    x_max: float
    z_min: float
    z_max: float
    time_start: float
    time_end: float
    period: float
    heater_width_fraction: float
    waveform_amplitude: float
    ramp_up_end: float
    hold_end: float
    ramp_down_end: float
    thermal_diffusivity: float
    volumetric_cooling: float
    latent_ratio: float
    joule_gain: float
    conductivity_phase_ratio: float
    conductivity_temperature_gain: float
    interface_width: float
    barrier_scale: float
    thermal_drive: float
    theta_transition: float
    mobility_cold: float
    mobility_hot: float
    mobility_width: float
    thermal_robin_biot: float
    initial_phase_background: float
    initial_seed_excess: float
    initial_seed_sigma_x: float
    initial_seed_sigma_z: float
    initial_seed_center_x: float
    initial_seed_center_z: float

    @classmethod
    def from_contract(
        cls,
        physical: PhkPhysicalContract,
        case: PhkV21CaseSpec,
    ) -> "PhkV22RPhysics":
        case.validate(physical)
        coordinates = physical.coordinates
        coefficients = physical.coefficients
        geometry = physical.payload["geometry"]
        waveform = physical.payload["waveform"]
        return cls(
            x_min=float(coordinates["x_min"]),
            x_max=float(coordinates["x_max"]),
            z_min=float(coordinates["z_min"]),
            z_max=float(coordinates["z_max"]),
            time_start=float(coordinates["time_start"]),
            time_end=float(coordinates["time_end"]),
            period=float(case.period),
            heater_width_fraction=float(case.heater_width_fraction),
            waveform_amplitude=float(case.waveform_amplitude),
            ramp_up_end=float(waveform["ramp_up_end"]),
            hold_end=float(case.pulse_hold_end),
            ramp_down_end=float(waveform["ramp_down_end"]),
            thermal_diffusivity=float(coefficients["thermal_diffusivity"]),
            volumetric_cooling=float(case.volumetric_cooling),
            latent_ratio=float(case.latent_ratio),
            joule_gain=float(coefficients["joule_gain"]),
            conductivity_phase_ratio=float(
                coefficients["conductivity_phase_ratio"]
            ),
            conductivity_temperature_gain=float(
                coefficients["conductivity_temperature_gain"]
            ),
            interface_width=float(case.interface_width),
            barrier_scale=float(coefficients["barrier_scale"]),
            thermal_drive=float(case.thermal_drive),
            theta_transition=float(coefficients["theta_transition"]),
            mobility_cold=float(case.mobility_cold),
            mobility_hot=float(case.mobility_hot),
            mobility_width=float(coefficients["mobility_width"]),
            thermal_robin_biot=float(geometry["thermal_robin_biot"]),
            initial_phase_background=float(case.initial_phase_background),
            initial_seed_excess=float(coefficients["initial_seed_excess"]),
            initial_seed_sigma_x=float(coefficients["initial_seed_sigma_x"]),
            initial_seed_sigma_z=float(coefficients["initial_seed_sigma_z"]),
            initial_seed_center_x=float(coefficients["initial_seed_center_x"]),
            initial_seed_center_z=float(coefficients["initial_seed_center_z"]),
        )

    @property
    def heater_half_width(self) -> float:
        return 0.5 * (self.x_max - self.x_min) * self.heater_width_fraction

    def normalize(self, coordinates: torch.Tensor) -> torch.Tensor:
        """Map physical ``(x,z,t)`` coordinates to ``[-1,1]^3``."""

        if coordinates.ndim != 2 or coordinates.shape[1] != 3:
            raise ValueError("PHK coordinates must have physical x, z, and t columns")
        lower = coordinates.new_tensor([self.x_min, self.z_min, self.time_start])
        upper = coordinates.new_tensor([self.x_max, self.z_max, self.time_end])
        return 2.0 * (coordinates - lower) / (upper - lower) - 1.0

    def initial_phase(self, coordinates: torch.Tensor) -> torch.Tensor:
        x = coordinates[:, 0:1]
        z = coordinates[:, 1:2]
        exponent = -0.5 * (
            ((x - self.initial_seed_center_x) / self.initial_seed_sigma_x).square()
            + ((z - self.initial_seed_center_z) / self.initial_seed_sigma_z).square()
        )
        return self.initial_phase_background + self.initial_seed_excess * torch.exp(
            exponent
        )

    def waveform(self, time: torch.Tensor) -> torch.Tensor:
        """Two-cycle C0 trapezoid matching the finite-volume object."""

        local = torch.remainder(time - self.time_start, self.period)
        rising = self.waveform_amplitude * local / self.ramp_up_end
        falling = self.waveform_amplitude * (
            self.ramp_down_end - local
        ) / (self.ramp_down_end - self.hold_end)
        value = torch.where(
            local < self.ramp_up_end,
            rising,
            torch.where(
                local <= self.hold_end,
                torch.full_like(local, self.waveform_amplitude),
                torch.where(local < self.ramp_down_end, falling, torch.zeros_like(local)),
            ),
        )
        in_horizon = (time >= self.time_start) & (time < self.time_end)
        return torch.where(in_horizon, value, torch.zeros_like(value))

    def conductivity(
        self, temperature: torch.Tensor, phase: torch.Tensor
    ) -> torch.Tensor:
        smooth_phase = phase.square() * (3.0 - 2.0 * phase)
        return torch.exp(
            math.log(self.conductivity_phase_ratio) * smooth_phase
            + self.conductivity_temperature_gain * temperature
        )

    def mobility(self, temperature: torch.Tensor) -> torch.Tensor:
        return self.mobility_cold + (
            self.mobility_hot - self.mobility_cold
        ) * torch.sigmoid(
            (temperature - self.theta_transition) / self.mobility_width
        )

    def potential_derivative(
        self, temperature: torch.Tensor, phase: torch.Tensor
    ) -> torch.Tensor:
        return (
            2.0
            * self.barrier_scale
            * phase
            * (1.0 - phase)
            * (1.0 - 2.0 * phase)
            + 6.0
            * self.thermal_drive
            * (self.theta_transition - temperature)
            * phase
            * (1.0 - phase)
        )


class FixedAxisFourier(nn.Module):
    """Non-trainable Fourier features without cross-axis frequency products."""

    def __init__(self, *, x: Sequence[float], z: Sequence[float], t: Sequence[float]):
        super().__init__()
        self.register_buffer("frequency_x", torch.as_tensor(tuple(x), dtype=torch.float64))
        self.register_buffer("frequency_z", torch.as_tensor(tuple(z), dtype=torch.float64))
        self.register_buffer("frequency_t", torch.as_tensor(tuple(t), dtype=torch.float64))
        self.output_dim = 3 + 2 * (
            len(self.frequency_x) + len(self.frequency_z) + len(self.frequency_t)
        )

    def forward(self, normalized: torch.Tensor) -> torch.Tensor:
        pieces = [normalized]
        for index, frequency in enumerate(
            (self.frequency_x, self.frequency_z, self.frequency_t)
        ):
            angles = 2.0 * math.pi * normalized[:, index : index + 1] * frequency
            pieces.extend((torch.sin(angles), torch.cos(angles)))
        return torch.cat(pieces, dim=1)


class ModifiedMLP(nn.Module):
    """Compact gated MLP used identically by every primary arm."""

    def __init__(
        self,
        input_dim: int,
        output_dim: int = 1,
        *,
        hidden_width: int = 64,
        hidden_layers: int = 4,
    ) -> None:
        super().__init__()
        if min(input_dim, output_dim, hidden_width, hidden_layers) <= 0:
            raise ValueError("modified MLP dimensions must be positive")
        self.u = nn.Linear(input_dim, hidden_width)
        self.v = nn.Linear(input_dim, hidden_width)
        self.input = nn.Linear(input_dim, hidden_width)
        self.hidden = nn.ModuleList(
            nn.Linear(hidden_width, hidden_width) for _ in range(hidden_layers - 1)
        )
        self.output = nn.Linear(hidden_width, output_dim)
        self.reset_parameters()

    def reset_parameters(self) -> None:
        for module in (self.u, self.v, self.input, *self.hidden):
            nn.init.xavier_normal_(module.weight)
            nn.init.zeros_(module.bias)
        nn.init.normal_(self.output.weight, mean=0.0, std=1.0e-3)
        nn.init.zeros_(self.output.bias)

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        u = torch.tanh(self.u(features))
        v = torch.tanh(self.v(features))
        hidden = torch.tanh(self.input(features))
        for layer in self.hidden:
            gate = torch.sigmoid(layer(hidden))
            hidden = (1.0 - gate) * u + gate * v
        return self.output(hidden)


@dataclass(frozen=True)
class PhkModelOutput:
    fields: torch.Tensor
    gate: torch.Tensor | None
    pilot_phase: torch.Tensor | None
    heater_pulse_proxy: torch.Tensor | None


@dataclass(frozen=True)
class PhkReadOnlyOutputDiagnostics:
    """Read-only transform observables; no parameter or sampler state is changed."""

    output: PhkModelOutput
    latents: Mapping[str, torch.Tensor]
    raw_latent_sigmoid_derivatives: Mapping[str, torch.Tensor]
    analytic_output_jacobians: Mapping[str, torch.Tensor]


class PhkV22RModel(nn.Module):
    """Field-selective raw/MF model with an optional strict routed probe."""

    def __init__(
        self,
        *,
        physics: PhkV22RPhysics,
        arm: PhkV22RArm | str,
        hidden_width: int = 64,
        hidden_layers: int = 4,
        frequency_band: FrequencyBand | None = None,
        temperature_scale: float = 2.5,
        phase_latent_scale: float = 8.0,
        gate_floor: float = 0.05,
        startup_time: float = 0.35,
        potential_output_transform: str = POTENTIAL_TRANSFORM_LEGACY,
        phase_output_transform: str = PHASE_TRANSFORM_LEGACY,
        phase_jacobian_beta_cap: float = 32.0,
    ) -> None:
        super().__init__()
        self.physics = physics
        self.arm = PhkV22RArm(arm)
        self.frequency_band = frequency_band or FrequencyBand.band_a()
        self.temperature_scale = float(temperature_scale)
        self.phase_latent_scale = float(phase_latent_scale)
        self.gate_floor = float(gate_floor)
        self.startup_time = float(startup_time)
        self.potential_output_transform = str(potential_output_transform)
        self.phase_output_transform = str(phase_output_transform)
        self.phase_jacobian_beta_cap = float(phase_jacobian_beta_cap)
        if not 0.0 < self.gate_floor < 1.0:
            raise ValueError("strict PHA gate floor must lie in (0, 1)")
        if self.startup_time <= 0.0:
            raise ValueError("hard-IC startup time must be positive")
        if self.potential_output_transform not in {
            POTENTIAL_TRANSFORM_LEGACY,
            POTENTIAL_TRANSFORM_TOP_DIRICHLET_HARD_LIFT,
        }:
            raise ValueError("unknown potential output transform")
        if self.phase_output_transform not in {
            PHASE_TRANSFORM_LEGACY,
            PHASE_TRANSFORM_JACOBIAN_NORMALIZED,
        }:
            raise ValueError("unknown phase output transform")
        if self.phase_jacobian_beta_cap != 32.0:
            raise ValueError("phase Jacobian beta cap is frozen to 32")

        raw_encoder = FixedAxisFourier(x=(), z=(), t=())
        if self.arm.uses_multifrequency:
            v_band = FrequencyBand(
                band_id=f"{self.frequency_band.band_id}_V",
                x=self.frequency_band.x[:4],
                z=self.frequency_band.z[:4],
                t=self.frequency_band.t[:2],
            )
            theta_band = FrequencyBand(
                band_id=f"{self.frequency_band.band_id}_THETA",
                x=self.frequency_band.x[:5],
                z=self.frequency_band.z[:5],
                t=self.frequency_band.t[:3],
            )
            self.encoders = nn.ModuleDict(
                {
                    "potential": FixedAxisFourier(
                        x=v_band.x, z=v_band.z, t=v_band.t
                    ),
                    "temperature": FixedAxisFourier(
                        x=theta_band.x, z=theta_band.z, t=theta_band.t
                    ),
                    "phase": FixedAxisFourier(
                        x=self.frequency_band.x,
                        z=self.frequency_band.z,
                        t=self.frequency_band.t,
                    ),
                }
            )
        else:
            self.encoders = nn.ModuleDict(
                {name: FixedAxisFourier(x=(), z=(), t=()) for name in FIELD_NAMES}
            )
        del raw_encoder

        self.heads = nn.ModuleDict(
            {
                name: ModifiedMLP(
                    self.encoders[name].output_dim,
                    hidden_width=hidden_width,
                    hidden_layers=hidden_layers,
                )
                for name in FIELD_NAMES
            }
        )
        if self.arm is PhkV22RArm.STRICT_PHA_PROBE:
            high_x = self.frequency_band.x[-2:]
            high_z = self.frequency_band.z[-2:]
            high_t = self.frequency_band.t[-2:]
            self.high_encoder: FixedAxisFourier | None = FixedAxisFourier(
                x=high_x, z=high_z, t=high_t
            )
            self.high_temperature: ModifiedMLP | None = ModifiedMLP(
                self.high_encoder.output_dim,
                hidden_width=max(16, hidden_width // 2),
                hidden_layers=max(2, hidden_layers - 1),
            )
            self.high_phase: ModifiedMLP | None = ModifiedMLP(
                self.high_encoder.output_dim,
                hidden_width=max(16, hidden_width // 2),
                hidden_layers=max(2, hidden_layers - 1),
            )
        else:
            self.high_encoder = None
            self.high_temperature = None
            self.high_phase = None

    def architecture_manifest(self) -> dict[str, object]:
        return {
            "arm": self.arm.value,
            "frequency_band": (
                self.frequency_band.band_id if self.arm.uses_multifrequency else None
            ),
            "parameter_count": sum(p.numel() for p in self.parameters()),
            "trainable_parameter_count": sum(
                p.numel() for p in self.parameters() if p.requires_grad
            ),
            "field_selective": self.arm.uses_multifrequency,
            "physics_sampler": self.arm.uses_physics_sampler,
            "strict_routing": self.arm is PhkV22RArm.STRICT_PHA_PROBE,
            "gate_stop_gradient": False,
            "potential_output_transform": self.potential_output_transform,
            "phase_output_transform": self.phase_output_transform,
            "phase_jacobian_beta_cap": self.phase_jacobian_beta_cap,
        }

    def _latent_fields(
        self, normalized: torch.Tensor
    ) -> tuple[dict[str, torch.Tensor], torch.Tensor | None, torch.Tensor | None, torch.Tensor | None]:
        latent = {
            name: self.heads[name](self.encoders[name](normalized))
            for name in FIELD_NAMES
        }
        if self.arm is not PhkV22RArm.STRICT_PHA_PROBE:
            return latent, None, None, None
        assert self.high_encoder is not None
        assert self.high_temperature is not None
        assert self.high_phase is not None
        physical = self._physical_coordinates(normalized)
        startup = 1.0 - torch.exp(
            -(physical[:, 2:3] - self.physics.time_start) / self.startup_time
        )
        initial = self.physics.initial_phase(physical).clamp(1.0e-8, 1.0 - 1.0e-8)
        initial_logit = torch.logit(initial)
        pilot_phase = torch.sigmoid(
            initial_logit
            + self.phase_latent_scale * startup * latent["phase"]
        )
        phase_indicator = 4.0 * pilot_phase * (1.0 - pilot_phase)
        softened_distance = torch.sqrt(physical[:, 0:1].square() + 1.0e-6)
        heater_proxy = torch.exp(
            -(
                softened_distance
                / max(self.physics.heater_half_width, 1.0e-8)
            ).square()
        )
        pulse = self.physics.waveform(physical[:, 2:3]) / max(
            self.physics.waveform_amplitude, 1.0e-8
        )
        heater_pulse_proxy = heater_proxy * pulse
        gate = self.gate_floor + (1.0 - self.gate_floor) * torch.sigmoid(
            6.0 * (phase_indicator + heater_pulse_proxy - 0.65)
        )
        high_features = self.high_encoder(normalized)
        latent["temperature"] = latent["temperature"] + gate * self.high_temperature(
            high_features
        )
        latent["phase"] = latent["phase"] + gate * self.high_phase(high_features)
        return latent, gate, pilot_phase, heater_pulse_proxy

    def _physical_coordinates(self, normalized: torch.Tensor) -> torch.Tensor:
        lower = normalized.new_tensor(
            [self.physics.x_min, self.physics.z_min, self.physics.time_start]
        )
        upper = normalized.new_tensor(
            [self.physics.x_max, self.physics.z_max, self.physics.time_end]
        )
        return lower + 0.5 * (normalized + 1.0) * (upper - lower)

    def read_only_output_diagnostics(
        self, coordinates: torch.Tensor
    ) -> PhkReadOnlyOutputDiagnostics:
        """Expose latent fields and analytic transform Jacobians for diagnostics."""

        normalized = self.physics.normalize(coordinates)
        latent, gate, pilot_phase, heater_proxy = self._latent_fields(normalized)
        time = coordinates[:, 2:3]
        z_fraction = (coordinates[:, 1:2] - self.physics.z_min) / (
            self.physics.z_max - self.physics.z_min
        )
        startup = 1.0 - torch.exp(
            -(time - self.physics.time_start) / self.startup_time
        )
        sigmoid_latent = {name: torch.sigmoid(value) for name, value in latent.items()}
        sigmoid_derivative = {
            name: value * (1.0 - value) for name, value in sigmoid_latent.items()
        }
        waveform = self.physics.waveform(time)
        if self.potential_output_transform == POTENTIAL_TRANSFORM_LEGACY:
            potential = waveform * sigmoid_latent["potential"]
            potential_jacobian = waveform * sigmoid_derivative["potential"]
        else:
            potential = waveform * (
                z_fraction + (1.0 - z_fraction) * sigmoid_latent["potential"]
            )
            potential_jacobian = (
                waveform * (1.0 - z_fraction) * sigmoid_derivative["potential"]
            )
        temperature = (
            self.temperature_scale
            * startup
            * (1.0 - z_fraction)
            * sigmoid_latent["temperature"]
        )
        initial = self.physics.initial_phase(coordinates).clamp(1.0e-8, 1.0 - 1.0e-8)
        if self.phase_output_transform == PHASE_TRANSFORM_LEGACY:
            phase = torch.sigmoid(
                torch.logit(initial)
                + self.phase_latent_scale * startup * latent["phase"]
            )
            phase_jacobian = (
                self.phase_latent_scale * startup * phase * (1.0 - phase)
            )
        else:
            phase_scale = torch.minimum(
                initial.new_full(initial.shape, self.phase_jacobian_beta_cap),
                1.0 / (initial * (1.0 - initial) + 1.0e-8),
            )
            phase = torch.sigmoid(
                torch.logit(initial) + startup * phase_scale * latent["phase"]
            )
            phase_jacobian = phase_scale * startup * phase * (1.0 - phase)
        output = PhkModelOutput(
            fields=torch.cat((potential, temperature, phase), dim=1),
            gate=gate,
            pilot_phase=pilot_phase,
            heater_pulse_proxy=heater_proxy,
        )
        return PhkReadOnlyOutputDiagnostics(
            output=output,
            latents=latent,
            raw_latent_sigmoid_derivatives=sigmoid_derivative,
            analytic_output_jacobians={
                "potential": potential_jacobian,
                "temperature": (
                    self.temperature_scale
                    * startup
                    * (1.0 - z_fraction)
                    * sigmoid_derivative["temperature"]
                ),
                "phase": phase_jacobian,
            },
        )

    def diagnostics(self, coordinates: torch.Tensor) -> PhkModelOutput:
        return self.read_only_output_diagnostics(coordinates).output

    def forward(self, coordinates: torch.Tensor) -> torch.Tensor:
        return self.diagnostics(coordinates).fields


@dataclass(frozen=True)
class PhkFieldBundle:
    coordinates: torch.Tensor
    values: Mapping[str, torch.Tensor]
    gradients: Mapping[str, torch.Tensor]
    diagonal_second: Mapping[str, Mapping[str, torch.Tensor]]


def _gradient(value: torch.Tensor, coordinates: torch.Tensor) -> torch.Tensor:
    gradient = torch.autograd.grad(
        value,
        coordinates,
        grad_outputs=torch.ones_like(value),
        create_graph=True,
        retain_graph=True,
        allow_unused=False,
    )[0]
    return gradient


def _axis_second(
    first_gradient: torch.Tensor, coordinates: torch.Tensor, axis: int
) -> torch.Tensor:
    return _gradient(first_gradient[:, axis : axis + 1], coordinates)[:, axis : axis + 1]


def evaluate_fields(
    model: PhkV22RModel, coordinates: torch.Tensor
) -> PhkFieldBundle:
    q = coordinates
    if not q.requires_grad:
        q = coordinates.detach().clone().requires_grad_(True)
    fields = model(q)
    values: dict[str, torch.Tensor] = {}
    gradients: dict[str, torch.Tensor] = {}
    diagonal: dict[str, Mapping[str, torch.Tensor]] = {}
    for index, name in enumerate(FIELD_NAMES):
        value = fields[:, index : index + 1]
        gradient = _gradient(value, q)
        values[name] = value
        gradients[name] = gradient
        diagonal[name] = {
            "xx": _axis_second(gradient, q, 0),
            "zz": _axis_second(gradient, q, 1),
        }
    return PhkFieldBundle(
        coordinates=q,
        values=values,
        gradients=gradients,
        diagonal_second=diagonal,
    )


def phase_kinetic_rhs_from_laplacian(
    physics: PhkV22RPhysics,
    *,
    temperature: torch.Tensor,
    phase: torch.Tensor,
    phase_laplacian: torch.Tensor,
) -> torch.Tensor:
    """Evaluate the canonical phase kinetic right-hand side for any field."""

    return physics.mobility(temperature) * (
        physics.interface_width**2 * phase_laplacian
        - physics.potential_derivative(temperature, phase)
    )


def _validate_coupling_alpha(coupling_alpha: float) -> float:
    alpha = float(coupling_alpha)
    if not math.isfinite(alpha) or not 0.0 <= alpha <= 1.0:
        raise ValueError("coupling alpha must be finite and lie in [0, 1]")
    return alpha


def interior_diagnostic_terms(
    model: PhkV22RModel,
    coordinates: torch.Tensor,
    *,
    coupling_alpha: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Decompose the exact strong-form residuals without changing model state."""

    bundle = evaluate_fields(model, coordinates)
    values = bundle.values
    gradients = bundle.gradients
    second = bundle.diagonal_second
    physics = model.physics
    alpha = _validate_coupling_alpha(coupling_alpha)
    if alpha == 1.0:
        coupling_phase = values["phase"]
        coupling_phase_time = gradients["phase"][:, 2:3]
    elif alpha == 0.0:
        coupling_phase = physics.initial_phase(bundle.coordinates)
        coupling_phase_time = torch.zeros_like(gradients["phase"][:, 2:3])
    else:
        initial_phase = physics.initial_phase(bundle.coordinates)
        coupling_phase = (1.0 - alpha) * initial_phase + alpha * values["phase"]
        coupling_phase_time = alpha * gradients["phase"][:, 2:3]

    conductivity = physics.conductivity(values["temperature"], coupling_phase)
    conductivity_gradient = _gradient(conductivity, bundle.coordinates)
    lap_potential = second["potential"]["xx"] + second["potential"]["zz"]
    lap_temperature = second["temperature"]["xx"] + second["temperature"]["zz"]
    lap_phase = second["phase"]["xx"] + second["phase"]["zz"]
    joule = conductivity * (
        gradients["potential"][:, 0:1].square()
        + gradients["potential"][:, 1:2].square()
    )
    electric_conductivity_laplacian = conductivity * lap_potential
    electric_gradient_x = (
        conductivity_gradient[:, 0:1] * gradients["potential"][:, 0:1]
    )
    electric_gradient_z = (
        conductivity_gradient[:, 1:2] * gradients["potential"][:, 1:2]
    )
    electric = (
        electric_conductivity_laplacian + electric_gradient_x + electric_gradient_z
    )
    thermal_time = gradients["temperature"][:, 2:3]
    thermal_latent = physics.latent_ratio * coupling_phase_time
    thermal_diffusion = -physics.thermal_diffusivity * lap_temperature
    thermal_cooling = physics.volumetric_cooling * values["temperature"]
    thermal_joule = -physics.joule_gain * joule
    thermal = (
        thermal_time
        + thermal_latent
        + thermal_diffusion
        + thermal_cooling
        + thermal_joule
    )
    phase_time = gradients["phase"][:, 2:3]
    phase_diffusion = physics.interface_width**2 * lap_phase
    potential_derivative = physics.potential_derivative(
        values["temperature"], values["phase"]
    )
    phase_reaction = -potential_derivative
    mobility = physics.mobility(values["temperature"])
    phase_kinetic_rhs = phase_kinetic_rhs_from_laplacian(
        physics,
        temperature=values["temperature"],
        phase=values["phase"],
        phase_laplacian=lap_phase,
    )
    phase = phase_time - phase_kinetic_rhs
    return {
        "electric_conductivity_laplacian": electric_conductivity_laplacian,
        "electric_conductivity_gradient_x": electric_gradient_x,
        "electric_conductivity_gradient_z": electric_gradient_z,
        "electric_residual": electric,
        "thermal_time": thermal_time,
        "thermal_latent": thermal_latent,
        "thermal_diffusion": thermal_diffusion,
        "thermal_cooling": thermal_cooling,
        "thermal_joule": thermal_joule,
        "thermal_residual": thermal,
        "phase_time": phase_time,
        "phase_diffusion": phase_diffusion,
        "phase_reaction": phase_reaction,
        "phase_kinetic_rhs": phase_kinetic_rhs,
        "phase_residual": phase,
        "joule_density": joule,
        "conductivity": conductivity,
        "mobility": mobility,
        "phase_indicator": 4.0 * values["phase"] * (1.0 - values["phase"]),
        "coupling_phase": coupling_phase,
        "coupling_phase_time": coupling_phase_time,
    }


def interior_residuals(
    model: PhkV22RModel,
    coordinates: torch.Tensor,
    *,
    coupling_alpha: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Evaluate the exact three strong-form residuals and sampler diagnostics."""

    terms = interior_diagnostic_terms(
        model, coordinates, coupling_alpha=coupling_alpha
    )
    return {
        "electric": terms["electric_residual"],
        "thermal": terms["thermal_residual"],
        "phase": terms["phase_residual"],
        "joule_density": terms["joule_density"],
        "phase_indicator": terms["phase_indicator"],
    }


def initial_residuals(
    model: PhkV22RModel, spatial_coordinates: torch.Tensor
) -> dict[str, torch.Tensor]:
    if spatial_coordinates.ndim != 2 or spatial_coordinates.shape[1] != 2:
        raise ValueError("initial coordinates must contain physical x and z")
    time = spatial_coordinates.new_full(
        (spatial_coordinates.shape[0], 1), model.physics.time_start
    )
    coordinates = torch.cat((spatial_coordinates, time), dim=1)
    fields = model(coordinates)
    return {
        "ic_potential": fields[:, 0:1],
        "ic_temperature": fields[:, 1:2],
        "ic_phase": fields[:, 2:3]
        - model.physics.initial_phase(coordinates),
    }


def boundary_residuals(
    model: PhkV22RModel,
    coordinates: torch.Tensor,
    *,
    side: str,
    coupling_alpha: float = 1.0,
) -> dict[str, torch.Tensor]:
    """Return mixed electrical, thermal, and phase boundary residuals."""

    if side not in {"left", "right", "bottom", "top"}:
        raise ValueError("boundary side must be left, right, bottom, or top")
    q = coordinates
    if not q.requires_grad:
        q = coordinates.detach().clone().requires_grad_(True)
    fields = model(q)
    values = {
        name: fields[:, index : index + 1]
        for index, name in enumerate(FIELD_NAMES)
    }
    gradients = {name: _gradient(value, q) for name, value in values.items()}
    physics = model.physics
    alpha = _validate_coupling_alpha(coupling_alpha)
    if alpha == 1.0:
        coupling_phase = values["phase"]
    elif alpha == 0.0:
        coupling_phase = physics.initial_phase(q)
    else:
        coupling_phase = (
            (1.0 - alpha) * physics.initial_phase(q) + alpha * values["phase"]
        )
    normal = {
        "left": (-1.0, 0.0),
        "right": (1.0, 0.0),
        "bottom": (0.0, -1.0),
        "top": (0.0, 1.0),
    }[side]
    normal_potential = (
        normal[0] * gradients["potential"][:, 0:1]
        + normal[1] * gradients["potential"][:, 1:2]
    )
    normal_temperature = (
        normal[0] * gradients["temperature"][:, 0:1]
        + normal[1] * gradients["temperature"][:, 1:2]
    )
    normal_phase = (
        normal[0] * gradients["phase"][:, 0:1]
        + normal[1] * gradients["phase"][:, 1:2]
    )
    conductivity = physics.conductivity(values["temperature"], coupling_phase)
    result: dict[str, torch.Tensor] = {"bc_phase_no_flux": normal_phase}
    if side == "top":
        result["bc_potential_top"] = values["potential"] - physics.waveform(
            q[:, 2:3]
        )
        result["bc_temperature_top"] = values["temperature"]
    else:
        result["bc_temperature_robin"] = (
            normal_temperature + physics.thermal_robin_biot * values["temperature"]
        )
        if side == "bottom":
            heater = q[:, 0].abs() <= physics.heater_half_width
            if bool(torch.any(heater)):
                result["bc_potential_heater"] = values["potential"][heater]
            outside = ~heater
            if bool(torch.any(outside)):
                result["bc_electric_insulating_bottom"] = (
                    conductivity * normal_potential
                )[outside]
        else:
            result["bc_electric_insulating_side"] = conductivity * normal_potential
    return result


def normalized_residual_loss(
    residuals: Mapping[str, torch.Tensor],
    *,
    scales: Mapping[str, float] | None = None,
) -> torch.Tensor:
    """Mean normalized squared residual; diagnostic fields are excluded."""

    physical = {
        name: value
        for name, value in residuals.items()
        if name not in {"joule_density", "phase_indicator"}
    }
    if not physical:
        raise ValueError("at least one physical residual is required")
    losses = []
    for name, value in physical.items():
        scale = 1.0 if scales is None else float(scales.get(name, 1.0))
        if not math.isfinite(scale) or scale <= 0.0:
            raise ValueError(f"residual scale must be positive for {name}")
        losses.append(torch.mean((value / scale).square()))
    return torch.stack(losses).mean()


@dataclass(frozen=True)
class CollocationMixture:
    uniform_sobol: float = 0.35
    residual: float = 0.25
    phase: float = 0.25
    joule: float = 0.15
    candidate_pool_multiplier: int = 4

    def validate(self) -> None:
        weights = (self.uniform_sobol, self.residual, self.phase, self.joule)
        if any(weight < 0.0 for weight in weights):
            raise ValueError("collocation mixture weights must be nonnegative")
        if not math.isclose(sum(weights), 1.0, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("collocation mixture weights must sum to one")
        if self.uniform_sobol <= 0.0:
            raise ValueError("collocation mixture must retain a positive uniform floor")
        if self.candidate_pool_multiplier < 1:
            raise ValueError("candidate pool multiplier must be positive")


def _integer_mixture_counts(total: int, mixture: CollocationMixture) -> dict[str, int]:
    if total < 4:
        raise ValueError("physics-aware batches require at least four points")
    raw = {
        "uniform": mixture.uniform_sobol * total,
        "residual": mixture.residual * total,
        "phase": mixture.phase * total,
        "joule": mixture.joule * total,
    }
    counts = {name: int(math.floor(value)) for name, value in raw.items()}
    for name, _ in sorted(
        raw.items(), key=lambda item: item[1] - math.floor(item[1]), reverse=True
    )[: total - sum(counts.values())]:
        counts[name] += 1
    if counts["uniform"] <= 0:
        raise ValueError("rounded mixture removed the uniform floor")
    return counts


class PhkCollocationSampler:
    """Deterministic Sobol sampler with equal causal replay and physics ranking."""

    def __init__(
        self,
        *,
        physics: PhkV22RPhysics,
        windows: Sequence[tuple[float, float]] = (
            (0.0, 0.35),
            (0.35, 1.25),
            (1.25, 1.60),
            (1.60, 2.50),
        ),
        mixture: CollocationMixture = CollocationMixture(),
        seed: int = 17,
    ) -> None:
        mixture.validate()
        if not windows:
            raise ValueError("at least one causal window is required")
        previous = physics.time_start
        for start, end in windows:
            if not math.isclose(start, previous, rel_tol=0.0, abs_tol=1.0e-12):
                raise ValueError("causal windows must be contiguous and ordered")
            if end <= start:
                raise ValueError("causal window end must exceed its start")
            previous = end
        if not math.isclose(previous, physics.time_end, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("causal windows must cover the full physical horizon")
        self.physics = physics
        self.windows = tuple((float(a), float(b)) for a, b in windows)
        self.mixture = mixture
        self.engine = torch.quasirandom.SobolEngine(3, scramble=True, seed=int(seed))

    def _unit(self, count: int, *, dtype: torch.dtype, device: torch.device) -> torch.Tensor:
        if count <= 0:
            return torch.empty((0, 3), dtype=dtype, device=device)
        return self.engine.draw(count, dtype=dtype).to(device=device)

    def interior_uniform(
        self,
        count: int,
        *,
        active_windows: int,
        dtype: torch.dtype,
        device: torch.device,
    ) -> torch.Tensor:
        if not 1 <= active_windows <= len(self.windows):
            raise ValueError("active window count is outside the causal schedule")
        base = count // active_windows
        remainder = count % active_windows
        pieces = []
        for index, (start, end) in enumerate(self.windows[:active_windows]):
            local_count = base + (1 if index < remainder else 0)
            unit = self._unit(local_count, dtype=dtype, device=device)
            x = self.physics.x_min + unit[:, 0:1] * (
                self.physics.x_max - self.physics.x_min
            )
            z = self.physics.z_min + unit[:, 1:2] * (
                self.physics.z_max - self.physics.z_min
            )
            t = start + unit[:, 2:3] * (end - start)
            pieces.append(torch.cat((x, z, t), dim=1))
        return torch.cat(pieces, dim=0)

    def select_interior(
        self,
        model: PhkV22RModel,
        *,
        count: int,
        active_windows: int,
        physics_aware: bool,
        dtype: torch.dtype,
        device: torch.device,
    ) -> torch.Tensor:
        if not physics_aware:
            return self.interior_uniform(
                count,
                active_windows=active_windows,
                dtype=dtype,
                device=device,
            )
        counts = _integer_mixture_counts(count, self.mixture)
        pool_count = max(
            count,
            count * self.mixture.candidate_pool_multiplier,
        )
        candidates = self.interior_uniform(
            pool_count,
            active_windows=active_windows,
            dtype=dtype,
            device=device,
        ).requires_grad_(True)
        with torch.enable_grad():
            diagnostics = interior_residuals(model, candidates)
            residual_score = torch.sqrt(
                diagnostics["electric"].square()
                + diagnostics["thermal"].square()
                + diagnostics["phase"].square()
                + 1.0e-30
            )[:, 0]
            phase_score = diagnostics["phase_indicator"][:, 0]
            joule_score = diagnostics["joule_density"][:, 0]
        selected = [
            self.interior_uniform(
                counts["uniform"],
                active_windows=active_windows,
                dtype=dtype,
                device=device,
            )
        ]
        used = torch.zeros(pool_count, dtype=torch.bool, device=device)
        for name, score in (
            ("residual", residual_score),
            ("phase", phase_score),
            ("joule", joule_score),
        ):
            masked_score = score.detach().clone()
            masked_score[used] = -torch.inf
            indices = torch.topk(
                masked_score,
                k=counts[name],
                largest=True,
                sorted=False,
            ).indices
            used[indices] = True
            selected.append(candidates.detach()[indices])
        return torch.cat(selected, dim=0)

    def boundary(
        self,
        count_per_side: int,
        *,
        active_windows: int,
        dtype: torch.dtype,
        device: torch.device,
    ) -> dict[str, torch.Tensor]:
        result = {}
        for side in ("left", "right", "bottom", "top"):
            unit = self._unit(count_per_side, dtype=dtype, device=device)
            x = self.physics.x_min + unit[:, 0:1] * (
                self.physics.x_max - self.physics.x_min
            )
            z = self.physics.z_min + unit[:, 1:2] * (
                self.physics.z_max - self.physics.z_min
            )
            window_index = torch.arange(count_per_side, device=device) % active_windows
            starts = unit.new_tensor([self.windows[i][0] for i in range(active_windows)])
            ends = unit.new_tensor([self.windows[i][1] for i in range(active_windows)])
            t = starts[window_index, None] + unit[:, 2:3] * (
                ends[window_index, None] - starts[window_index, None]
            )
            if side == "left":
                x.fill_(self.physics.x_min)
            elif side == "right":
                x.fill_(self.physics.x_max)
            elif side == "bottom":
                z.fill_(self.physics.z_min)
            else:
                z.fill_(self.physics.z_max)
            result[side] = torch.cat((x, z, t), dim=1)
        return result

    def initial(
        self,
        count: int,
        *,
        dtype: torch.dtype,
        device: torch.device,
    ) -> torch.Tensor:
        unit = self._unit(count, dtype=dtype, device=device)
        x = self.physics.x_min + unit[:, 0:1] * (
            self.physics.x_max - self.physics.x_min
        )
        z = self.physics.z_min + unit[:, 1:2] * (
            self.physics.z_max - self.physics.z_min
        )
        return torch.cat((x, z), dim=1)


__all__ = [
    "CollocationMixture",
    "FIELD_NAMES",
    "FrequencyBand",
    "PhkCollocationSampler",
    "PhkFieldBundle",
    "PhkModelOutput",
    "PhkReadOnlyOutputDiagnostics",
    "PhkV22RArm",
    "PhkV22RModel",
    "PhkV22RPhysics",
    "PHASE_TRANSFORM_JACOBIAN_NORMALIZED",
    "PHASE_TRANSFORM_LEGACY",
    "POTENTIAL_TRANSFORM_LEGACY",
    "POTENTIAL_TRANSFORM_TOP_DIRICHLET_HARD_LIFT",
    "boundary_residuals",
    "evaluate_fields",
    "initial_residuals",
    "interior_diagnostic_terms",
    "interior_residuals",
    "normalized_residual_loss",
    "phase_kinetic_rhs_from_laplacian",
]
