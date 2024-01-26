from dataclasses import dataclass, field

from automation1 import PsoDistanceInput, PsoWindowInput, PsoOutputPin

from pyautomation import controller, modules, utils


__all__ = ["controller", "modules", "utils", "PyAutomation"]


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
