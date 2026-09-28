"""Four-fin Spear with flush cylinder cap and one detailed lateral nozzle."""
from cadgen import step
from spear_cylinder_cap_shapes import make_cylindrical_cap_preview

@step(out="../STEP/Spear_CylinderFillet_Nozzle0.step")
def spear_cylinder_fillet_nozzle0():
    return make_cylindrical_cap_preview()

if __name__ == "__main__":
    spear_cylinder_fillet_nozzle0()
