import time
from automation1 import PsoDistanceInput, PsoWindowInput, PsoOutputPin
from pyautomation import PyAutomation
from pyautomation.controller import AutomationAxis
from pyautomation.modules import Trajectory

# Create the Axis objects. Temporary, only single axis is supported, so the first axis in the list is used.
theta_axis = AutomationAxis(name="Theta", counts_per_unit=1491308.0888888889)

# Create the PyAutomation object
pyautomation = PyAutomation(
    ip="10.54.160.27",
    axis=[theta_axis],
    verbose=True,
    pso_distance_input=PsoDistanceInput.iXC4ePrimaryFeedback,
    pso_window_input=PsoWindowInput.iXC4ePrimaryFeedback,
    pso_output_pin=PsoOutputPin.iXC4eAuxiliaryMarkerDifferential,
)

trj = Trajectory(start_position=0, end_position=3.0, exposure=1, number_of_pulses=3, travel_direction=1)

pyautomation.enable_controller()
pyautomation.load_trajectory(trj)
pyautomation.run_trajectory()
pyautomation.disable_controller()
