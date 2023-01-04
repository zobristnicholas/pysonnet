import os
import numpy as np
from pysonnet import outputs


def test_load_spectre():
    directory = os.path.dirname(__file__)
    file_name = os.path.join(os.path.join(directory, "data"), "two_coupled_lines.dat")
    model = outputs.NCoupledLines.from_spectre(file_name)
    assert model.frequencies.shape == (5, 1, 1)
    np.testing.assert_allclose(model.frequencies.ravel(), [4e9, 5e9, 6e9, 7e9, 8e9])
    assert model.inductance.shape == (5, 2, 2)
    assert model.resistance.shape == (5, 2, 2)
    assert model.capacitance.shape == (5, 2, 2)
    assert model.conductance.shape == (5, 2, 2)
    np.testing.assert_allclose(model.characteristic_impedance[:, 0], 52.31121352 + 2.40510447783e-5j, rtol=1e-5)
    np.testing.assert_allclose(model.characteristic_impedance[:, 1], 61.60609002 + 2.8326590859e-5j, rtol=1e-5)
    np.testing.assert_allclose(model.effective_relative_permittivity[:, 0], 6.4986057995 - 5.9778267033e-6j, rtol=1e-5)
    np.testing.assert_allclose(model.effective_relative_permittivity[:, 1], 6.4627453529 - 5.9449212497e-6j, rtol=1e-5)
