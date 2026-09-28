"""Lengthen the original intake first, then divide it at the stage seam."""
from cadgen import build123d as bd
from study_shapes import body, rotate, tag, SEAM, SEPARATION
from intake_r3_shapes import passage
from intake_r4_shapes import extended_passage
from intake_r6_shapes import curved_outer
from halberd_r8_shapes import build_r8, MATERIALS
from halberd_r9_shapes import taller_fin, MIDPOINT, CLOCK

MAIN_LABEL="main_body_intake_r10"
FAIRING_LABEL="booster_intake_fairing_1"


def continuous_housing(back,end_x=MIDPOINT,end_lean=0.):
    # The same original cubic width law and linear roof slope are evaluated
    # over the longer domain. There is no added transition or kink at SEAM.
    return curved_outer(end_x=end_x,end_lean=end_lean)-passage()-extended_passage(back)


def split_housing(housing):
    main_half=bd.Box(6000.,600.,600.).translate((SEAM+3000.,0,0))
    booster_half=bd.Box(6000.,600.,600.).translate((SEAM-3000.,0,0))
    return housing & main_half,housing & booster_half


def build_r10(separated=False,end_x=MIDPOINT,end_lean=0.):
    previous=build_r8()
    old={p.label:p for p in previous.children}
    back=max(v.X for v in old["main_intake_dark_floor_1"].vertices())
    long_housing=continuous_housing(back,end_x,end_lean)
    main_piece,aft_piece=split_housing(long_housing)
    main=body()+rotate(main_piece,CLOCK)
    other=curved_outer()-passage()-extended_passage(back)
    for angle in (135.,225.,315.):
        main=main+rotate(other,angle)
    parts=[tag(main,MAIN_LABEL),
           tag(rotate(aft_piece,CLOCK),FAIRING_LABEL),taller_fin()]
    parts.extend(p for p in previous.children
                 if p.label not in ("main_body_four_intakes_r8","booster_fin_1"))
    for part in parts:
        if not part.is_valid or len(part.solids())!=1 or part.volume<=0:
            raise ValueError(f"Invalid R10 part: {part.label}")
    if separated:
        parts=[p.moved(bd.Location((-SEPARATION,0,0)))
               if p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=parts,label="Halberd_R10_Continuous_Intake"+
                       ("_Separated" if separated else ""))


def focus(model):
    clip=bd.Box(720.,450.,450.).translate((-1240.,0,0))
    parts=[]
    for p in model.children:
        if p.label not in (MAIN_LABEL,"booster_body","booster_fin_1",FAIRING_LABEL):
            continue
        shape=p.rotate(bd.Axis.X,CLOCK) & clip
        shape.label=p.label
        shape.color=p.color
        parts.append(shape)
    return bd.Compound(children=parts,label="Halberd_R10_Continuous_Intake_Focus")
