"""Matched concept boards and same-scale silhouettes against the actual AAM4 dump.

The reference is a missile mesh, not a mounted aircraft clearance test.
"""
import json
from pathlib import Path
import numpy as np
import trimesh
from PIL import Image, ImageDraw, ImageOps
from cadgen import read_step

ROOT = Path(__file__).resolve().parent
DUMP = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option\BepInEx\config\Erenaldi.MunitionsPackage")


def main():
    views = ("iso", "opposite", "side", "top", "nose", "tail", "separated",
             "separated_opposite", "intake", "mouth", "grazing", "upper_aft", "booster_face")
    for start in range(0, len(views), 4):
        board = Image.new("RGB", (1600, 2520), "white")
        draw = ImageDraw.Draw(board)
        for row, view in enumerate(views[start:start+4]):
            for col, name in enumerate(("Pod", "Shoulder")):
                path = ROOT / f"Halberd_Concept_{name}_{view}.png"
                with Image.open(path) as image:
                    tile = ImageOps.contain(image.convert("RGB"), (800, 600))
                board.paste(tile, (col*800, row*630))
                draw.text((col*800+10, row*630+605), f"{name}: {view}", fill="black")
        output = ROOT / f"Halberd_Concept_Comparison_{start//4+1}.png"
        board.save(output)
        print(output)

    dump = json.loads((DUMP / "missile-geometry.json").read_text())
    entry = next(item for item in dump["targets"] if item["prefabName"] == "AAM4")
    vanilla = trimesh.load(DUMP / entry["objFileName"], force="mesh", process=False)
    # Inverse of the established game basis, for comparison only.
    vertices = np.asarray(vanilla.vertices)[:, [2, 0, 1]] * 1000
    datasets = [("AAM4 runtime mesh", [(vertices, vanilla.faces)])]
    for name in ("Pod", "Shoulder"):
        model = read_step(ROOT / f"Halberd_Concept_{name}.step")
        meshes = []
        for part in model.children:
            points, faces = part.tessellate(0.3, 0.15)
            meshes.append((np.array([(v.X, v.Y, v.Z) for v in points]), faces))
        datasets.append((name, meshes))
    page = Image.new("RGB", (1800, 1140), "white")
    draw = ImageDraw.Draw(page)
    for row, (name, meshes) in enumerate(datasets):
        for col, axis in enumerate((2, 1)):
            ox, oy = 450+col*900, 180+row*380
            scale = 0.235
            for points, faces in meshes:
                projected = [(ox+p[0]*scale, oy-p[axis]*scale) for p in points]
                for triangle in faces:
                    draw.polygon([projected[i] for i in triangle], fill="#344449")
            draw.text((col*900+20, row*380+20), f"{name} - {'side' if axis==2 else 'top'} - same scale", fill="black")
            draw.line((ox-1000*scale, oy+100, ox+1000*scale, oy+100), fill="black", width=2)
            draw.text((ox-20, oy+110), "2 metres", fill="black")
    path = ROOT / "Halberd_Concept_AAM4_Silhouettes.png"
    page.save(path)
    print(path)


if __name__ == "__main__":
    main()
