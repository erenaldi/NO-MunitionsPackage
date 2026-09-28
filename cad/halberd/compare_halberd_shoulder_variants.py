"""Equal-framing render boards plus true-scale side/top silhouette comparison."""
import json
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageOps
from cadgen import read_step
from halberd_shoulder_variants import VARIANTS
from compare_halberd_concepts import DUMP

ROOT=Path(__file__).resolve().parent


def main():
    panels=(("iso","opposite","side"),("top","nose","tail"),
            ("separated","separated_front","seam"),("seam_side","intakes","grazing"))
    for index, views in enumerate(panels,1):
        board=Image.new("RGB",(1800,2400),"white")
        draw=ImageDraw.Draw(board)
        for row,key in enumerate(VARIANTS):
            for col,view in enumerate(views):
                with Image.open(ROOT/f"Halberd_{key}_{view}.png") as image:
                    tile=ImageOps.contain(image.convert("RGB"),(600,450))
                board.paste(tile,(col*600,row*480))
                draw.text((col*600+10,row*480+458),f"{key.replace('_',' ')} / {view}",fill="black")
        path=ROOT/f"Halberd_B_Variants_Board_{index}.png"
        board.save(path)
        print(path)

    dump=json.loads((DUMP/"missile-geometry.json").read_text())
    entry=next(t for t in dump["targets"] if t["prefabName"]=="AAM4")
    mesh=trimesh.load(DUMP/entry["objFileName"],force="mesh",process=False)
    sets=[("AAM4 runtime reference",[(np.asarray(mesh.vertices)[:,[2,0,1]]*1000,mesh.faces)])]
    for key in VARIANTS:
        model=read_step(ROOT/f"Halberd_{key}.step")
        meshes=[]
        for part in model.children:
            points,faces=part.tessellate(.3,.15)
            meshes.append((np.array([(v.X,v.Y,v.Z) for v in points]),faces))
        sets.append((key,meshes))
    page=Image.new("RGB",(2000,1560),"white")
    draw=ImageDraw.Draw(page)
    for row,(key,meshes) in enumerate(sets):
        for col,axis in enumerate((2,1)):
            x,y=500+col*1000,130+row*260
            for points,faces in meshes:
                projected=[(x+p[0]*.235,y-p[axis]*.235) for p in points]
                for face in faces:
                    draw.polygon([projected[i] for i in face],fill="#344449")
            draw.text((col*1000+15,row*260+12),f"{key} / {'side' if axis==2 else 'top'} / identical scale",fill="black")
            draw.line((x-235,y+85,x+235,y+85),fill="black",width=2)
            draw.text((x-20,y+93),"2 metres",fill="black")
    path=ROOT/"Halberd_B_Variants_TrueScale.png"
    page.save(path)
    print(path)


if __name__=="__main__":
    main()
