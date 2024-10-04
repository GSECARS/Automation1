#!/usr/bin/python3
# ----------------------------------------------------------------------------------
# Project: PyAutomation
# File: controller.py
# ----------------------------------------------------------------------------------
# Purpose:
# This file is used to define the AerotechController class which is used to control
# the Aerotech controller. The AerotechController class is used to connect to the
# Aerotech controller, start the controller, disconnect from the controller, get the
# current position of an axis, and move an axis linearly.
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

from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable, cast, TypeVar

from automation1 import AxisStatusItem, Controller, StatusItemConfiguration

from pyautomation.utils import print_output


MethodType = TypeVar("MethodType", bound=Callable[..., Any])


def requires_automation1_connection(method: MethodType) -> MethodType:
    """Decorator to handle connecting and disconnecting from the controller."""

    @wraps(method)
    def wrapper(self: "AerotechController", *args: Any, **kwargs: Any) -> Any:
        if not self._automation1:
            print_output(
                message="You are not connected to a controller!",
                verbose=self.verbose,
            )
            return None
        return method(self, *args, **kwargs)

    return cast(MethodType, wrapper)


@dataclass
class AutomationAxis:
    """Class to represent an axis on the Aerotech controller."""

    name: str = field(compare=False)
    counts_per_unit: float = field(compare=False)


@dataclass
class AerotechController:
    """Class to represent the Aerotech controller."""

    ip: str = field(compare=False)
    axis: list[AutomationAxis] = field(compare=False)
    verbose: bool = field(default=False, compare=False)

    _automation1: Controller | None = field(init=False, repr=False, compare=False, default=None)

    def connect(self) -> None:
        """Connects Aerotech controller."""
        if self._automation1:
            print_output(message="Already connected!", verbose=self.verbose)
        else:
            self._automation1 = Controller.connect(host=self.ip)
            print_output(
                message=f"Connected to controller with IP of {self.ip}.",
                verbose=self.verbose,
            )

    @requires_automation1_connection
    def start(self) -> None:
        """Starts the Aerotech controller."""
        self._automation1.start()  # type: ignore
        print_output(
            message=f"Started the Aerotech controller at {self.ip}.",
            verbose=self.verbose,
        )

    @requires_automation1_connection
    def disconnect(self) -> None:
        """Disconnects from the connected Aerotech controller."""
        self._automation1.disconnect()  # type: ignore
        print_output(
            message=f"Disconnected from the Aerotech controller at {self.ip}.",
            verbose=self.verbose,
        )

    @requires_automation1_connection
    def get_current_position(self, axis: AutomationAxis) -> float:
        """Gets the current position of the axis."""
        item_config = StatusItemConfiguration()
        item_config.axis.add(AxisStatusItem.ProgramPosition, axis.name)
        current_position = float(self._automation1.runtime.status.get_status_items(item_config).axis.get(AxisStatusItem.ProgramPosition, axis.name).value)
        return round(current_position, 4)

    @requires_automation1_connection
    def move_linear(self, axis: AutomationAxis, distance: float, speed: float) -> None:
        """Moves the axis linearly."""
        self._automation1.runtime.commands.motion.move_linear(axes=axis.name, distances=[distance], coordinated_speed=speed)
        print_output(
            message=f"Moved axis {axis.name} {distance} units.",
            verbose=self.verbose,
        )

    @property
    def automation1(self) -> Controller | None:
        return self._automation1
