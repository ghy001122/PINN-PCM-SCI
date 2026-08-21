"""Shared electro-phase gate for multi-frequency Q-POP PINN fields.

The gate is deterministic: it is computed only from current model predictions,
the frozen Q-POP parameters, and the queried coordinates.  The same scalar
field can therefore route the high-frequency correction and collocation
allocation without introducing an oracle-label path.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

import torch
from torch import nn

from .kinetics_clock import make_mlp
from .qpop_physics import QPopParameters


@dataclass(frozen=True)
class PhaseHotspotOutput:
    fields: torch.Tensor
    physical_gate: torch.Tensor
    capacity_gate: torch.Tensor
    phase_indicator: torch.Tensor
    joule_indicator: torch.Tensor


class _FourierCorrection(nn.Module):
    def __init__(
        self,
        *,
        frequencies: tuple[float, ...],
        output_scales: torch.Tensor,
        hidden_width: int,
        hidden_layers: int,
        correction_fraction: float,
    ) -> None:
        super().__init__()
        if not frequencies or any(frequency <= 0.0 for frequency in frequencies):
            raise ValueError("Fourier frequencies must be positive")
        self.register_buffer(
            "frequencies", torch.tensor(frequencies, dtype=torch.float64)
        )
        self.register_buffer("output_scales", output_scales.detach().clone())
        if not 0.0 < correction_fraction <= 1.0:
            raise ValueError("Fourier correction fraction must lie in (0, 1]")
        self.correction_fraction = float(correction_fraction)
        encoded_width = 2 * 3 * len(frequencies)
        self.network = make_mlp(
            encoded_width,
            int(output_scales.numel()),
            hidden_width=hidden_width,
            hidden_layers=hidden_layers,
        )
        final = self.network[-1]
        assert isinstance(final, nn.Linear)
        nn.init.zeros_(final.weight)
        nn.init.zeros_(final.bias)

    def forward(self, coordinates: torch.Tensor) -> torch.Tensor:
        angles = (
            2.0
            * math.pi
            * coordinates.unsqueeze(-1)
            * self.frequencies.to(dtype=coordinates.dtype, device=coordinates.device)
        )
        encoded = torch.cat(
            [torch.sin(angles).flatten(1), torch.cos(angles).flatten(1)], dim=1
        )
        return (
            coordinates[:, 2:3]
            * self.correction_fraction
            * self.output_scales.to(dtype=coordinates.dtype, device=coordinates.device)
            * torch.tanh(self.network(encoded))
        )


class SharedPhaseHotspotRepresentation(nn.Module):
    """Add multi-frequency corrections behind one electro-phase gate interface."""

    def __init__(
        self,
        *,
        parameters: QPopParameters,
        hidden_width: int,
        hidden_layers: int,
        gate_floor: float = 0.05,
    ) -> None:
        super().__init__()
        if not 0.0 < gate_floor < 1.0:
            raise ValueError("gate floor must lie strictly between zero and one")
        self.parameters_contract = parameters
        self.gate_floor = float(gate_floor)
        current_scale = max(
            abs(parameters.current_initial) * 5.0,
            abs(parameters.drive_voltage / parameters.resistor) * 5.0,
            1.0e-12,
        )
        output_scales = torch.tensor(
            [
                1.6,
                1.6,
                20.0,
                20.0,
                parameters.drive_voltage,
                0.5,
                current_scale,
            ],
            dtype=torch.float64,
        )
        branch_width = max(8, hidden_width)
        self.mid_branch = _FourierCorrection(
            frequencies=(1.0, 2.0),
            output_scales=output_scales,
            hidden_width=branch_width,
            hidden_layers=hidden_layers,
            correction_fraction=0.005,
        )
        self.high_branch = _FourierCorrection(
            frequencies=(4.0, 8.0),
            output_scales=output_scales,
            hidden_width=branch_width,
            hidden_layers=hidden_layers,
            correction_fraction=0.005,
        )

    def _physical_gate(
        self, coordinates: torch.Tensor, base_fields: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        if coordinates.ndim != 2 or coordinates.shape[1] != 3:
            raise ValueError("PHA coordinates must have normalized x, y, t columns")
        if base_fields.ndim != 2 or base_fields.shape[1] != 7:
            raise ValueError("PHA base fields must contain the seven Q-POP unknowns")
        p = self.parameters_contract
        eta = base_fields[:, 0:1]
        mu = base_fields[:, 1:2]
        phi = base_fields[:, 4:5]
        temperature = base_fields[:, 5:6]
        current = base_fields[:, 6:7]
        physical_xy = torch.stack(
            [coordinates[:, 0] * p.lx, coordinates[:, 1] * p.ly], dim=1
        )
        tc_variance = p.tc_variance(physical_xy).unsqueeze(1)
        structural_rate_proxy = torch.abs(
            2.0 * p.structural_mobility * p.dfb_deta(
                temperature, eta, mu, tc_variance
            )
        )
        phase_indicator = structural_rate_proxy / (1.0 + structural_rate_proxy)

        power_proxy = torch.abs(current * phi)
        power_scale = max(
            abs(p.current_initial * p.drive_voltage),
            abs(p.current_initial * p.phi_initial),
            1.0e-12,
        )
        joule_indicator = power_proxy / (power_scale + power_proxy)
        combined = 1.0 - (1.0 - phase_indicator) * (1.0 - joule_indicator)
        physical_gate = self.gate_floor + (1.0 - self.gate_floor) * combined
        return physical_gate, phase_indicator, joule_indicator

    def forward(
        self,
        coordinates: torch.Tensor,
        base_fields: torch.Tensor,
        *,
        gate_capacity: bool,
    ) -> PhaseHotspotOutput:
        physical_gate, phase_indicator, joule_indicator = self._physical_gate(
            coordinates, base_fields
        )
        capacity_gate = (
            physical_gate if gate_capacity else torch.ones_like(physical_gate)
        )
        fields = (
            base_fields
            + self.mid_branch(coordinates)
            + capacity_gate * self.high_branch(coordinates)
        )
        return PhaseHotspotOutput(
            fields=fields,
            physical_gate=physical_gate,
            capacity_gate=capacity_gate,
            phase_indicator=phase_indicator,
            joule_indicator=joule_indicator,
        )
