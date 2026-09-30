from cadgen import read_scene
s=read_scene("reference/agm1_mount/DonorPylon_Surface.step")
for l in s.leaves():
    b=l.shape().bounding_box(); print(getattr(l,'label',None),[round(v) for v in (b.min.X,b.max.X,b.min.Y,b.max.Y,b.min.Z,b.max.Z)])
