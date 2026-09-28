from cadgen import build123d as bd, read_step
r=read_step("STEP/S_AftExhaust_R1_AftSection.step")
def leaves(n):
    c=list(getattr(n,"children",()) or ())
    return [l for k in c for l in leaves(k)] if c else [n]
b=[l for l in leaves(r) if str(l.label).startswith("RDM9")][0]
import sys
for x in (-600.0,-320.0,-300.0,-200.0):
  for y in (10.0,50.0,58.0,62.0,66.0):
    row=''.join('.' if not b.is_inside(bd.Vector(x,y,z)) else '#' for z in range(-90,-14,4))
    print(x,y,row,flush=True)
