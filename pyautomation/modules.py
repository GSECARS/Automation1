from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from automation1 import (
    PsoDistanceInput,
    PsoWindowInput,
    PsoWaveformMode,
    PsoOutputSource,
    PsoOutputPin,
    PsoWindowEventMode
)

from pyautomation.controller import AerotechController, AutomationAxis


@dataclass
class PsoModuleBase(ABC):
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
        return int(self.controller.axis.counts_per_unit * units)


@dataclass
class PsoDistance(PsoModuleBase):
    """PSO module for distance."""

    def prepare_module(self, pso_distance_input: PsoDistanceInput, distance: float) -> None:
        """Prepares the PSO module for use."""
        # Configure which encoder signal to track
        self.controller.automation1.runtime.commands.pso.pso_distance_configure_inputs(
            axis=self.axis.name,
            inputs=[pso_distance_input],
        )
        # Configure the PSO distance module to fire every "distance" counts
        self.controller.automation1.runtime.commands.pso.pso_distance_configure_fixed_distance(
            axis=self.axis.name,
            distance=self.convert_to_counts(distance),
        )

    def enable(self) -> None:
        """Enables the PSO module."""
        # Enables the PSO distance counter
        self.controller.automation1.runtime.commands.pso.pso_distance_counter_on(axis=self.axis)
        # Enables the PSO distance event module
        self.controller.automation1.runtime.commands.pso.pso_distance_events_on(axis=self.axis)

    def disable(self) -> None:
        """Disables the PSO module."""
        # Disable the PSO distance counter
        self.controller.automation1.runtime.commands.pso.pso_distance_counter_off(axis=self.axis)
        # Disable the PSO distance event module
        self.controller.automation1.runtime.commands.pso.pso_distance_events_off(axis=self.axis)


@dataclass
class PsoWindow(PsoModuleBase):
    """PSO window module."""

    def prepare_module(self, pso_window_input: PsoWindowInput, start_position: float, end_position: float, direction: int) -> None:
        # Setup which window to use (0 or 1)
        self.controller.automation1.runtime.commands.pso.pso_window_configure_input(
            axis=self.axis,
            window=0,
            input=pso_window_input,
            reverse_direction=direction,
        )
        # Setup the window range
        self.controller.automation1.runtime.commands.pso.pso_window_configure_fixed_range(
            axis=self.axis,
            window=0,
            lower_bound=self.convert_to_counts(start_position),
            upper_bound=self.convert_to_counts(end_position),
        )

    def enable(self) -> None:
        # Enable the window output
        self.controller.automation1.runtime.commands.pso.pso_window_output_on(axis=self.axis, window_number=0)
        # Configure the event mask to include the window output
        self.controller.automation1.runtime.commands.pso.pso_event_configure_mask(
            axis=self.axis, event_mask=PsoWindowEventMode.PsoEventMask.WindowMask
        )

    def disable(self) -> None:
        # Disable the PSO window output
        self.controller.automation1.runtime.commands.pso.pso_window_output_off(axis=self.axis, window_number=0)


@dataclass
class PsoWaveform(PsoModuleBase):
    """PSO waveform module"""

    def prepare_module(self, exposure: float, number_of_pulses: int) -> None:
        # Configure the waveform module for pulse mode
        self.controller.automation1.runtime.commands.pso.pso_waveform_configure_mode(
            axis=self.axis, waveform_mode=PsoWaveformMode.Pulse
        )
        # Configure the PSO total time per fixed distance pulse in microseconds
        self.controller.automation1.runtime.commands.pso.pso_waveform_configure_pulse_fixed_total_time(
            axis=self.axis,
            total_time=(exposure * 1000),  # convert to microseconds
        )
        # Configure the PSO total ON time per pulse (50% duty cycle) in microseconds
        self.controller.automation1.runtime.commands.pso.pso_waveform_configure_pulse_fixed_on_time(
            axis=self.axis,
            on_time=((exposure * 1000) / 2),  # convert to microseconds and 50% duty cycle
        )
        # Configure the number of output events per pulse
        self.controller.automation1.runtime.commands.pso.pso_waveform_configure_pulse_fixed_count(
            axis=self.axis, pulse_count=1
        )
        # Apply waveform configuration
        self.controller.automation1.runtime.commands.pso.pso_waveform_apply_pulse_configuration(axis=self.axis)

    def enable(self) -> None:
        """Enable the waveform module."""
        self.controller.automation1.runtime.commands.pso.pso_waveform_on(axis=self.axis)

    def disable(self) -> None:
        """Disable the waveform module."""
        self.controller.automation1.runtime.commands.pso.pso_waveform_off(axis=self.axis)


@dataclass
class PsoOutput:
    """PSO output module."""
    controller: AerotechController = field(compare=False)
    axis: AutomationAxis = field(compare=False)

    def prepare_module(self, pso_output_pin: PsoOutputPin) -> None:
        # Configure the waveform module as the PSO output
        self.controller.automation1.runtime.commands.pso.pso_output_configure_source(
            axis=self.axis, output_source=PsoOutputSource.Waveform
        )
        # Setup the physical output pin
        self.controller.automation1.runtime.commands.pso.pso_output_configure_output(
            axis=self.axis,
            output=pso_output_pin
        )


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
        exposure: float,
        number_of_pulses: int,
        travel_direction: int = 0
    ) -> None:
        """Prepares the PSO modules for use."""
        self._pso_distance_module.prepare_module(pso_distance_input=self.pso_distance_input, distance=distance)
        self._pso_window_module.prepare_module(pso_window_input=self.pso_window_input, start_position=start_position, end_position=end_position, direction=travel_direction)
        self._pso_waveform_module.prepare_module(exposure=exposure, number_of_pulses=number_of_pulses)
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
