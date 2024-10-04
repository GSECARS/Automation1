#!/usr/bin/python3
# ----------------------------------------------------------------------------------
# Project: PyAutomation
# File: modules.py
# ----------------------------------------------------------------------------------
# Purpose:
# This file is used to define the PSO modules and the trajectory class. The PSO
# modules are used to control the PSO modules on the Aerotech controller. The
# trajectory class is used to calculate the distance, velocity, acceleration
# distance, and taxi distance of the trajectory.
# ----------------------------------------------------------------------------------
# Author: Christofanis Skordas
#
# Copyright (C) 2024 GSECARS, The University of Chicago, USA
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
# ----------------------------------------------------------------------------------

from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from automation1 import PsoDistanceInput, PsoWindowInput, PsoWaveformMode, PsoOutputSource, PsoOutputPin

from pyautomation.controller import AerotechController, AutomationAxis


@dataclass
class PsoModuleBase(ABC):
    """Abstract base class for PSO modules."""

    controller: AerotechController = field(compare=False)
    axis: AutomationAxis = field(compare=False)

    @abstractmethod
    def prepare_module(self) -> None:
        """Prepares the PSO module for use."""
        pass

    @abstractmethod
    def enable(self) -> None:
        """Enables the PSO module."""
        pass

    @abstractmethod
    def disable(self) -> None:
        """Disables the PSO module."""
        pass

    def convert_to_counts(self, units: float) -> int:
        """Converts to encoder counts"""
        return int(self.axis.counts_per_unit * units)


@dataclass
class PsoDistance(PsoModuleBase):
    """PSO distance module."""

    def prepare_module(self, pso_distance_input: PsoDistanceInput, distance: float, number_of_pulses) -> None:
        """Prepares the PSO module for use."""
        # Configure which encoder signal to track
        self.controller.automation1.runtime.commands.pso.pso_distance_configure_inputs(
            axis=self.axis.name,
            inputs=[pso_distance_input],
        )
        # Configure the PSO distance module to fire every "distance" counts
        self.controller.automation1.runtime.commands.pso.pso_distance_configure_fixed_distance(
            axis=self.axis.name,
            distance=self.convert_to_counts(distance / number_of_pulses),
        )

    def enable(self) -> None:
        """Enables the PSO module."""
        # Enables the PSO distance counter
        self.controller.automation1.runtime.commands.pso.pso_distance_counter_on(axis=self.axis.name)
        # Enables the PSO distance event module
        self.controller.automation1.runtime.commands.pso.pso_distance_events_on(axis=self.axis.name)

    def disable(self) -> None:
        """Disables the PSO module."""
        # Disable the PSO distance counter
        self.controller.automation1.runtime.commands.pso.pso_distance_counter_off(axis=self.axis.name)
        # Disable the PSO distance event module
        self.controller.automation1.runtime.commands.pso.pso_distance_events_off(axis=self.axis.name)


@dataclass
class PsoWindow(PsoModuleBase):
    """PSO window module."""

    def prepare_module(self, pso_window_input: PsoWindowInput, start_position: float, end_position: float, direction: int) -> None:
        # Set direction of travel for Automation1
        direction = 0 if direction == -1 else 1

        # Setup which window to use (0 or 1)
        self.controller.automation1.runtime.commands.pso.pso_window_configure_input(
            axis=self.axis.name,
            window_number=0,
            input=pso_window_input,
            reverse_direction=direction,
        )
        # Setup the window range
        self.controller.automation1.runtime.commands.pso.pso_window_configure_fixed_range(
            axis=self.axis.name,
            window_number=0,
            lower_bound=self.convert_to_counts(start_position),
            upper_bound=self.convert_to_counts(end_position),
        )

    def enable(self) -> None:
        # Enable the window output
        self.controller.automation1.runtime.commands.pso.pso_window_output_on(axis=self.axis.name, window_number=0)
        # Configure the event mask to include the window output
        self.controller.automation1.runtime.commands.pso.pso_event_configure_mask(axis=self.axis.name, event_mask=0)

    def disable(self) -> None:
        # Disable the PSO window output
        self.controller.automation1.runtime.commands.pso.pso_window_output_off(axis=self.axis.name, window_number=0)


@dataclass
class PsoWaveform(PsoModuleBase):
    """PSO waveform module"""

    def prepare_module(self, exposure: float) -> None:
        # Configure the waveform module for pulse mode
        self.controller.automation1.runtime.commands.pso.pso_waveform_configure_mode(axis=self.axis.name, waveform_mode=PsoWaveformMode.Pulse)
        # Configure the PSO total time per fixed distance pulse in microseconds
        self.controller.automation1.runtime.commands.pso.pso_waveform_configure_pulse_fixed_total_time(
            axis=self.axis.name,
            total_time=(exposure * 1000000 * 0.1),  # convert to microseconds
        )
        # Configure the PSO total ON time per pulse (50% duty cycle) in microseconds
        self.controller.automation1.runtime.commands.pso.pso_waveform_configure_pulse_fixed_on_time(
            axis=self.axis.name,
            on_time=((exposure * 1000000) / 2),  # convert to microseconds and 50% duty cycle
        )
        # Configure the number of output events per pulse
        self.controller.automation1.runtime.commands.pso.pso_waveform_configure_pulse_fixed_count(axis=self.axis.name, pulse_count=1)
        # Apply waveform configuration
        self.controller.automation1.runtime.commands.pso.pso_waveform_apply_pulse_configuration(axis=self.axis.name)

    def enable(self) -> None:
        """Enable the waveform module."""
        self.controller.automation1.runtime.commands.pso.pso_waveform_on(axis=self.axis.name)

    def disable(self) -> None:
        """Disable the waveform module."""
        self.controller.automation1.runtime.commands.pso.pso_waveform_off(axis=self.axis.name)


@dataclass
class PsoOutput:
    """PSO output module."""

    controller: AerotechController = field(compare=False)
    axis: AutomationAxis = field(compare=False)

    def prepare_module(self, pso_output_pin: PsoOutputPin) -> None:
        # Configure the waveform module as the PSO output
        self.controller.automation1.runtime.commands.pso.pso_output_configure_source(axis=self.axis.name, output_source=PsoOutputSource.Waveform)
        # Setup the physical output pin
        self.controller.automation1.runtime.commands.pso.pso_output_configure_output(axis=self.axis.name, output=pso_output_pin)


@dataclass
class PSO:
    controller: AerotechController = field(compare=False)
    axis: AutomationAxis = field(compare=False)
    pso_distance_input: PsoDistanceInput = field(compare=False)
    pso_window_input: PsoWindowInput = field(compare=False)
    pso_output_pin: PsoOutputPin = field(compare=False)

    _pso_distance_module: PsoDistance = field(init=False, repr=False, compare=False)
    _pso_window_module: PsoWindow = field(init=False, repr=False, compare=False)
    _pso_waveform_module: PsoWaveform = field(init=False, repr=False, compare=False)
    _pso_output_module: PsoOutput = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        self._pso_distance_module = PsoDistance(controller=self.controller, axis=self.axis)
        self._pso_window_module = PsoWindow(controller=self.controller, axis=self.axis)
        self._pso_waveform_module = PsoWaveform(controller=self.controller, axis=self.axis)
        self._pso_output_module = PsoOutput(controller=self.controller, axis=self.axis)

    def prepare_modules(
        self,
        distance: float,
        start_position: float,
        end_position: float,
        number_of_pulses: int,
        exposure: float,
        travel_direction: int,
    ) -> None:
        """Prepares the PSO modules for use."""
        self._pso_distance_module.prepare_module(pso_distance_input=self.pso_distance_input, distance=distance, number_of_pulses=number_of_pulses)
        self._pso_window_module.prepare_module(
            pso_window_input=self.pso_window_input,
            start_position=start_position,
            end_position=end_position,
            direction=travel_direction,
        )
        self._pso_waveform_module.prepare_module(exposure=exposure)
        self._pso_output_module.prepare_module(pso_output_pin=self.pso_output_pin)

    def enable_modules(self) -> None:
        """Enables the PSO modules."""
        self._pso_distance_module.enable()
        self._pso_window_module.enable()
        self._pso_waveform_module.enable()

    def disable_modules(self) -> None:
        """Disables the PSO modules."""
        self._pso_distance_module.disable()
        self._pso_window_module.disable()
        self._pso_waveform_module.disable()


@dataclass
class Trajectory:

    start_position: float = field(compare=False)
    end_position: float = field(compare=False)
    exposure: float = field(compare=False)
    number_of_pulses: int = field(compare=False)
    travel_direction: int = field(compare=False)
    accel_time: float = field(default=2.0, compare=False)
    base_velocity: float = field(default=10.0, compare=False)

    _distance: float = field(init=False, repr=False, compare=False)
    _velocity: float = field(init=False, repr=False, compare=False)
    _accel_distance: float = field(init=False, repr=False, compare=False)
    _taxi_distance: float = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        # Calculate the distance
        self._distance = abs(self.end_position - self.start_position)
        # Calculate the velocity
        self._velocity = self._distance / (self.exposure * self.number_of_pulses)
        # Calculate the acceleration distance
        self._accel_distance = self._compute_acceleration_distance()

    def _compute_acceleration_distance(self) -> float:
        """Computes the acceleration distance for the trajectory."""
        return self.accel_time / 2.0 * self._velocity

    @property
    def distance(self) -> float:
        return self._distance

    @property
    def velocity(self) -> float:
        return self._velocity

    @property
    def accel_distance(self) -> float:
        return self._accel_distance

    @property
    def taxi_distance(self) -> float:
        return self._taxi_distance

    @taxi_distance.setter
    def taxi_distance(self, value: float) -> None:
        self._taxi_distance = value
