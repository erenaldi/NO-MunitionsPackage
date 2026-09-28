"""Approved R11 continuous intake and taller-fin geometry at all four stations."""
from cadgen import build123d as bd
from study_shapes import body, rotate, tag, SEPARATION
from halberd_r11_shapes import build_r11, END_ROOF_X, END_LEAN, MATERIALS
from halberd_r10_shapes import continuous_housing, split_housing, MAIN_LABEL as OLD_MAIN
from halberd_r8_shapes import copy_at

MAIN_LABEL="main_body_intake_r12"


def build_r12(separated=False):
    approved={p.label:p for p in build_r11().children}
    back=max(v.X for v in approved["main_intake_dark_floor_1"].vertices())
    main_piece,_=split_housing(continuous_housing(back,END_ROOF_X,END_LEAN))
    main=body()
    for angle in (45.,135.,225.,315.):
        main=main+rotate(main_piece,angle)
    parts=[tag(main,MAIN_LABEL)]
    parts.extend(p for label,p in approved.items()
                 if label!=OLD_MAIN and not label.startswith("booster_fin_")
                 and not label.startswith("booster_intake_fairing_"))
    for i,delta in enumerate((0.,90.,180.,270.),1):
        parts.append(copy_at(approved["booster_fin_1"],delta,f"booster_fin_{i}"))
        parts.append(copy_at(approved["booster_intake_fairing_1"],delta,f"booster_intake_fairing_{i}"))
    if len(parts)!=27:
        raise ValueError("Unexpected R12 part count")
    if separated:
        parts=[p.moved(bd.Location((-SEPARATION,0,0)))
               if p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=parts,label="Halberd_R12_Four_Approved_Stations"+
                       ("_Separated" if separated else ""))
