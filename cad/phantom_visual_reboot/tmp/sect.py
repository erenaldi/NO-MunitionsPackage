from cadgen import read_scene
from cadgen import build123d as bd
s=read_scene("STEP/S_EngineBay_B2H_Stowed_Full.step")
body=[l for l in s.leaves() if 'symmetric_body' in str(getattr(l,'label',''))][0]
sh=body.shape()
for x in [1400,1395,1300,1200,1100,1000,950,900,800,600,0,-800,-1200,-1390]:
    r=sh&bd.Box(0.5,400,400).moved(bd.Location((x,0,0))); b=r.bounding_box()
    print(x,round(b.min.Y,1),round(b.max.Y,1),round(b.min.Z,1),round(b.max.Z,1))
