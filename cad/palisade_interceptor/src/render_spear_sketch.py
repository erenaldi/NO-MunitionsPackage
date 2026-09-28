"""Compare Broad against two one-fin interpretations of the user drawing."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps

from render_spear_revisions import REVIEWS, snapshot, tight


NAMES = ("Broad", "SketchSpan", "SketchLow")


def main():
    for name in NAMES:
        snapshot(f"Spear_{name}_Boattail", ("sketch_iso",))
        snapshot(f"Spear_{name}_Boattail_Separated", ("sketch_separated",))
        snapshot(f"Spear_{name}_Fin_Focus", ("sketch_fin",))
    board = Image.new("RGB", (3*850, 3*540+90), "white")
    draw = ImageDraw.Draw(board)
    draw.text((22, 16), "USER DRAWING: long, low trapezoid; tip chord ~83% of root, longer bevel forward (+X right).", fill="#162536")
    draw.text((22, 42), "Reference image supplied in chat; no saved local image file. Only ONE fin changed in each CAD preview.", fill="#162536")
    for col, name in enumerate(NAMES):
        stem = f"Spear_{name}"
        for row, view in enumerate(("sketch_iso", "sketch_fin", "sketch_separated")):
            if row == 1:
                filename = f"{stem}_Fin_Focus_{view}.png"
            else:
                state = "_Boattail_Separated" if row == 2 else "_Boattail"
                filename = f"{stem}{state}_{view}.png"
            image = tight(REVIEWS / filename)
            if row == 1:
                image = image.crop((0, int(image.height*.22),
                                    int(image.width*.44), int(image.height*.82)))
            tile = ImageOps.contain(image, (815, 475), Image.Resampling.LANCZOS)
            x, y = col*850+(850-tile.width)//2, row*540+90+(490-tile.height)//2
            board.paste(tile, (x, y))
            label = ("original Broad tip 82/200 mm",
                     "SketchSpan tip 165/200; radius 92 mm",
                     "SketchLow tip 165/200; radius 79 mm")[col]
            draw.text((col*850+17, row*540+90+500), f"{label} | {view}", fill="#152333")
    path = REVIEWS / "Spear_UserFin_Sketch_Comparison.png"
    board.save(path)
    print(path)


if __name__ == "__main__":
    main()
