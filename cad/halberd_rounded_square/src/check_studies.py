"""Independent exported-artifact checks; no import from geometry factories."""
import argparse
import json
import math
from pathlib import Path
from cadgen import build123d as bd, read_step

ROOT = Path(__file__).resolve().parents[1]
FILES = {"A": "A_Trace", "B": "B_Chine", "C": "C_Shoulder"}
# Brief-derived numerical limits; separate from the generating module.
SEAM = -3370/3
PROBES = {"A": (630, 100, 17, 0), "B": (725, math.sqrt(2)*30+70, 15, 45),
          "C": (495, 100, 19, 0)}


def close(a, b, tol=0.002):
    assert abs(a-b) < tol, (a, b)


def leaves(shape):
    if shape.children:
        return [leaf for child in shape.children for leaf in leaves(child)]
    return [shape]


def point(x, radius, angle):
    a = math.radians(angle)
    return (x, radius*math.sin(a), radius*math.cos(a))


def check(key):
    model = read_step(ROOT / "STEP" / (FILES[key]+".step"))
    sep = read_step(ROOT / "STEP" / (FILES[key]+"_Separated.step"))
    parts = {p.label: p for p in leaves(model)}
    moved = {p.label: p for p in leaves(sep)}
    expected = {"main_body", "main_ogive", "booster_body"} | {
        f"{prefix}_{i}" for prefix in ("main_intake", "main_fin", "booster_fin") for i in range(1,5)}
    assert set(parts) == set(moved) == expected
    assert len(leaves(model)) == len(parts) == 15
    b = model.bounding_box()
    close(b.min.X, -1685); close(b.max.X, 1685); close(b.size.X, 3370)
    for name, p in parts.items():
        assert p.is_valid and len(p.solids()) == 1 and p.volume > 0, name
        q = moved[name]
        assert q.is_valid and len(q.solids()) == 1 and q.volume > 0, name
        close(p.volume, q.volume, max(.01, p.volume*1e-8))
        delta = -340 if name.startswith("booster") else 0
        pb, qb = p.bounding_box(), q.bounding_box()
        for coord in ("min", "max"):
            for axis in ("X", "Y", "Z"):
                close(getattr(getattr(qb,coord),axis), getattr(getattr(pb,coord),axis)+(delta if axis=="X" else 0))
        if name.startswith("booster"):
            assert pb.max.X <= SEAM+.002, name
        else:
            assert pb.min.X >= SEAM-.002, name
    body, booster = parts["main_body"], parts["booster_body"]
    close(booster.bounding_box().size.X, 3370/6)
    close(body.bounding_box().min.X, SEAM)
    close(booster.bounding_box().max.X, SEAM)
    for p in (body, booster):
        close(p.bounding_box().size.Y, 200, .05)
        close(p.bounding_box().size.Z, 200, .05)
    # Compare actual cross-section areas at the two sides of the join.
    sections = []
    for p, x in ((body,SEAM+.1),(booster,SEAM-.1)):
        s = bd.section(p, section_by=bd.Plane(origin=(x,0,0), x_dir=(0,1,0), z_dir=(1,0,0)))
        sections.append(s)
    # Main exhaust recess removes center area, so compare outer boundary length.
    perimeters = [max(f.outer_wire().length for f in s.faces()) for s in sections]
    close(*perimeters, .01)
    for p,x in ((body,0),(booster,SEAM-40)):
        s=p.solids()[0]
        assert s.is_inside((x,99,0)) and s.is_inside((x,0,99))
        assert not s.is_inside((x,99,99)), "corner is not rounded"
        assert s.is_inside((x,78,78)), "section is too circular"
    contacts = {}
    for prefix, host in (("main_intake",body),("main_fin",body),("booster_fin",booster)):
        vols=[]
        for i in range(1,5):
            p=parts[f"{prefix}_{i}"]
            intersection = p & host
            contact = intersection.volume if intersection else 0
            assert contact > .01, f"floating {p.label}"
            contacts[p.label] = round(contact,3)
            vols.append(p.volume)
        assert max(vols)-min(vols)<.01, f"asymmetric {prefix}"
    mouth,base,height,clock = PROBES[key]
    for i in range(4):
        angle = clock+90*i
        p=parts[f"main_intake_{i+1}"].solids()[0]
        for x in (mouth-1,mouth-100,mouth-170):
            probe=point(x,base+height*.5,angle)
            assert not p.is_inside(probe), "blocked intake"
            assert not body.solids()[0].is_inside(probe), "body blocks mouth"
        assert p.is_inside(point(mouth-190,base+height*.5,angle)), "missing blind passage back"
    return dict(key=key,ok=True,parts=len(parts),length_mm=b.size.X,
                booster_length_mm=booster.bounding_box().size.X,seam_mm=SEAM,
                maximum_span_yz_mm=[b.size.Y,b.size.Z],join_outer_perimeters_mm=perimeters,
                contacts_mm3=contacts,separated_translation_mm=-340)


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("keys",nargs="*",default=list(FILES))
    args=parser.parse_args()
    results=[check(key) for key in args.keys]
    path=ROOT / "reviews" / ("checks_"+"".join(args.keys)+".json")
    path.write_text(json.dumps(results,indent=2)+"\n")
    print(json.dumps(results,indent=2))
