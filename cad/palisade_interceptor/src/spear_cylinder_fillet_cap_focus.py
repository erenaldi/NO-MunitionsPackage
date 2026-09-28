"""Isolated cap to inspect the aft-edge fillet and one detailed nozzle."""
from cadgen import step
from spear_cylinder_cap_shapes import make_cylindrical_cap_preview

@step(out="../STEP/Spear_CylinderFillet_Cap_Focus.step")
def spear_cylinder_fillet_cap_focus():
    return make_cylindrical_cap_preview(cap_only=True)

if __name__ == "__main__":
    spear_cylinder_fillet_cap_focus()
