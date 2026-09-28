"""Five broad exterior game-asset studies branching from Shoulder.

Matched constant sections at each stage joint give identical outline AND tangent.
No production model, runtime component, or aerodynamic simulation is imported.
"""
import math
from cadgen import build123d as bd, srgb
from halberd_concept_shapes import tagged, disk, barrel, fin, clock, visual_nozzle

VARIANTS = {
    "B1_Needle": dict(length=3600, width=170, height=170, corner=47, nose=740,
                      inlet_x=690, inlet_length=630, inlet_width=28, inlet_depth=10,
                      fin_span=174, fin_chord=230, booster_span=184, booster_chord=310,
                      sweep=80, angular=False, soft=False, mounts=2),
    "B2_Broadhead": dict(length=3000, width=250, height=250, corner=65, nose=400,
                         inlet_x=650, inlet_length=270, inlet_width=65, inlet_depth=23,
                         fin_span=260, fin_chord=430, booster_span=270, booster_chord=580,
                         sweep=20, angular=False, soft=False, mounts=1),
    "B3_Chisel": dict(length=3360, width=208, height=208, corner=12, nose=570,
                      inlet_x=720, inlet_length=390, inlet_width=44, inlet_depth=16,
                      fin_span=220, fin_chord=360, booster_span=233, booster_chord=450,
                      sweep=-30, angular=True, soft=False, mounts=2),
    "B4_Manta": dict(length=3200, width=320, height=144, corner=36, nose=590,
                     inlet_x=610, inlet_length=460, inlet_width=52, inlet_depth=13,
                     fin_span=292, fin_chord=450, booster_span=305, booster_chord=560,
                     sweep=140, angular=True, soft=False, mounts=1),
    "B5_Sculpted": dict(length=3500, width=226, height=226, corner=85, nose=650,
                        inlet_x=700, inlet_length=430, inlet_width=54, inlet_depth=24,
                        fin_span=223, fin_chord=330, booster_span=242, booster_chord=430,
                        sweep=110, angular=False, soft=True, mounts=2),
}


def section(x, w, h, corner):
    # Rotate XY -> YZ: original rectangle width maps to Z, height maps to Y.
    return bd.RectangleRounded(h, w, corner).rotate(bd.Axis.Y, 90).translate((x, 0, 0))


def rect_hull(stations, config, smooth=False):
    return bd.loft([section(x, config["width"]*scale, config["height"]*scale,
                            config["corner"]*scale) for x, scale in stations], ruled=not smooth)


def inlet_cut(config, index):
    """A real recessed shoulder opening; parameters control appearance only."""
    sy, sz = ((1,1), (1,-1), (-1,-1), (-1,1))[index]
    c = config["corner"]
    y = sy*(config["width"]/2-c+c/math.sqrt(2))
    z = sz*(config["height"]/2-c+c/math.sqrt(2))
    angle = math.degrees(math.atan2(sy, sz))
    a = config["inlet_x"]-config["inlet_length"]
    b = config["inlet_x"]
    half_width, depth = config["inlet_width"]/2, config["inlet_depth"]
    profiles = []
    for x, width_factor, radial in ((a, .45, -depth*.35), (a+(b-a)*.35, 1, -depth*.1), (b, .75, depth*.2)):
        if config["angular"]:
            face = bd.RectangleRounded(depth*2, half_width*2*width_factor, 2)
        else:
            face = bd.Ellipse(depth, half_width*width_factor)
        face = face.rotate(bd.Axis.Y,90).translate((x,0,radial))
        profiles.append(face)
    cutter = bd.loft(profiles, ruled=not config["soft"])
    return clock(cutter, angle).translate((0,y,z))


def build_variant(key):
    cfg = VARIANTS[key]
    half = cfg["length"]/2
    seam = -cfg["length"]*.1
    nose_base = half-cfg["nose"]
    shoulder_end = max(cfg["inlet_x"]+35, nose_base-160)
    # Constant body through the joint; the taper starts well away from separation.
    body = rect_hull([(seam,1), (shoulder_end,1), (nose_base,.78)], cfg)
    for i in range(4):
        body -= inlet_cut(cfg, i)
    recess_radius = min(cfg["width"],cfg["height"])*.31
    body -= barrel(seam-1,seam+70,recess_radius)
    parts = [tagged(body, "sustainer_body")]
    nose = rect_hull([(nose_base,.78), (nose_base+cfg["nose"]*.38,.65),
                      (nose_base+cfg["nose"]*.78,.28), (half,.006)],cfg,smooth=cfg["soft"])
    parts.append(tagged(nose,"radome",srgb("#D1D4D1")))
    parts.append(tagged(visual_nozzle(seam,70,recess_radius),"sustainer_nozzle",srgb("#626C70")))
    # Same exact section for at least 180 mm on the booster side, no round waist.
    aft_scale = .80 if key!="B4_Manta" else .88
    booster = rect_hull([(-half,aft_scale), (-half+240,1), (seam,1)],cfg)
    booster -= barrel(-half-1,-half+75,recess_radius*.82)
    # Recessed front closure is interior to the common outer outline.
    booster -= bd.loft([disk(seam-10,recess_radius*.68), disk(seam+1,recess_radius*.8)],ruled=True)
    parts.append(tagged(booster,"booster_body"))
    parts.append(tagged(visual_nozzle(-half,75,recess_radius*.82),"booster_nozzle",srgb("#626C70")))
    root = min(cfg["width"],cfg["height"])*.52
    for i,angle in enumerate((45,135,225,315),1):
        # Manta spreads the four blades nearly horizontally, preserving upper/lower pairs.
        if key=="B4_Manta":
            angle = (70,110,250,290)[i-1]
            root = 118
        aft = seam+95
        tip_aft = aft+cfg["sweep"]
        blade = fin(aft,aft+cfg["fin_chord"],tip_aft,tip_aft+cfg["fin_chord"]*.40,
                    cfg["fin_span"],root,11)
        parts.append(tagged(clock(blade,angle),f"sustainer_fin_{i}",srgb("#626C70")))
        aft = -half+110
        tip_aft = aft+cfg["sweep"]*.65
        blade = fin(aft,aft+cfg["booster_chord"],tip_aft,tip_aft+cfg["booster_chord"]*.42,
                    cfg["booster_span"],root,13)
        parts.append(tagged(clock(blade,angle),f"booster_fin_{i}",srgb("#626C70")))
    stations = (210,) if cfg["mounts"]==1 else (0,480)
    for i,x in enumerate(stations,1):
        long = 220 if cfg["mounts"]==1 else 62
        width = 48 if cfg["mounts"]==1 else 25
        shoe = bd.Box(long,width,10).translate((x,0,cfg["height"]/2+3))
        parts.append(tagged(shoe,f"mount_{i}",srgb("#626C70")))
    return bd.Compound(children=parts,label=key)
