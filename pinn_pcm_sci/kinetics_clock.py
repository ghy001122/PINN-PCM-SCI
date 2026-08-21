"""Field-selective Structural Kinetics-Clock building blocks.

The module keeps the clock, structural field, and remaining physical fields as
separate trainable blocks.  It also exposes the complete first/second-order
coordinate pullback used by strong-form residuals on smooth protocol segments.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable, Sequence

import torch
from torch import nn
from torch.nn import functional as F


def make_mlp(
    input_dim: int,
    output_dim: int,
    *,
    hidden_width: int,
    hidden_layers: int,
) -> nn.Sequential:
    if min(input_dim, output_dim, hidden_width, hidden_layers) <= 0:
        raise ValueError("MLP dimensions and hidden layer count must be positive")
    layers: list[nn.Module] = []
    width = input_dim
    for _ in range(hidden_layers):
        layers.extend((nn.Linear(width, hidden_width), nn.Tanh()))
        width = hidden_width
    layers.append(nn.Linear(width, output_dim))
    return nn.Sequential(*layers)


class IdentityClock(nn.Module):
    """Engineering control: the structural coordinate is the raw time."""

    def forward(self, xyt: torch.Tensor) -> torch.Tensor:
        _validate_coordinates(xyt)
        return xyt[:, -1:]

    def rate(self, xyt: torch.Tensor) -> torch.Tensor:
        _validate_coordinates(xyt)
        return torch.ones_like(xyt[:, -1:])


class PositiveGaussianClock(nn.Module):
    """Constructively monotone local clock with an analytic erf cumulative.

    Amplitudes depend only on space.  Time enters only through fixed Gaussian
    rate bases, so the derivative with respect to physical time has the strict
    lower bound ``kappa_floor`` by construction.
    """

    def __init__(
        self,
        *,
        spatial_dim: int,
        centers: Sequence[float],
        widths: Sequence[float],
        kappa_floor: float,
        hidden_width: int,
        segment_start: float = 0.0,
        segment_offset: float = 0.0,
    ) -> None:
        super().__init__()
        if spatial_dim <= 0:
            raise ValueError("spatial_dim must be positive")
        if not centers or len(centers) != len(widths):
            raise ValueError("centers and widths must be non-empty and aligned")
        if any(width <= 0.0 for width in widths):
            raise ValueError("Gaussian widths must be positive")
        if kappa_floor <= 0.0:
            raise ValueError("kappa_floor must be strictly positive")
        self.spatial_dim = spatial_dim
        self.amplitude_model = make_mlp(
            spatial_dim,
            len(centers),
            hidden_width=hidden_width,
            hidden_layers=1,
        )
        self.register_buffer("centers", torch.tensor(centers).reshape(1, -1))
        self.register_buffer("widths", torch.tensor(widths).reshape(1, -1))
        self.register_buffer("kappa_floor", torch.tensor(float(kappa_floor)))
        self.register_buffer("segment_start", torch.tensor(float(segment_start)))
        self.register_buffer("segment_offset", torch.tensor(float(segment_offset)))

    def _validate(self, xyt: torch.Tensor) -> None:
        _validate_coordinates(xyt)
        if xyt.shape[1] != self.spatial_dim + 1:
            raise ValueError(
                f"clock expects {self.spatial_dim + 1} coordinates, got {xyt.shape[1]}"
            )

    def amplitudes(self, spatial_coordinates: torch.Tensor) -> torch.Tensor:
        return F.softplus(self.amplitude_model(spatial_coordinates))

    def rate(self, xyt: torch.Tensor) -> torch.Tensor:
        self._validate(xyt)
        time = xyt[:, -1:]
        scaled = (time - self.centers) / self.widths
        gaussian = torch.exp(-0.5 * scaled.square())
        return self.kappa_floor + (
            self.amplitudes(xyt[:, : self.spatial_dim]) * gaussian
        ).sum(dim=1, keepdim=True)

    def forward(self, xyt: torch.Tensor) -> torch.Tensor:
        self._validate(xyt)
        time = xyt[:, -1:]
        lower = self.segment_start.to(dtype=xyt.dtype, device=xyt.device)
        sqrt_two = math.sqrt(2.0)
        upper_argument = (time - self.centers) / (sqrt_two * self.widths)
        lower_argument = (lower - self.centers) / (sqrt_two * self.widths)
        gaussian_integral = self.widths * math.sqrt(math.pi / 2.0) * (
            torch.erf(upper_argument) - torch.erf(lower_argument)
        )
        cumulative = (
            self.amplitudes(xyt[:, : self.spatial_dim]) * gaussian_integral
        ).sum(dim=1, keepdim=True)
        return (
            self.segment_offset
            + self.kappa_floor * (time - lower)
            + cumulative
        )


class PiecewisePositiveGaussianClock(nn.Module):
    """Continuously accumulate positive-rate clocks across physical breakpoints."""

    def __init__(
        self,
        *,
        segments: Sequence[PositiveGaussianClock],
        breakpoints: Sequence[float],
    ) -> None:
        super().__init__()
        if len(segments) != len(breakpoints) + 1:
            raise ValueError("piecewise clock requires one more segment than breakpoint")
        if any(right <= left for left, right in zip(breakpoints, breakpoints[1:])):
            raise ValueError("clock breakpoints must be strictly increasing")
        spatial_dim = segments[0].spatial_dim
        for index, segment in enumerate(segments):
            if segment.spatial_dim != spatial_dim:
                raise ValueError("all clock segments must use the same spatial dimension")
            if float(segment.segment_offset) != 0.0:
                raise ValueError("piecewise wrapper owns cumulative offsets")
            if index > 0 and not math.isclose(
                float(segment.segment_start), float(breakpoints[index - 1])
            ):
                raise ValueError("each segment must start at its preceding breakpoint")
        self.spatial_dim = spatial_dim
        self.segments = nn.ModuleList(segments)
        self.register_buffer("breakpoints", torch.tensor(tuple(breakpoints)))

    def _segment_index(self, xyt: torch.Tensor) -> torch.Tensor:
        return torch.bucketize(xyt[:, -1].contiguous(), self.breakpoints, right=True)

    def _cumulative_values(self, xyt: torch.Tensor) -> list[torch.Tensor]:
        prior = torch.zeros_like(xyt[:, -1:])
        values: list[torch.Tensor] = []
        for index, segment in enumerate(self.segments):
            values.append(prior + segment(xyt))
            if index < len(self.breakpoints):
                endpoint = torch.cat(
                    [
                        xyt[:, : self.spatial_dim],
                        torch.full_like(xyt[:, -1:], float(self.breakpoints[index])),
                    ],
                    dim=1,
                )
                prior = prior + segment(endpoint)
        return values

    def forward(self, xyt: torch.Tensor) -> torch.Tensor:
        _validate_coordinates(xyt)
        if xyt.shape[1] != self.spatial_dim + 1:
            raise ValueError("piecewise clock coordinate dimension mismatch")
        index = self._segment_index(xyt)
        values = self._cumulative_values(xyt)
        output = values[0]
        for segment_index, value in enumerate(values[1:], start=1):
            output = torch.where(index[:, None] == segment_index, value, output)
        return output

    def rate(self, xyt: torch.Tensor) -> torch.Tensor:
        _validate_coordinates(xyt)
        index = self._segment_index(xyt)
        rates = [segment.rate(xyt) for segment in self.segments]
        output = rates[0]
        for segment_index, value in enumerate(rates[1:], start=1):
            output = torch.where(index[:, None] == segment_index, value, output)
        return output


@dataclass(frozen=True)
class PullbackResult:
    coordinates: torch.Tensor
    tau: torch.Tensor
    value: torch.Tensor
    latent_gradient: torch.Tensor
    latent_hessian: torch.Tensor
    tau_gradient: torch.Tensor
    tau_hessian: torch.Tensor
    physical_gradient: torch.Tensor
    physical_hessian: torch.Tensor


def _validate_coordinates(coordinates: torch.Tensor) -> None:
    if coordinates.ndim != 2 or coordinates.shape[1] < 2:
        raise ValueError("coordinates must have shape [batch, spatial_dim + time]")
    if not coordinates.is_floating_point():
        raise ValueError("coordinates must use a floating-point dtype")


def _pointwise_gradient(output: torch.Tensor, inputs: torch.Tensor) -> torch.Tensor:
    if not output.requires_grad:
        return torch.zeros_like(inputs)
    gradient = torch.autograd.grad(
        output,
        inputs,
        grad_outputs=torch.ones_like(output),
        create_graph=True,
        retain_graph=True,
        allow_unused=True,
    )[0]
    return torch.zeros_like(inputs) if gradient is None else gradient


def _pointwise_hessian(gradient: torch.Tensor, inputs: torch.Tensor) -> torch.Tensor:
    rows: list[torch.Tensor] = []
    for index in range(gradient.shape[1]):
        component = gradient[:, index : index + 1]
        rows.append(_pointwise_gradient(component, inputs))
    return torch.stack(rows, dim=1)


def full_pullback(
    eta_model: nn.Module,
    clock: nn.Module,
    coordinates: torch.Tensor,
) -> PullbackResult:
    """Return the complete physical first/second derivatives of eta(x, tau(x,t))."""

    _validate_coordinates(coordinates)
    evaluation_coordinates = coordinates
    if not evaluation_coordinates.requires_grad:
        evaluation_coordinates = coordinates.detach().clone().requires_grad_(True)
    tau = clock(evaluation_coordinates)
    if tau.shape != (evaluation_coordinates.shape[0], 1):
        raise ValueError("clock output must have shape [batch, 1]")
    latent_coordinates = torch.cat([evaluation_coordinates[:, :-1], tau], dim=1)
    value = eta_model(latent_coordinates)
    if value.shape != (evaluation_coordinates.shape[0], 1):
        raise ValueError("eta model output must have shape [batch, 1]")

    latent_gradient = _pointwise_gradient(value, latent_coordinates)
    latent_hessian = _pointwise_hessian(latent_gradient, latent_coordinates)
    tau_gradient = _pointwise_gradient(tau, evaluation_coordinates)
    tau_hessian = _pointwise_hessian(tau_gradient, evaluation_coordinates)

    batch = evaluation_coordinates.shape[0]
    physical_dim = evaluation_coordinates.shape[1]
    spatial_dim = physical_dim - 1
    identity = torch.eye(
        spatial_dim,
        dtype=evaluation_coordinates.dtype,
        device=evaluation_coordinates.device,
    ).expand(batch, -1, -1)
    spatial_time_column = torch.zeros(
        (batch, spatial_dim, 1),
        dtype=evaluation_coordinates.dtype,
        device=evaluation_coordinates.device,
    )
    latent_jacobian = torch.cat(
        [
            torch.cat([identity, spatial_time_column], dim=2),
            tau_gradient.unsqueeze(1),
        ],
        dim=1,
    )
    physical_gradient = torch.einsum(
        "bip,bi->bp", latent_jacobian, latent_gradient
    )
    physical_hessian = torch.einsum(
        "bip,bik,bkq->bpq",
        latent_jacobian,
        latent_hessian,
        latent_jacobian,
    )
    physical_hessian = physical_hessian + (
        latent_gradient[:, -1:].unsqueeze(-1) * tau_hessian
    )
    return PullbackResult(
        coordinates=evaluation_coordinates,
        tau=tau,
        value=value,
        latent_gradient=latent_gradient,
        latent_hessian=latent_hessian,
        tau_gradient=tau_gradient,
        tau_hessian=tau_hessian,
        physical_gradient=physical_gradient,
        physical_hessian=physical_hessian,
    )


@dataclass(frozen=True)
class KineticsClockOutput:
    tau: torch.Tensor
    eta: torch.Tensor
    physical_fields: torch.Tensor


@dataclass(frozen=True)
class ClockDiagnostics:
    min_rate: float
    max_spatial_gradient: float
    max_coordinate_condition: float
    max_first_order_amplification: float
    max_second_order_amplification: float


@dataclass(frozen=True)
class ClockAdmissibilitySpec:
    min_rate: float
    max_spatial_gradient: float
    max_coordinate_condition: float
    max_first_order_amplification: float
    max_second_order_amplification: float

    def __post_init__(self) -> None:
        if self.min_rate <= 0.0:
            raise ValueError("admissible minimum rate must be positive")
        if min(
            self.max_spatial_gradient,
            self.max_coordinate_condition,
            self.max_first_order_amplification,
            self.max_second_order_amplification,
        ) <= 0.0:
            raise ValueError("admissibility upper bounds must be positive")


@dataclass(frozen=True)
class ClockAdmissibilityReport:
    passed: bool
    violations: tuple[str, ...]
    diagnostics: ClockDiagnostics


def _clock_coordinate_jacobian(tau_gradient: torch.Tensor) -> torch.Tensor:
    batch, physical_dim = tau_gradient.shape
    spatial_dim = physical_dim - 1
    identity = torch.eye(
        spatial_dim,
        dtype=tau_gradient.dtype,
        device=tau_gradient.device,
    ).expand(batch, -1, -1)
    spatial_time_column = torch.zeros(
        (batch, spatial_dim, 1),
        dtype=tau_gradient.dtype,
        device=tau_gradient.device,
    )
    return torch.cat(
        [
            torch.cat([identity, spatial_time_column], dim=2),
            tau_gradient.unsqueeze(1),
        ],
        dim=1,
    )


def clock_diagnostics(pullback: PullbackResult) -> ClockDiagnostics:
    jacobian = _clock_coordinate_jacobian(pullback.tau_gradient)
    singular_values = torch.linalg.svdvals(jacobian)
    largest = singular_values[:, 0]
    smallest = singular_values[:, -1]
    condition = largest / smallest
    spatial_gradient = torch.linalg.vector_norm(
        pullback.tau_gradient[:, :-1], dim=1
    )
    tau_hessian_norm = torch.linalg.matrix_norm(
        pullback.tau_hessian, ord=2
    )
    second_order = largest.square() + tau_hessian_norm
    return ClockDiagnostics(
        min_rate=float(pullback.tau_gradient[:, -1].min().detach().cpu()),
        max_spatial_gradient=float(spatial_gradient.max().detach().cpu()),
        max_coordinate_condition=float(condition.max().detach().cpu()),
        max_first_order_amplification=float(largest.max().detach().cpu()),
        max_second_order_amplification=float(second_order.max().detach().cpu()),
    )


def evaluate_clock_admissibility(
    pullback: PullbackResult,
    spec: ClockAdmissibilitySpec,
) -> ClockAdmissibilityReport:
    diagnostics = clock_diagnostics(pullback)
    violations: list[str] = []
    if diagnostics.min_rate < spec.min_rate:
        violations.append("MIN_RATE")
    if diagnostics.max_spatial_gradient > spec.max_spatial_gradient:
        violations.append("SPATIAL_GRADIENT")
    if diagnostics.max_coordinate_condition > spec.max_coordinate_condition:
        violations.append("COORDINATE_CONDITION")
    if diagnostics.max_first_order_amplification > spec.max_first_order_amplification:
        violations.append("FIRST_ORDER_AMPLIFICATION")
    if diagnostics.max_second_order_amplification > spec.max_second_order_amplification:
        violations.append("SECOND_ORDER_AMPLIFICATION")
    return ClockAdmissibilityReport(
        passed=not violations,
        violations=tuple(violations),
        diagnostics=diagnostics,
    )


def kinetics_alignment_loss(
    predicted_rate: torch.Tensor,
    target_rate: torch.Tensor,
    *,
    stop_gradient_target: bool,
) -> torch.Tensor:
    if predicted_rate.shape != target_rate.shape:
        raise ValueError("clock rate and kinetics target must have identical shapes")
    target = target_rate.detach() if stop_gradient_target else target_rate
    return torch.mean((predicted_rate - target).square())


class StructuralKineticsClockPINN(nn.Module):
    """Architectural boundary enforcing the field-selective clock graph."""

    def __init__(
        self,
        *,
        clock: nn.Module,
        eta_model: nn.Module,
        physical_field_model: nn.Module,
    ) -> None:
        super().__init__()
        self.clock = clock
        self.eta_model = eta_model
        self.physical_field_model = physical_field_model
        self._assert_parameter_isolation()

    def parameter_id_sets(self) -> dict[str, set[int]]:
        return {
            "clock": {id(parameter) for parameter in self.clock.parameters()},
            "eta": {id(parameter) for parameter in self.eta_model.parameters()},
            "physical_fields": {
                id(parameter) for parameter in self.physical_field_model.parameters()
            },
        }

    def _assert_parameter_isolation(self) -> None:
        groups = self.parameter_id_sets()
        if (
            groups["clock"] & groups["eta"]
            or groups["clock"] & groups["physical_fields"]
            or groups["eta"] & groups["physical_fields"]
        ):
            raise ValueError("clock, eta, and physical fields must not share parameters")

    def forward(self, coordinates: torch.Tensor) -> KineticsClockOutput:
        _validate_coordinates(coordinates)
        tau = self.clock(coordinates)
        eta = self.eta_model(torch.cat([coordinates[:, :-1], tau], dim=1))
        physical_fields = self.physical_field_model(coordinates)
        return KineticsClockOutput(
            tau=tau,
            eta=eta,
            physical_fields=physical_fields,
        )


def piecewise_strong_form_mask(
    time: torch.Tensor,
    *,
    breakpoints: Iterable[float],
    exclusion_radius: float,
) -> torch.Tensor:
    if exclusion_radius < 0.0:
        raise ValueError("exclusion_radius must be non-negative")
    mask = torch.ones_like(time, dtype=torch.bool)
    for breakpoint in breakpoints:
        mask &= torch.abs(time - float(breakpoint)) > exclusion_radius
    return mask
