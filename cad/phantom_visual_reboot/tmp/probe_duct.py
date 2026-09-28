from cadgen import build123d as bd, read_step
r=read_step("STEP/S_AftExhaust_R1_Body_Duct.step")
def leaves(n):
    c=list(getattr(n,"children",()) or ())
    return [l for k in c for l in leaves(k)] if c else [n]
b=leaves(r)[0]
slab=bd.Box(3000,0.02,400)
s=b & slab
for f in s.faces():
    if f.area>1000 and abs(f.normal_at().Y)>0.9:
        print("face area",round(f.area), "outer bb",f.bounding_box().min.X,f.bounding_box().max.X)
        for w in f.inner_wires():
            bb=w.bounding_box(); print(" inner X",round(bb.min.X,1),round(bb.max.X,1),"Z",round(bb.min.Z,1),round(bb.max.Z,1))
