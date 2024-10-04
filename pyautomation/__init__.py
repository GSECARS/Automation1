#!/usr/bin/python3
# ----------------------------------------------------------------------------------
# Project: PyAutomation
# File: pyautomation/__init__.py
# ----------------------------------------------------------------------------------
# Purpose:
# This file is used to define the PyAutomation class which is the main class of the
# PyAutomation package. The PyAutomation class is used to control the Aerotech
# controller and the PSO modules. The class is used to load and run trajectories
# on the PSO modules.
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

import time
from dataclasses import dataclass, field
from functools import wraps
from math import ceil
from typing import Any, Callable

from automation1 import PsoDistanceInput, PsoWindowInput, PsoOutputPin

from pyautomation import controller, modules, utils


__all__ = ["controller", "modules", "utils", "PyAutomation"]


def with_active_trajectory(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to check if there is an active trajectory."""

    @wraps(method)
    def wrapper(self: "PyAutomation", *args: Any, **kwargs: Any) -> Any:
        if self._active_trajectory is None:
            print("No active trajectory!", verbose=self.verbose)
            return
        return method(self, *args, **kwargs)

    return wrapper


@dataclass
class PyAutomation:
    ip: str = field(compare=False)
    axis: list[controller.AutomationAxis] = field(compare=False)
    pso_distance_input: PsoDistanceInput = field(compare=False)
    pso_window_input: PsoWindowInput = field(compare=False)
    pso_output_pin: PsoOutputPin = field(compare=False)
    verbose: bool = field(default=False, compare=False)

    _controller: controller.AerotechController = field(init=False, compare=False)
    _pso: modules.PSO = field(init=False, compare=False)

    _pre_trj_position: float = field(init=False, repr=False, compare=False)
    _active_trajectory: modules.Trajectory | None = field(init=False, repr=False, compare=False, default=None)
    _is_valid_trj: bool = field(init=False, repr=False, compare=False, default=False)

    def __post_init__(self) -> None:
        self._controller = controller.AerotechController(ip=self.ip, axis=self.axis, verbose=self.verbose)
        self._pso = modules.PSO(
            controller=self._controller,
            axis=self.axis[0],
            pso_distance_input=self.pso_distance_input,
            pso_window_input=self.pso_window_input,
            pso_output_pin=self.pso_output_pin,
        )

    def enable_controller(self) -> None:
        """Connects and starts the Aerotech controller."""
        self._controller.connect()
        self._controller.start()

    def disable_controller(self) -> None:
        """Disconnects the Aerotech controller."""
        self._controller.disconnect()

    @with_active_trajectory
    def _validate_direction(self) -> None:
        """Validates the trajectory direction."""
        # Helper variables
        start_position = self._active_trajectory.start_position
        end_position = self._active_trajectory.end_position
        direction = self._active_trajectory.travel_direction

        if direction == 1:
            # Positive direction
            # Check if start position is less than end position
            if start_position > end_position:
                self._active_trajectory = None
                utils.print_output("Trajectory direction is invalid!", verbose=self.verbose)
                self._is_valid_trj = False
                return
        elif direction == -1:
            # Negative direction
            # Check if start position is greater than end position
            if start_position < end_position:
                self._active_trajectory = None
                utils.print_output("Trajectory direction is invalid!", verbose=self.verbose)
                self._is_valid_trj = False
                return
        self._is_valid_trj = True

    @with_active_trajectory
    def _compute_taxi_distance(self) -> None:
        """Computes the taxi distance for the trajectory."""
        self._active_trajectory.taxi_distance = ceil(self._active_trajectory.accel_distance + (self._active_trajectory.accel_distance * 0.001))

    @with_active_trajectory
    def _prepare_pso(self) -> None:
        """Prepares the PSO for use."""
        self._pso.prepare_modules(
            distance=self._active_trajectory.distance,
            start_position=self._active_trajectory.start_position,
            end_position=self._active_trajectory.end_position,
            number_of_pulses=self._active_trajectory.number_of_pulses,
            exposure=self._active_trajectory.exposure,
            travel_direction=self._active_trajectory.travel_direction,
        )

    @with_active_trajectory
    def _move_to_starting_position(self) -> None:
        """Moves the axis to the starting position."""
        self._pre_trj_position = self._controller.get_current_position(self.axis[0])

        if self._active_trajectory.start_position > self._pre_trj_position:
            starting_position = abs(self._pre_trj_position - self._active_trajectory.start_position)
        elif self._active_trajectory.start_position < self._pre_trj_position:
            starting_position = -abs(self._active_trajectory.start_position - self._pre_trj_position)
        else:
            starting_position = self._pre_trj_position

        # Move to starting position
        self._controller.move_linear(
            axis=self.axis[0],
            distance=starting_position + (-self._active_trajectory.taxi_distance * self._active_trajectory.travel_direction),
            speed=self._active_trajectory.base_velocity,
        )

    @with_active_trajectory
    def _reset_axis(self) -> None:
        """Resets the axis to its previous state."""
        # Disable PSO modules
        self._pso.disable_modules()
        # Revert axis to pre trajectory position
        current_position = self._controller.get_current_position(self.axis[0])
        if current_position > self._pre_trj_position:
            self._controller.move_linear(
                axis=self.axis[0],
                distance=-abs(self._pre_trj_position - current_position),
                speed=self._active_trajectory.base_velocity,
            )
        elif current_position < self._pre_trj_position:
            self._controller.move_linear(
                axis=self.axis[0],
                distance=abs(current_position - self._pre_trj_position),
                speed=self._active_trajectory.base_velocity,
            )

    def load_trajectory(self, trajectory: modules.Trajectory) -> None:
        """Loads a trajectory into the PSO."""
        # Set the active trajectory
        self._active_trajectory = trajectory

        # Validate the trajectory direction
        self._validate_direction()

        if self._is_valid_trj:
            # Calculate the taxi distance
            self._compute_taxi_distance()
            # Prepare PSO modules
            self._prepare_pso()

    def run_trajectory(self) -> None:
        """Starts the trajectory."""
        # Skip if there is no active valid trajectory
        if not self._is_valid_trj:
            return

        # Move to starting position
        self._move_to_starting_position()
        # Enable PSO modules
        self._pso.enable_modules()
        # Start the trajectory
        time.sleep(0.1)
        total_distance = self._active_trajectory.distance + abs(self._active_trajectory.taxi_distance)
        self._controller.move_linear(
            self.axis[0],
            distance=total_distance * self._active_trajectory.travel_direction,
            speed=self._active_trajectory.velocity,
        )
        time.sleep(0.1)
        # Revert axis to previous state
        self._reset_axis()

    def abort_trajectory(self) -> None:
        """Aborts the trajectory."""
        pass
