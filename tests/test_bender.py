import plistlib
from typing import Optional
import pytest
import bender


# @pytest.fixture
def solver_fixture() -> bender.VGBendingSolver:
    """ Fixture to generate solver for the following test cases

    Returns:
        bender.VGBendingSolver: the test solver
    """
    solver = bender.VGBendingSolver()

    with open("tests/test_modell.plist", "rb") as fp:
        plist = plistlib.load(fp)
        solver.parse_material_data(plist)

    return solver


@pytest.mark.parametrize("position,neutral_axis,diameter,expectation",
                         [(100, 60, 60, 0.00133),
                          (20, 60, 60, -0.00133),
                          (60, 60, 60, 0.0)])
def test_strain(position, neutral_axis, diameter, expectation):
    """ Tests correctness of the _strain function

    Args:
        position (float): _description_
        neutral_axis (float): _description_
        diameter (float): _description_
        expectation (float): expectation value
    """
    solver = solver_fixture()  # TODO replace by fixture later
    assert solver._strain(position, neutral_axis,
                          diameter) == pytest.approx(expectation, rel=6e-4)


@pytest.mark.parametrize("strain,material_name,expectation",
                         [(0.001, "Hastelloy", 190e6),
                          (-0.001, "Hastelloy", -190e6),
                          (0, "Hastelloy", 0.0e6)])
def test_stress(strain, material_name, expectation):
    """_summary_

    Args:
        strain (_type_): _description_
        material_name (_type_): _description_
        expectation (_type_): _description_
    """
    solver = solver_fixture()  # TODO replace by fixture later
    material: Optional[bender.VGBendingMaterialData] = None
    if solver._modell is not None:
        for data in solver._modell:
            if data.name == material_name:
                material = data
                break
    if material is not None:
        assert solver._stress(strain, material) == pytest.approx(expectation,
                                                                 rel=6e-4)


@pytest.mark.parametrize("diameter,expectation", [(100, 60.0), (60, 60.0),
                                                  (2, 60.0)])
def test_position_of_neutral_axis(diameter, expectation):
    """_summary_

    Args:
        diameter (_type_): _description_
        expectation (_type_): _description_
    """
    solver = solver_fixture()  # TODO replace by fixture later
    assert solver._position_of_neutral_axis(
        diameter, solver._modell) == pytest.approx(expectation, rel=6e-4)
