import sys
sys.path.insert(0,'src')
from cadgen import build123d as bd
import aft_exhaust_r1 as aft
import engine_bay_b2 as b
parts=aft._read_parts("Deployed")
r=parts["intake_r1_ramp"]
print("ramp solids",len(r.solids()),[round(s.volume) for s in r.solids()])
for x in (-800,-600,-400):
    sl=r & bd.Box(0.2,300,300).translate((x,0,0))
    for s in sl.solids():
        bb=s.bounding_box(); print(x,"y",round(bb.min.Y,1),round(bb.max.Y,1),"z",round(bb.min.Z,1),round(bb.max.Z,1),round(s.volume,1))
blk=b.engine_block(b.RAMP_DEG)[0]
inter=blk & r
print("overlap", None if inter is None else [(round(s.volume,1),[round(v,1) for v in (s.bounding_box().min.X,s.bounding_box().max.X,s.bounding_box().min.Y,s.bounding_box().max.Y,s.bounding_box().min.Z,s.bounding_box().max.Z)]) for s in inter.solids()])
