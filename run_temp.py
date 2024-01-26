from automation1 import PsoDistanceInput, PsoWindowInput, PsoOutputPin
from pyautomation import PyAutomation
from pyautomation.controller import AutomationAxis

# Create the Axis objects. Temporary, only single axis is supported, so the first axis in the list is used.
theta_axis = AutomationAxis(name="Theta", counts_per_unit=1491308.0888888889)

# Create the PyAutomation object
pyautomation = PyAutomation(
    ip="192.168.1.10",
    axis=[theta_axis],
    verbose=True,
    pso_distance_input=PsoDistanceInput.iXC4ePrimaryFeedback,
    pso_window_input=PsoWindowInput.iXC4ePrimaryFeedback,
    pso_output_pin=PsoOutputPin.iXC4eAuxiliaryMarkerDifferential,
)
