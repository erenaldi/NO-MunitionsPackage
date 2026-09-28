"""R5 idealized engineering lines and rear-face-only occlusion material."""
from cadgen import build123d as bd, srgb
from study_shapes import body, tag, rotate, SEAM, SEPARATION
from intake_r3_shapes import outer_profile, passage, CLOCK, CORNER_RADIUS, MOUTH_FOOT_X, ENTRY_SWEEP
from intake_r4_shapes import build_r4, extended_passage, housing_extension

TAPER_START=210.
FRONT_END=715.
# Roof and shoulder endpoints define straight lines, not fitted sketch traces.
END_WIDTH=8.
START_WIDTH=88.
END_ROOF_HALF=1.6
START_ROOF_HALF=16.
END_ROOF=136.
START_ROOF=147.5
FRONT_ROOF=145.


def straight_outer():
    shape=bd.loft([
        outer_profile(SEAM,END_WIDTH,END_ROOF_HALF,END_ROOF),
        outer_profile(TAPER_START,START_WIDTH,START_ROOF_HALF,START_ROOF),
        outer_profile(FRONT_END,START_WIDTH,START_ROOF_HALF,FRONT_ROOF),
    ],ruled=True)
    def front_x(radial):
        return MOUTH_FOOT_X-ENTRY_SWEEP*(radial-CORNER_RADIUS)
    tool=bd.Face(bd.Wire.make_polygon([
        (front_x(75.),-120.,75.),(850.,-120.,75.),
        (850.,-120.,200.),(front_x(200.),-120.,200.),
    ],close=True))
    return shape-bd.extrude(tool,amount=240.,dir=(0,1,0))


def black_back(shape,label):
    shape.label=label
    shape.color=srgb("#000000")
    # Black metalness=1 removes dielectric glints from the occlusion proxy.
    # The surrounding real-looking matte walls keep their original material.
    shape.cad_material={"roughness":1.,"metalness":1.,"clearcoat":0.}
    return shape


def build_r5(separated=False):
    baseline=build_r4()
    previous={p.label:p for p in baseline.children}
    _,back=housing_extension(previous["main_body_intake_r4"])
    housing=rotate(straight_outer(),CLOCK)
    main=(body()+housing)-rotate(passage(),CLOCK)-rotate(extended_passage(back),CLOCK)
    parts=[tag(main,"main_body_intake_r5")]
    for label,part in previous.items():
        if label=="main_body_intake_r4":
            continue
        if label=="main_intake_dark_recess":
            # A geometric split isolates only the blind back, retaining exactly
            # the same cup walls, seat and clear channel depth.
            back_slab=bd.Box(6.,600.,600.).translate((back-3.,0,0))
            cap=part & back_slab
            lining=part-cap
            lining.label=label
            lining.color=part.color
            lining.cad_material=dict(part.cad_material)
            parts.extend([lining,black_back(cap,"main_intake_dark_floor")])
        elif label in ("main_nozzle_dark_floor","booster_nozzle_dark_floor"):
            parts.append(black_back(part,label))
        else:
            parts.append(part)
    placed=[p.moved(bd.Location((-SEPARATION,0,0))) if separated and p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=placed,label="Halberd_R5_Straight_Taper"+("_Separated" if separated else ""))
