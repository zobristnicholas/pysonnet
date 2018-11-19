import os
import pytest
import numpy as np
from matplotlib import pyplot
from pysonnet import outputs


@pytest.fixture
def current_density():
    """Returns a CurrentDensity object using 'pysonnet/tests/data/M1_912_90p612.csv'"""
    directory = os.path.dirname(__file__)
    file_name = os.path.join(os.path.join(directory, "data"), "M1_912_90p612.csv")
    return outputs.CurrentDensity(file_name)


def test_default_unloaded(current_density):
    assert current_density._data_loaded is False
    assert current_density._header_loaded is False


def test_version(current_density):
    assert current_density.version == "VER : 2"


def test_sonnet_file_path(current_density):
    path = ("C:\\Users\\kids\\Documents\\Masks\\MEC\\device\\M1\\M1_v2\\" +
            "FinerSonnetSims\\M1_912_90p612.csv")
    assert current_density.sonnet_file_path == path


def test_sonnet_version(current_density):
    assert current_density.sonnet_version == "16.52"


def test_sonnet_file_name(current_density):
    assert current_density.sonnet_file_name == "M1_912_90p612"


def test_frequency(current_density):
    assert current_density.frequency == 5687140000.0


def test_ports(current_density):
    assert current_density.ports == [2, 1]


@pytest.mark.parametrize("port", [2, 1])
def test_drive_voltage(current_density, port):
    if port == 1:
        assert current_density.drive_voltage(port) == 1.0
    elif port == 2:
        assert current_density.drive_voltage(port) == 0.0


@pytest.mark.parametrize("port", [2, 1])
def test_drive_phase(current_density, port):
    assert current_density.drive_phase(port) == 0.0


def test_level_string(current_density):
    assert current_density.level_string == '1'


def test_level(current_density):
    assert type(current_density.level) is int
    assert current_density.level == 1


def test_position_unit_string(current_density):
    assert current_density.position_unit_string == "µm"


def test_position_unit(current_density):
    assert current_density.position_unit == 1e-6


def test_dx(current_density):
    assert current_density.dx == 0.5


def test_dy(current_density):
    assert current_density.dy == 0.05


def test_area(current_density):
    assert current_density.area == 2.5e-14


def test_area_unit_string(current_density):
    assert current_density.area_unit_string == "m^2"


def test_current_unit_string(current_density):
    assert current_density.current_unit_string == "A/m"


def test_x_position(current_density):
    assert current_density.x_position.shape == (265,)


def test_y_position(current_density):
    assert current_density.y_position.shape == (2820,)


def test_current_density(current_density):
    assert current_density.current_density().shape == (2820, 265)
    assert np.mean(current_density.current_density()) == 73295.98813106936
    assert (np.mean(current_density.current_density(power=-23.2, impedance=23.3)) ==
            1094.6446591536262)


def test_trim_data(current_density):
    current_density.trim_data(40, 140, 140, 160)
    assert current_density.x_position.shape == (200,)
    assert current_density.y_position.shape == (400,)
    assert current_density.current_density().shape == (400, 200)


def test_plot_current(current_density):
    current_density.plot_current(block=False)
    current_density.plot_current(power=-100, impedance=45, scale=2, block=False)
    _, axis = pyplot.subplots()
    current_density.plot_current(axis=axis, block=False)
    pyplot.close("all")


def test_copy(current_density):
    copy = current_density.copy()
    assert copy is not current_density


def test_deepcopy(current_density):
    deepcopy = current_density.deepcopy()
    assert deepcopy is not current_density
