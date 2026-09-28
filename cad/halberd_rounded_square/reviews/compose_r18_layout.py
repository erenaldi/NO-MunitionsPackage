"""Annotated surface-composition proposal, not detailed CAD or a machining drawing.

Colored outlines are projected onto the saved planning base. Fastener symbols
and interface callouts show design intent; no new pocket/hardware is exported.
"""
import json
import math
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFont
from cadgen import build123d as bd, read_scene

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reviews"
TEAL = "#087F8C"
AMBER = "#B66A21"
INK = "#24394A"
QUIET = "#697D69"
BG = "#EDF2F7"
FONT = "C:/Windows/Fonts/arial.ttf"


def font(size):
    return ImageFont.truetype(FONT, size)


def circle(radius, count=64, keyed=False):
    points = [(radius * math.cos(i * 2 * math.pi / count),
               radius * math.sin(i * 2 * math.pi / count)) for i in range(count)]
    return [(min(x, radius * .65), y) for x, y in points] if keyed else points


def d_door():
    arc = [(-45 + 20 * math.cos(math.pi / 2 + i * math.pi / 24),
            20 * math.sin(math.pi / 2 + i * math.pi / 24)) for i in range(25)]
    return [(65, -20), (65, 20), *arc]


# These are individual layouts, not a station list to be copied around the body.
FEATURES = [
    dict(id="F02", name="Tapered shoulder hatch", face="upper", clock=0,
         x=900., tangent=0.,
         outline=[(-70,-16),(-62,-22),(60,-14),(70,-6),(70,6),(60,14),(-62,22),(-70,16)],
         screws=[(-55,-13),(-55,13),(52,-7),(52,7)],
         label=(700,105), note="One cover following the shoulder taper; four corner heads."),
    dict(id="F04A", name="Clipped forward access door", face="lateral_positive", clock=90,
         x=440., tangent=0.,
         outline=[(-90,-22),(62,-22),(90,-4),(90,12),(80,22),(-90,22)],
         screws=[(-76,-13),(-76,13),(-12,-13),(-12,13),(64,-9),(70,11)],
         label=(990,110), note="Broad asymmetric outline near the forward intake/service region."),
    dict(id="F04B", name="Rounded-end aft access door", face="lateral_positive", clock=90,
         x=-790., tangent=0., outline=d_door(),
         screws=[(-43,-10),(-43,10),(49,-11),(49,11)],
         label=(1810,455), note="A separate aft access region; rounded end and four-head layout."),
    dict(id="F05", name="Longitudinal service cover", face="lower", clock=180,
         x=140., tangent=14.,
         outline=[(-250,-5),(-242,-8),(226,-8),(250,-3),(250,3),(226,8),(-242,8),(-250,5)],
         screws=[(-231,0),(219,0)],
         lines=[[(-237,-8),(-237,8)],[(225,-8),(237,5)]],
         label=(1120,100), note="One narrow lower-face assembly with distinct terminal pieces."),
    dict(id="F03A", name="Round inspection cap", face="lateral_negative", clock=270,
         x=590., tangent=-5., outline=circle(18), inner=circle(15.5),
         screws=[(-9,0),(9,0)], label=(965,120),
         note="Forward circular cap with a fine retaining lip and paired heads."),
    dict(id="F03B", name="Keyed aft cap", face="lateral_negative", clock=270,
         x=-1390., tangent=0., outline=circle(12, keyed=True),
         screws=[], lines=[[(-6,0),(5,0)]], label=(2280,450),
         note="Small keyed outline with a central slot; no copy of the forward cap."),
    dict(id="F10", name="Booster service hatch", face="upper", clock=0,
         x=-1450., tangent=0.,
         outline=[(-48,-16),(34,-16),(48,-6),(48,10),(26,18),(-40,18),(-48,10)],
         screws=[(-34,-8),(-34,9),(33,1)], label=(2300,465),
         note="One offset-ended booster hatch with three local fastener sites."),
]
FACES = [
    ("upper", "UPPER / +Z", "One shoulder hatch and one distinct booster hatch"),
    ("lateral_positive", "LATERAL / +Y", "Two different access doors, separated by quiet body skin"),
    ("lower", "LOWER / -Z", "One longitudinal assembly; no repeated door row"),
    ("lateral_negative", "OPPOSITE LATERAL / -Y", "Round forward cap and keyed aft cap; broad empty spans"),
]


def foreground_bounds(image):
    image = image.convert("RGB")
    difference = ImageChops.difference(image, Image.new("RGB", image.size, image.getpixel((0,0))))
    mask = difference.convert("L").point(lambda value: 255 if value > 18 else 0)
    bounds = mask.getbbox()
    if bounds is None or bounds[2] - bounds[0] < image.width * .5:
        raise ValueError("Could not calibrate the CAD silhouette in the raw image")
    return bounds


def outline(draw, points, color=TEAL, width=3):
    points = [(round(x), round(y)) for x,y in points]
    draw.line(points + [points[0]], fill=color, width=width, joint="curve")


def draw_feature(draw, feature, project, screw_radius):
    outline(draw, [project(x,y) for x,y in feature["outline"]])
    if "inner" in feature:
        outline(draw, [project(x,y) for x,y in feature["inner"]], width=2)
    for line in feature.get("lines", []):
        draw.line([project(x,y) for x,y in line], fill=TEAL, width=3)
    for x,y in feature["screws"]:
        px,py = project(x,y)
        r = screw_radius
        draw.ellipse((px-r,py-r,px+r,py+r), outline=TEAL, width=2)
        draw.line((px-r*.65,py,px+r*.65,py), fill=TEAL, width=1)


def callout(draw, anchor, position, text, color=TEAL):
    x,y = position
    f = font(27)
    box = draw.textbbox((0,0), text, font=f)
    width = box[2] - box[0]
    x = min(max(x,20), 2780-width)
    endpoint = (x + min(45,width/2), y+34 if y < anchor[1] else y-7)
    draw.line((anchor, endpoint), fill=color, width=2)
    draw.ellipse((anchor[0]-4,anchor[1]-4,anchor[0]+4,anchor[1]+4), fill=color)
    draw.rounded_rectangle((x-7,y-5,x+width+7,y+34), radius=5, fill=BG)
    draw.text((x,y), text, font=f, fill=color)


def draw_flat(face, title, subtitle):
    image = Image.open(OUT / f"R18_base_{face}.png").convert("RGB")
    bounds = foreground_bounds(image)
    scale = (bounds[2]-bounds[0]-1) / 3370.
    center_y = (bounds[1]+bounds[3]-1)/2
    project = lambda x,t: (bounds[0] + (1685.-x)*scale, center_y+t*scale)
    draw = ImageDraw.Draw(image)
    draw.text((28,18), title, font=font(35), fill=INK)
    draw.text((650,25), subtitle, font=font(27), fill=INK)
    for feature in FEATURES:
        if feature["face"] != face:
            continue
        convert = lambda x,y: project(feature["x"]+x, feature["tangent"]+y)
        draw_feature(draw, feature, convert, max(2.,1.5*scale))
        ax,at=feature["outline"][0]
        callout(draw, project(feature["x"]+ax,feature["tangent"]+at), feature["label"],
                f'{feature["id"]}  {feature["name"]}')
    # One coherent stage joint is drawn at its real boundary, not repeated ticks.
    draw.line([project(-3370/3,-28), project(-3370/3,28)], fill=AMBER, width=3)
    callout(draw, project(-3370/3,28), (2070,550), "F09  stage interface", AMBER)
    quiet_end = -260. if face == "lower" else 100.
    q0, q1 = project(quiet_end,0)[0], project(-620,0)[0]
    y = 515
    draw.line((q0,y,q1,y), fill=QUIET, width=3)
    draw.line((q0,y-7,q0,y+7), fill=QUIET, width=2)
    draw.line((q1,y-7,q1,y+7), fill=QUIET, width=2)
    draw.text(((q0+q1)/2-80,y+14), "QUIET SKIN", font=font(25), fill=QUIET)
    if face == "upper":
        callout(draw, project(1085,-40), (400,110), "F01  retained nose joint", AMBER)
        # Marks reference that actual joint; they are not a repeating motif.
        for x in (1075.,1067.):
            draw.line([project(x,24),project(x,30)], fill=AMBER, width=2)
        draw.text((480,460), "F12  small joint index marks", font=font(25), fill=AMBER)
    image.save(OUT / f"R18_layout_{face}.png")
    return image, dict(image=f"R18_base_{face}.png", foreground_bbox_px=list(bounds),
                       pixels_per_mm=scale, transverse_origin_px=center_y)


def sampled_projection_bounds(parts, right, up):
    projected = []
    for shape in parts.values():
        for edge in shape.edges():
            for index in range(33):
                point = edge.position_at(index/32.)
                projected.append((point.dot(right), point.dot(up)))
    return (min(p[0] for p in projected), max(p[0] for p in projected),
            min(p[1] for p in projected), max(p[1] for p in projected))


def compose_whole(parts):
    raw = Image.open(OUT / "R18_base_whole.png").convert("RGB")
    image = Image.new("RGB", (raw.width, raw.height+200), BG)
    image.paste(raw, (0,120))
    draw = ImageDraw.Draw(image)
    draw.text((28,18), "VISIBLE-FACE COMPOSITION / UPPER +Z AND LATERAL +Y", font=font(32), fill=INK)
    direction = bd.Vector(.35,1.,.65).normalized()
    right = bd.Vector(0,0,1).cross(direction).normalized()
    up = direction.cross(right).normalized()
    u0,u1,v0,v1 = sampled_projection_bounds(parts, right, up)
    left,top,right_px,bottom = foreground_bounds(Image.open(OUT / "R18_base_whole.png"))
    scale = (right_px-left-1)/(u1-u0)
    project_world = lambda point: (left + (bd.Vector(point).dot(right)-u0)*scale,
                                  top + 120 + (v1-bd.Vector(point).dot(up))*scale)

    def on_skin(feature, x, t):
        host = parts["booster_body" if feature["x"] < -3370/3 else "main_body_intake_r12"].solids()[0]
        angle = math.radians(feature["clock"])
        point = lambda radius: bd.Vector(x, t*math.cos(angle)+radius*math.sin(angle),
                                          -t*math.sin(angle)+radius*math.cos(angle))
        low,high = 0.,160.
        if not host.is_inside(point(low)):
            raise ValueError(f"No skin at proposed feature {feature['id']}")
        for _ in range(32):
            middle=(low+high)/2
            if host.is_inside(point(middle)):
                low=middle
            else:
                high=middle
        return point((low+high)/2)

    for feature in FEATURES:
        if feature["face"] not in ("upper","lateral_positive"):
            continue
        convert=lambda x,y: project_world(on_skin(feature,feature["x"]+x,feature["tangent"]+y))
        draw_feature(draw,feature,convert,max(2.,scale*1.5))
        anchor=convert(0,0)
        draw.text((anchor[0]+14,anchor[1]-30),feature["id"],font=font(24),fill=TEAL)
    # Interface anchors only: their actual conformal paths await the local fit gate.
    anchors = [
        ("F06  intake edge joints", (430,72,115), (1050,100)),
        ("F07  paired root seats", (-975,102,102), (1760,65)),
        ("F08  shaped booster collars", (-1351,96,96), (2220,90)),
        ("F09  true stage boundary", (-3370/3,100,0), (2050,620)),
        ("F11  retained nozzle rims", (-1685,0,0), (2380,690)),
    ]
    for text,point,position in anchors:
        callout(draw,project_world(point),position,text,AMBER)
    draw.text((30,760), "Amber leaders identify interface regions; they are not modeled cuts or fittings.",
              font=font(26),fill=AMBER)
    image.save(OUT / "R18_layout_whole.png")
    return image, dict(projected_bounds_mm=[u0,u1,v0,v1],pixels_per_mm=scale,
                       basis_right=list(right),basis_up=list(up))


def feature_sheet():
    cw,ch = 1300,550
    rows=(len(FEATURES)+1)//2
    image=Image.new("RGB",(cw*2,rows*ch+150),BG)
    draw=ImageDraw.Draw(image)
    draw.text((25,22),"SEVEN INDIVIDUAL ACCESS FEATURES / OUTLINE STUDIES",font=font(38),fill=INK)
    draw.text((25,82),"Fit-to-cell views. These are proposed shapes and hardware layouts, not finished CAD.",font=font(27),fill=INK)
    for index,feature in enumerate(FEATURES):
        ox=(index%2)*cw; oy=150+(index//2)*ch
        draw.text((ox+30,oy+15),f'{feature["id"]}  {feature["name"]}',font=font(31),fill=TEAL)
        xs=[p[0] for p in feature["outline"]]; ys=[p[1] for p in feature["outline"]]
        scale=min(9.,(cw-170)/(max(xs)-min(xs)),250/(max(ys)-min(ys)))
        project=lambda x,y:(ox+cw/2-x*scale,oy+245+y*scale)
        draw_feature(draw,feature,project,max(3.,1.5*scale))
        text=feature["note"]
        words=text.split(); lines=[""]
        for word in words:
            if len(lines[-1])+len(word)>75:
                lines.append("")
            lines[-1]+=(" " if lines[-1] else "")+word
        draw.multiline_text((ox+35,oy+415),"\n".join(lines),font=font(25),fill=INK,spacing=8)
    image.save(OUT / "R18_Feature_Designs.png")


if __name__ == "__main__":
    scene=read_scene(ROOT / "STEP" / "halberd_r18_layout_base.step")
    parts={leaf.label:scene.resolve(leaf.ref).shape() for leaf in scene.leaves()}
    assert len(parts)==28 and len({feature["id"] for feature in FEATURES})==7
    images=[]; calibrations={}
    for face,title,subtitle in FACES:
        image,calibration=draw_flat(face,title,subtitle)
        images.append(image); calibrations[face]=calibration
    whole,calibration=compose_whole(parts)
    images.append(whole); calibrations["whole"]=calibration
    board=Image.new("RGB",(2800,150+sum(image.height for image in images)+130),BG)
    draw=ImageDraw.Draw(board)
    draw.text((30,18),"HALBERD R18 / SURFACE-COMPOSITION PROPOSAL",font=font(43),fill=INK)
    draw.text((30,78),"Teal: individual access designs     Amber: assembly-related interfaces     Green: intentional quiet skin",
              font=font(28),fill=INK)
    y=150
    for image in images:
        board.paste(image,(0,y))
        y+=image.height
    draw.text((30,board.height-95),"PLANNING OVERLAY: proposed footprints and placement intent; dimensions, pockets and attachments need the next local CAD gate.",
              font=font(26),fill=INK)
    board.save(OUT / "R18_Surface_Layout.png")
    feature_sheet()
    manifest=dict(state="concept-review",base_document_hash=scene.document_hash,
                  units="mm",note="2D surface proposal; no feature geometry exported",
                  individual_access_features=FEATURES,calibrations=calibrations)
    (OUT / "R18_layout_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    print("Wrote four face maps, whole composition, seven-feature sheet and hash-bound layout manifest.")
