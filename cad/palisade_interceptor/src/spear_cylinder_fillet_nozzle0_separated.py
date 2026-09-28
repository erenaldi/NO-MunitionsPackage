"""Translated cap review with unchanged full Spear geometry."""
from cadgen import step
from spear_cylinder_cap_shapes import make_cylindrical_cap_preview

@step(out="../STEP/Spear_CylinderFillet_Nozzle0_Separated.step")
def spear_cylinder_fillet_nozzle0_separated():
    return make_cylindrical_cap_preview(separated=True)

if __name__ == "__main__":
    spear_cylinder_fillet_nozzle0_separated()
