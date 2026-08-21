"""Explicit Q-POP IMT physical parameters and constitutive relations.

The formulas mirror the frozen CPC-v1 ``qpop-imt.py`` source.  Values are kept
in the source program's dimensionless units: nm, ns, 338 K, and mV are the
base scales for space, time, temperature, and voltage respectively.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path
import xml.etree.ElementTree as ET

import torch


def fermi(gamma: torch.Tensor) -> torch.Tensor:
    regular = 1.0 / (
        torch.exp(-gamma)
        + 3.0 * math.sqrt(math.pi) / 4.0 * (4.0 + gamma.square()).pow(-0.75)
    )
    high = 4.0 / (3.0 * math.sqrt(math.pi)) * (4.0 + gamma.square()).pow(0.75)
    return torch.where(gamma < -100.0, torch.zeros_like(gamma), torch.where(gamma > 100.0, high, regular))


def dfermi(gamma: torch.Tensor) -> torch.Tensor:
    regular_fermi = 1.0 / (
        torch.exp(-gamma)
        + 3.0 * math.sqrt(math.pi) / 4.0 * (4.0 + gamma.square()).pow(-0.75)
    )
    regular = regular_fermi.square() * (
        torch.exp(-gamma)
        + 9.0 * math.sqrt(math.pi) / 8.0
        * (4.0 + gamma.square()).pow(-1.75)
        * gamma
    )
    high = 2.0 / math.sqrt(math.pi) * gamma * (4.0 + gamma.square()).pow(-0.25)
    return torch.where(gamma < -100.0, torch.zeros_like(gamma), torch.where(gamma > 100.0, high, regular))


def _value(root: ET.Element, path: str, default: float) -> float:
    element = root.find(path)
    return default if element is None or element.text is None else float(element.text)


@dataclass(frozen=True)
class QPopParameters:
    lx: float
    ly: float
    lz: float
    terminal_time: float
    ramp_time: float
    substrate_temperature: float
    drive_voltage: float
    resistor: float
    capacitor: float
    eta_initial: float
    mu_initial: float
    temperature_initial: float
    gamma_e_initial: float
    gamma_h_initial: float
    phi_initial: float
    current_initial: float
    eta_surrounding: float
    mu_surrounding: float
    effective_boundary_length: float
    tc_shift: float
    nucleus_radius: float
    domain_wall_width: float
    kb: float
    charge: float
    unit_cell_volume: float
    tc: float
    t1: float
    t2: float
    an1: float
    an2: float
    an3: float
    au1: float
    au2: float
    au3: float
    gnu1: float
    gnu2: float
    gnu3: float
    chi: float
    structural_mobility: float
    structural_gradient: float
    electronic_mobility: float
    electronic_gradient: float
    electron_density_of_states: float
    hole_density_of_states: float
    electron_mobility_x: float
    electron_mobility_y: float
    hole_mobility_x: float
    hole_mobility_y: float
    recombination_rate: float
    permittivity: float
    volumetric_heat_capacity: float
    thermal_conductivity: float
    heat_transfer: float

    @classmethod
    def from_input(cls, path: Path) -> "QPopParameters":
        root = ET.parse(path).getroot()
        lunit = 1.0e-9
        tunit = 1.0e-9
        tempunit = 338.0
        boltzmann_si = 1.3806504e-23
        eunit = boltzmann_si * tempunit
        vunit = 1.0e-3
        cunit = eunit / vunit
        munit = eunit * (tunit / lunit) ** 2
        runit = vunit / (cunit / tunit)

        kb = boltzmann_si / eunit * tempunit
        charge = 1.602176487e-19 / cunit
        unit_cell_volume = 59.0e-30 / lunit**3
        tc = 338.0 / tempunit
        t1 = 275.0 / tempunit
        t2 = 270.0 / tempunit
        an1 = 2.05714 * kb * tc / unit_cell_volume
        an2 = (-0.623108 + 0.121228) / 2.0 * kb * tc / unit_cell_volume
        an3 = (0.330568 + 4.18947) / 4.0 * kb * tc / unit_cell_volume
        au1 = 3.94286 * kb * tc / unit_cell_volume
        au2 = (1.36767 - 3.67915) / 2.0 * kb * tc / unit_cell_volume
        au3 = (0.4 + 2.0) / 4.0 * kb * tc / unit_cell_volume
        gnu1 = 0.3 * kb * tc / unit_cell_volume
        gnu2 = (0.2 - 1.5 + 0.3 / 2.0) / 2.0 * kb * tc / unit_cell_volume
        gnu3 = (0.05 + 2.0) / 2.0 * kb * tc / unit_cell_volume
        chi = 0.286 * 1.602176487e-19 / eunit
        tau_lattice = 1.0e-12 / tunit
        structural_mobility = 1.0 / (tau_lattice * an1 * (tc - t1) / tc)
        structural_gradient = (1.602176487e-19 / 1.0e-9) / eunit * lunit
        tau_electronic = 10.0e-15 / tunit
        excited_density = 0.16 / unit_cell_volume
        electronic_mobility = 1.0 / (tau_electronic * chi * 2.0 * excited_density)
        electronic_gradient = structural_gradient
        density_of_states = 2.0 * (
            65.0
            * (9.10938215e-31 / munit)
            * kb
            * tc
            / (2.0 * math.pi * (1.054571628e-34 / eunit / tunit) ** 2)
        ) ** 1.5
        electron_mobility_y = 5.0e-5 / lunit**2 * vunit * tunit
        electron_mobility_x = electron_mobility_y * 0.5
        hole_mobility_y = electron_mobility_y / 1.2
        hole_mobility_x = hole_mobility_y * 0.5
        recombination_rate = 1.0 / (
            2.0
            * density_of_states
            * math.exp(-chi * 0.827987**2 / (kb * 322.0 / tempunit))
            * (14.235e-6 / tunit)
        )
        permittivity = 60.0 * (8.854187817e-12 * vunit / cunit * lunit)
        volumetric_heat_capacity = 690.0 * 4340.0 / eunit * lunit**3 * tempunit
        thermal_conductivity = 6.0 / eunit * tunit * lunit * tempunit
        heat_transfer = _value(root, "external/heatdiss", 3.0e6) / (
            eunit / (tunit * lunit**2 * tempunit)
        )

        lx = _value(root, "external/Lx", 50.0)
        ly = _value(root, "external/Ly", 20.0)
        lz = _value(root, "external/Lz", 36.0)
        terminal_time = _value(root, "time/endtime", 5000.0)
        substrate_temperature = _value(root, "external/temperature", 300.0) / tempunit
        drive_voltage = _value(root, "external/voltage", 0.07) / vunit
        resistor = _value(root, "external/resistor", 8.0e3) / runit
        capacitor = _value(root, "external/capacitor", 1.0) / (cunit / vunit / 1.0e-9)
        temperature_initial = _value(root, "initialization/temperature", 300.0) / tempunit
        eta_initial = _value(root, "initialization/SOP", 0.791296 * math.sqrt(2.0))
        mu_initial = _value(root, "initialization/EOP", -0.914352 * math.sqrt(2.0))
        gamma_e_initial = -(chi * mu_initial**2 / 2.0) / (kb * temperature_initial)
        gamma_h_initial = gamma_e_initial
        initial_device_resistance = ly / (
            charge
            * (
                density_of_states * math.exp(gamma_e_initial) * electron_mobility_y
                + density_of_states * math.exp(gamma_h_initial) * hole_mobility_y
            )
            * lx
            * lz
        )
        voltage_fraction = initial_device_resistance / (initial_device_resistance + resistor)
        phi_initial = drive_voltage * voltage_fraction
        current_initial = phi_initial / initial_device_resistance
        return cls(
            lx=lx,
            ly=ly,
            lz=lz,
            terminal_time=terminal_time,
            ramp_time=10.0,
            substrate_temperature=substrate_temperature,
            drive_voltage=drive_voltage,
            resistor=resistor,
            capacitor=capacitor,
            eta_initial=eta_initial,
            mu_initial=mu_initial,
            temperature_initial=temperature_initial,
            gamma_e_initial=gamma_e_initial,
            gamma_h_initial=gamma_h_initial,
            phi_initial=phi_initial,
            current_initial=current_initial,
            eta_surrounding=1.0,
            mu_surrounding=-1.0,
            effective_boundary_length=10.0,
            tc_shift=_value(root, "initialization/Tcvariance/Tcshift", -20.0) / tempunit,
            nucleus_radius=_value(root, "initialization/Tcvariance/radius", 3.0),
            domain_wall_width=10.0,
            kb=kb,
            charge=charge,
            unit_cell_volume=unit_cell_volume,
            tc=tc,
            t1=t1,
            t2=t2,
            an1=an1,
            an2=an2,
            an3=an3,
            au1=au1,
            au2=au2,
            au3=au3,
            gnu1=gnu1,
            gnu2=gnu2,
            gnu3=gnu3,
            chi=chi,
            structural_mobility=structural_mobility,
            structural_gradient=structural_gradient,
            electronic_mobility=electronic_mobility,
            electronic_gradient=electronic_gradient,
            electron_density_of_states=density_of_states,
            hole_density_of_states=density_of_states,
            electron_mobility_x=electron_mobility_x,
            electron_mobility_y=electron_mobility_y,
            hole_mobility_x=hole_mobility_x,
            hole_mobility_y=hole_mobility_y,
            recombination_rate=recombination_rate,
            permittivity=permittivity,
            volumetric_heat_capacity=volumetric_heat_capacity,
            thermal_conductivity=thermal_conductivity,
            heat_transfer=heat_transfer,
        )

    def tc_variance(self, coordinates_xy: torch.Tensor) -> torch.Tensor:
        x = coordinates_xy[..., 0]
        y = coordinates_xy[..., 1]
        radius = torch.sqrt((x - self.lx / 2.0).square() + y.square())
        return self.tc_shift * (
            -torch.tanh(
                2.0 * (radius - self.nucleus_radius) / self.domain_wall_width
            )
            + 1.0
        ) / 2.0

    def ramped_voltage(self, time_ns: torch.Tensor) -> torch.Tensor:
        return torch.where(
            time_ns <= self.ramp_time,
            self.phi_initial
            + (self.drive_voltage - self.phi_initial) * time_ns / self.ramp_time,
            torch.full_like(time_ns, self.drive_voltage),
        )

    def dfb_deta(
        self, temperature: torch.Tensor, eta: torch.Tensor, mu: torch.Tensor, tcvar: torch.Tensor
    ) -> torch.Tensor:
        return (
            self.an1 * (temperature - self.t1 - tcvar) / self.tc * eta
            + self.an2 * eta.pow(3)
            + self.an3 * eta.pow(5)
            + self.gnu1 * mu
            - self.gnu2 * eta * mu.square()
            + 1.5 * self.gnu3 * eta.square() * mu
        )

    def dfb_dmu(
        self, temperature: torch.Tensor, eta: torch.Tensor, mu: torch.Tensor, tcvar: torch.Tensor
    ) -> torch.Tensor:
        return (
            self.au1 * (temperature - self.t2 - tcvar) / self.tc * mu
            + self.au2 * mu.pow(3)
            + self.au3 * mu.pow(5)
            + self.gnu1 * eta
            - self.gnu2 * eta.square() * mu
            + 0.5 * self.gnu3 * eta.pow(3)
        )
