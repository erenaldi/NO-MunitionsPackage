"""First Kris-quality surface-detail prototype: one recessed service cover."""
from copy import deepcopy
from cadgen import build123d as bd
from study_shapes import tag, SEPARATION
from halberd_r12_shapes import MAIN_LABEL, MATERIALS as BASE_MATERIALS

PANEL_X=-320.
DETAIL_LABELS=("main_service_cover_1","main_service_border_1",
               "main_service_fastener_1","main_service_fastener_2")
MATERIALS=deepcopy(BASE_MATERIALS)
MATERIALS["definitions"].update({
    "detail_paint":{"name":"Service cover paint","roughness":.65,"metalness":.15},
    "detail_border":{"name":"Recessed joint","roughness":.9,"metalness":.05},
    "detail_metal":{"name":"Small metallic hardware","roughness":.38,"metalness":.65},
})
MATERIALS["assignments"].extend([
    {"targets":["#main_service_cover_1"],"material":"detail_paint"},
    {"targets":["#main_service_border_1"],"material":"detail_border"},
    {"targets":["#main_service_fastener_1","#main_service_fastener_2"],"material":"detail_metal"},
])


def profile(width,height,radius,z):
    return bd.RectangleRounded(width,height,radius).translate((PANEL_X,0,z))


def pocket():
    return bd.extrude(profile(124.,30.,3.4,98.8),amount=2.)


def panel_parts():
    # Positive, closed solids with a real shallow seat and a restrained edge bevel.
    cover=bd.loft([profile(120.,26.,3.,98.65),profile(120.,26.,3.,99.5),
                   profile(119.3,25.3,2.65,99.85)],ruled=True)
    border=bd.extrude(profile(124.,30.,3.4,98.65),amount=.45)
    border-=bd.extrude(profile(120.,26.,3.,98.5),amount=1.)
    heads=[]
    for i,x in enumerate((PANEL_X-48.,PANEL_X+48.),1):
        stem=bd.Cylinder(1.3,.65,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((x,0,98.5))
        head=bd.Cone(1.3,1.78,.55,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((x,0,99.1))
        screw=stem+head
        slot=bd.Box(.5,2.5,.5).translate((x,0,99.65))
        screw-=slot
        bore=bd.Cylinder(1.36,1.5,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((x,0,98.5))
        sink=bd.Cone(1.36,2.12,.75,align=(bd.Align.CENTER,bd.Align.CENTER,bd.Align.MIN)).translate((x,0,99.1))
        cover=cover-bore-sink
        heads.append(tag(screw,f"main_service_fastener_{i}","#87939B"))
    return [tag(cover,"main_service_cover_1"),tag(border,"main_service_border_1","#505960"),*heads]


def detail(model,separated=False):
    parts=[]
    for p in model.children:
        if p.label==MAIN_LABEL:
            p=tag(p-pocket(),MAIN_LABEL)
        parts.append(p)
    parts.extend(panel_parts())
    if separated:
        parts=[p.moved(bd.Location((-SEPARATION,0,0)))
               if p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=parts,label="Halberd_R13_Service_Panel_Prototype"+
                       ("_Separated" if separated else ""))


def focus(model):
    clip=bd.Box(220.,180.,70.).translate((PANEL_X,0,115.))
    parts=[]
    for p in model.children:
        if p.label not in (MAIN_LABEL,*DETAIL_LABELS):
            continue
        shape=p & clip
        shape.label=p.label
        shape.color=p.color
        parts.append(shape)
    return bd.Compound(children=parts,label="Halberd_R13_Service_Panel_Focus")


FOCUS_MATERIALS={"definitions":MATERIALS["definitions"],"assignments":MATERIALS["assignments"][-3:]}
