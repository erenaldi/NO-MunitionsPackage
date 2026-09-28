from cadgen import read_step
r=read_step("STEP/S_AftExhaust_R1_AftSection.step")
def leaves(n):
    c=list(getattr(n,"children",()) or ())
    return [l for k in c for l in leaves(k)] if c else [n]
for l in leaves(r):
    bb=l.bounding_box(); print(l.label, round(bb.min.X),round(bb.max.X),round(bb.min.Y),round(bb.max.Y),round(bb.min.Z),round(bb.max.Z), round(l.volume))
