from dataclasses import dataclass, field
from functools import wraps
from typing import Any, Callable

from automation1 import Controller

from pyautomation.utils import print_output


def requires_automation1_connection(method: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to handle connecting and disconnecting from the controller."""

    @wraps(method)
    def wrapper(self: 'AerotechController', *args: Any, **kwargs: Any) -> Any:
        if not self._automation1:
            print_output(
                message="You are not connected to a controller!",
                verbose=self.verbose,
            )
            return
        return method(self, *args, **kwargs)

    return wrapper

@dataclass
class AutomationAxis:
    name: str = field(compare=False)
    counts_per_unit: float = field(compare=False)


@dataclass
class AerotechController:
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
        self._automation1.start()
        print_output(
            message=f"Started the Aerotech controller at {self.ip}.",
            verbose=self.verbose,
        )

    @requires_automation1_connection
    def disconnect(self) -> None:
        """Disconnects from the connected Aerotech controller."""
        self._automation1.disconnect()
        print_output(
            message=f"Disconnected from the Aerotech controller at {self.ip}.",
            verbose=self.verbose,
        )

    @property
    def automation1(self) -> Controller | None:
        return self._automation1
