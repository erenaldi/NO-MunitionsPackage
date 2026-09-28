"""Complete four-station CAD layout with 170 mm noseward booster-fin shift."""
from cadgen import build123d as bd
from study_shapes import body, tag, SEPARATION
from booster_fin_r7_shapes import build_r7

BOOSTER_FIN_SHIFT=170.
STATION_DELTAS=(0.,90.,180.,270.)
MATERIALS={
    "definitions":{
        "interior":{"name":"Matte interior","roughness":.90,"metalness":.08},
        "occlusion":{"name":"Black obscured back","roughness":1.,"metalness":1.,"clearcoat":0.},
    },
    "assignments":[
        {"targets":[f"#main_intake_dark_recess_{i}" for i in range(1,5)]+[
            "#main_nozzle_dark_recess","#booster_nozzle_dark_recess"],"material":"interior"},
        {"targets":[f"#main_intake_dark_floor_{i}" for i in range(1,5)]+[
            "#main_nozzle_dark_floor","#booster_nozzle_dark_floor"],"material":"occlusion"},
    ],
}


def copy_at(shape,delta,label,forward=0.):
    placed=shape.moved(bd.Location((forward,0,0))).rotate(bd.Axis.X,-delta)
    placed.label=label
    placed.color=shape.color
    return placed


def build_r8(separated=False):
    approved=build_r7()
    old={p.label:p for p in approved.children}
    core=body()
    one_body=old["main_body_intake_r6"]
    lost_core=core-one_body
    if lost_core and lost_core.volume>.01:
        raise ValueError("Approved intake cuts the original core; delta replication is unsafe")
    # The approved housing-only delta already contains the channel. Rotating
    # whole bodies would refill it with another copy of the core.
    housing=one_body-core
    if not housing or not housing.is_valid or housing.volume<=0:
        raise ValueError("Approved housing delta is invalid")
    main=one_body
    for delta in STATION_DELTAS[1:]:
        main=main+housing.rotate(bd.Axis.X,-delta)
    parts=[tag(main,"main_body_four_intakes_r8")]
    static=("main_ogive","booster_body","main_nozzle_dark_recess","main_nozzle_dark_floor",
            "booster_nozzle_dark_recess","booster_nozzle_dark_floor")
    parts.extend(old[name] for name in static)
    for i,delta in enumerate(STATION_DELTAS,1):
        parts.append(copy_at(old["main_fin_housing_r3"],delta,f"main_fin_{i}"))
        parts.append(copy_at(old["booster_fin_r7_prototype"],delta,f"booster_fin_{i}",BOOSTER_FIN_SHIFT))
        parts.append(copy_at(old["main_intake_dark_recess"],delta,f"main_intake_dark_recess_{i}"))
        parts.append(copy_at(old["main_intake_dark_floor"],delta,f"main_intake_dark_floor_{i}"))
    if len({p.label for p in parts})!=23:
        raise ValueError("Unexpected four-station label set")
    # The shared runtime upgraded to 0.6.6 during this task. Historical factories
    # use the retired dynamic finish attribute; preserve their colors and move
    # the same finishes to this model's supported named-material declaration.
    for part in parts:
        if "cad_material" in getattr(part,"__dict__",{}):
            delattr(part,"cad_material")
    placed=[p.moved(bd.Location((-SEPARATION,0,0))) if separated and p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=placed,label="Halberd_R8_Four_Stations"+("_Separated" if separated else ""))
