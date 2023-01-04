import os
import numpy as np
from pysonnet import outputs


def test_load_touchstone():
    directory = os.path.dirname(__file__)
    file_name = os.path.join(os.path.join(directory, "data"), "resonator_output_file.ts")
    response = outputs.SYZParameter.from_touchstone(file_name)
    assert response.f.size == 950
    np.testing.assert_allclose(response.f[[1, 100, 205, 800]], [5.335, 5.765, 5.915, 6.35])
    assert response.value.shape == (950, 2, 2)
    np.testing.assert_allclose(
        response.value[0],
        [[0.00239171+0.01962441j, 0.99266898-0.11923679j], [0.99266898-0.11923679j, 0.00232377+0.01963257j]],
        rtol=1e-6,
    )
    assert response.value_type == "s"
