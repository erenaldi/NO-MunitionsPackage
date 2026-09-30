from cadgen import read_scene
s=read_scene("STEP/S_EngineBay_B2H_Stowed_Full.step")
for l in s.leaves():
    try:
        sh=l.shape() if callable(getattr(l,'shape',None)) else l.shape
        b=sh.bounding_box()
        print(getattr(l,'label',None) or getattr(l,'name',None), round(b.min.X),round(b.max.X),round(b.min.Y),round(b.max.Y),round(b.min.Z),round(b.max.Z))
    except Exception as e:
        print('ERR',l,e);break
