from cadgen import build123d as bd, read_step
def leaves(n):
    c=list(getattr(n,"children",()) or ())
    return [l for k in c for l in leaves(k)] if c else [n]
for st in ("Stowed","Deployed"):
    r=[l for l in leaves(read_step(f"STEP/S_AftExhaust_R1_{st}.step")) if str(l.label).startswith("intake_r1_ramp")]
    print(st,[str(l.label) for l in r])
    for l in r:
        for x in (-900,-600,-320):
            for y in (0,50,61):
                s=l & bd.Box(0.2,0.2,400).translate((x,y,0))
                if s is not None and s.volume>0:
                    bb=s.bounding_box(); print(" x",x,"y",y,"z",round(bb.min.Z,1),round(bb.max.Z,1))
