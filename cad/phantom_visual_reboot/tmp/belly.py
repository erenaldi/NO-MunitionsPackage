import sys
sys.path.insert(0,'.')
from cadgen import build123d as bd
import aft_exhaust_r1 as aft
body=aft._read_parts("Stowed")[aft.BODY_LABEL]
for x in (-985.0,-600.0,60.0,120.0):
    row=''.join('#' if body.is_inside(bd.Vector(x,y,-85.5)) else '.' for y in range(0,90,4))
    print(x,row,flush=True)
