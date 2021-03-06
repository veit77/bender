"""_summary_
"""
from typing import Optional, Any
from dataclasses import dataclass
from multiprocessing import Pool
import plistlib


@dataclass
class VGBendingMaterialData:
    """_summary_
    """
    name: str
    is_superconductor: bool
    thickness: float
    youngs1: float
    youngs2: float
    youngs3: float
    sigma1: float
    sigma2: float
    critical_tensil_strain: float


@dataclass
class CriticalConditions:
    """_summary_
    """
    pos: float
    material: VGBendingMaterialData


class VGBendingSolver:
    """_summary_
    """
    _modell: Optional[list[VGBendingMaterialData]] = None

    @property
    def _total_thickness(self) -> float:
        thickness = 0.0
        if (materials := self._modell) is not None:
            for material in materials:
                thickness += material.thickness
        return thickness

    min_bending_diameter_d: Optional[float] = None
    min_bending_diameter_u: Optional[float] = None

    @property
    def min_double_bending_diameter(self):
        bending_dia_down = 0.0
        bending_dia_up = 0.0

        if self.min_bending_diameter_d is not None:
            bending_dia_down = self.min_bending_diameter_d

        if self.min_bending_diameter_u is not None:
            bending_dia_up = self.min_bending_diameter_u

        return max(bending_dia_down, bending_dia_up)

    def solve(self) -> None:
        """ Starts the calculation of the critical bending diameter
        """
        if self._modell is None:
            print("No modell loaded")
            return

        with Pool(2) as pool:
            values = [self._modell, self._modell[::-1]]
            result = pool.map(self._min_bending_diameter, values)

            self.min_bending_diameter_u = result[0]

            self.min_bending_diameter_d = result[1]

    def parse_material_data(self, data: dict[str, Any]) -> None:
        """ Assigns the material data from the plist to the internal data structure

        Args:
            data (dict[str, Any]): dictionary containing material data from the plist
        """
        self._modell = []
        for material in data["Layers"]:
            parameters = VGBendingMaterialData(
                name=material["name"],
                is_superconductor=material["isSuperconductor"],
                thickness=material["thickness"],
                youngs1=material["E1"],
                youngs2=material["E2"],
                youngs3=material["E3"],
                sigma1=material["sigma1"],
                sigma2=material["sigma2"],
                critical_tensil_strain=material["criticalTensilStrain"],
            )
            self._modell.append(parameters)

    def _min_bending_diameter(
            self, modell: list[VGBendingMaterialData]) -> Optional[float]:

        bending_diameter: Optional[float] = None

        superconductors: list[CriticalConditions] = []
        pos_value: float = 0.0

        for material in modell:
            if not material.is_superconductor:
                pos_value += material.thickness
            else:
                superconductor = CriticalConditions(pos=pos_value,
                                                    material=material)
                superconductors.append(superconductor)

        for diameter in range(300, 0, -1):
            if bending_diameter is None:
                neutral_axis = self._position_of_neutral_axis(
                    diameter=float(diameter), modell=modell)
                print(f"{diameter} mm: Neutral Axis is at y= {neutral_axis}")

                for superconductor in superconductors:
                    epsilon = self._strain(superconductor.pos, neutral_axis,
                                           float(diameter))
                    if (epsilon > 0 and epsilon >
                            superconductor.material.critical_tensil_strain):
                        print(f"Minimum Bending Diameter is {diameter} mm")
                        bending_diameter = float(diameter)
        return bending_diameter

    def _position_of_neutral_axis(
            self, diameter: float,
            modell: list[VGBendingMaterialData]) -> float:
        max_value = int(self._total_thickness)
        forces: list[float] = [
            abs(self._force(diameter, float(value), modell))
            for value in range(max_value)
        ]

        return float(forces.index(min(forces)))

    def _force(self, diameter: float, neutral_axis: float,
               modell: list[VGBendingMaterialData]) -> float:
        max_value = int(self._total_thickness)
        force = 0.0
        width = 12e-3

        for pos in range(max_value):
            epsilon = self._strain(float(pos), neutral_axis, diameter)
            max_pos = 0.0

            for material in modell:
                max_pos += material.thickness
                if float(pos) < max_pos:
                    force += self._stress(epsilon, material) * 1e-6 * width
                    break

        return force

    def _strain(self, pos: float, neutral_axis: float,
                diameter: float) -> float:
        return (pos - neutral_axis) * 1e-6 / (diameter / 2 * 1e-3 +
                                              neutral_axis * 1e-6)

    def _stress(self, strain: float, material: VGBendingMaterialData) -> float:
        max_strain1 = material.sigma1 / material.youngs1
        max_strain2 = max_strain1 + (material.sigma2 -
                                     material.sigma1) / material.youngs2

        if strain >= 0:
            if strain > max_strain2:
                return material.sigma2 + (strain -
                                          max_strain2) * material.youngs3
            elif strain > max_strain1:
                return material.sigma1 + (strain -
                                          max_strain1) * material.youngs2
            else:
                return strain * material.youngs1
        else:
            if strain > -max_strain1:
                return strain * material.youngs1
            else:
                return -material.sigma1 + (strain +
                                           max_strain1) * material.youngs3


if __name__ == "__main__":
    solver = VGBendingSolver()

    print("Loading Modell...")

    with open("modell.plist", "rb") as fp:
        plist = plistlib.load(fp)
        solver.parse_material_data(plist)

    print("Modell loaded.")

    print("\nCalculating...")
    solver.solve()

    print(f"Minimum Bending Diameter Downward is: "
          f"{solver.min_bending_diameter_d}")

    print(f"Minimum Bending Diameter Upwards is: "
          f"{solver.min_bending_diameter_u}")

    print(f"\nMinimum Double Bending Diameter is: "
          f"{solver.min_double_bending_diameter}")
