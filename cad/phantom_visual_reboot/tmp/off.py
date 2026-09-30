import time
from cadgen import read_scene
from cadgen import build123d as bd
s=read_scene("STEP/S_EngineBay_B2H_Stowed_Full.step")
body=[l for l in s.leaves() if 'symmetric_body' in str(getattr(l,'label',''))][0].shape()
print(body.volume, body.is_valid if not callable(body.is_valid) else body.is_valid())
for x in (850,900,990):
  for z in (-35,0,35):
    r=body&bd.Box(1,400,1).moved(bd.Location((x,0,z)))
    print(x,z,round(r.bounding_box().max.Y,2))
t=time.time()
try:
    o=bd.offset(body,amount=0.4); print('offset ok',o.volume,time.time()-t)
except Exception as e: print('offset fail',e)
