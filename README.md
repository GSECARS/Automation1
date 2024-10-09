# PyAutomation

![License](https://img.shields.io/badge/license-MIT-orange.svg) ![Python](https://img.shields.io/badge/python-v3.12-22558a.svg?logo=python&color=22558a)

A simple library used to interface with the Aerotech automation1 controller API.

------------
## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)

------------
## Installation

There are two methods that you can install the library:

### Requirements

Before you begin, ensure you have met the following requirements:

>  Python >= 3.12  
>
> Aerotech automation1 API - [click here for more information](http://help.aerotech.com/automation1/Content/APIs/Python/Get-Started/Intro-to-Python.htm)

### PyPI
To install from PyPI run:

```bash
pip install pyautomation
```

### Source

To install the library from source, first clone the repository and navigate into the project directory:

```bash
git clone https://github.com/GSECARS/PyAutomation.git && cd PyAutomation
```

If you want to install the project in development mode run:
```bash
pip install -e ".[development]"
```
otherwise just run:
```bash
pip install .
```

------------
## Usage

> ⚠️ **Warning:** To work around how PSO functions, an additional step is added as a taxi distance for each trajectory. For example, if you are running
> a trajectory from 0 to 10 with a step size of 2, the starting position will be at -2. This is a work in progress, more testing is required!

Below is an example of how to use the PyAutomation library to control an Aerotech automation1 controller, tested to work with the iXC4e.

First, import the necessary modules and create the AutomationAxis and PyAutomation objects:

```python
from automation1 import PsoDistanceInput, PsoWindowInput, PsoOutputPin
from pyautomation import PyAutomation
from pyautomation.controller import AutomationAxis
from pyautomation.modules import Trajectory

# Create the Axis objects.
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
```

Next, create a Trajectory object and configure it with the desired parameters:

```python
trj = Trajectory(start_position=0, end_position=3.0, exposure=1, number_of_pulses=3, travel_direction=1)
```

Enable the controller, load the trajectory, run it, and then disable the controller:
```python
pyautomation.enable_controller()
pyautomation.load_trajectory(trj)
pyautomation.run_trajectory()
pyautomation.disable_controller()
```

------------
## Contributing

All contributions to PyAutomation are welcome! Here are some ways you can help:
- Report a bug by opening an [issue](https://github.com/GSECARS/PyAutomation/issues).
- Add new features, fix bugs or improve documentation by submitting a [pull request](https://github.com/GSECARS/PyAutomation/pulls).

Please adhere to the [GitHub flow](https://docs.github.com/en/get-started/quickstart/github-flow) model when making your contributions! This means creating a new branch for each feature or bug fix, and submitting your changes as a pull request against the main branch. If you're not sure how to contribute, please open an issue and we'll be happy to help you out.

By contributing to PyAutomation, you agree that your contributions will be licensed under the MIT License.

[back to top](#table-of-contents)

------------
## License

PyAutomation is distributed under the MIT license. You should have received a [copy](LICENSE) of the MIT License along with this program. If not, see https://mit-license.org/ for additional details.