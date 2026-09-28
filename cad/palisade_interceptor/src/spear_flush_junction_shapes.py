"""Fix only the first 22 mm of Spear body and mate it to the plain cap."""

from cadgen import build123d as bd

from concept_shapes import SEPARATION, STUDIES, body
from spear_cylinder_cap_shapes import cylindrical_cap, make_cylindrical_cap_preview


FLUSH_RADIUS = STUDIES["A"]["radius"]


def make_flush_junction(separated=False, cap_only=False):
    source = make_cylindrical_cap_preview()
    revised_body = body(dict(STUDIES["A"], aft_radius_ratio=1.))
    revised_cap = cylindrical_cap(radius=FLUSH_RADIUS)
    parts = [revised_body if item.label == "body" else
             revised_cap if item.label == "turning_cap" else item
             for item in source.children]
    if cap_only:
        parts = [item for item in parts
                 if item.label == "turning_cap" or item.label.startswith("thruster_")]
    elif separated:
        parts = [item.moved(bd.Location((-SEPARATION, 0, 0)))
                 if item.label == "turning_cap" or item.label.startswith("thruster_")
                 else item for item in parts]
    suffix = "_Cap_Focus" if cap_only else ("_Separated" if separated else "")
    return bd.Compound(children=parts, label=f"Spear_FlushJunction_Cap{suffix}")
