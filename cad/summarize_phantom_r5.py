"""Assemble the RDM-9 Phantom R5 review packet: deployed and retracted boards."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).parent
VIEWS = (
    ("iso", "opposed isometric A"),
    ("opposite", "opposed isometric B"),
    ("side", "side orthographic"),
    ("top", "top orthographic"),
    ("bottom", "bottom orthographic"),
    ("nose", "nose end view"),
    ("tail", "tail / exhaust end view"),
    ("grazing", "body grazing view"),
)
BOARDS = (
    ("Phantom_R5_Dart", "RDM-9 Phantom R5 dart5 deployed - 2.5 mm folding panels swept out"),
    ("Phantom_R5_Retracted", "RDM-9 Phantom R5 retracted - panels parked in the dorsal bay, slot + hinge fairing"),
)


def main():
    tile_width, tile_height = 900, 650
    for stem, caption in BOARDS:
        board = Image.new("RGB", (tile_width * 2, tile_height * 4 + 30), "white")
        draw = ImageDraw.Draw(board)
        for index, (suffix, label) in enumerate(VIEWS):
            column, row = index % 2, index // 2
            with Image.open(ROOT / f"{stem}_{suffix}.png") as image:
                tile = ImageOps.contain(image.convert("RGB"), (tile_width, tile_height - 35))
            x = column * tile_width + (tile_width - tile.width) // 2
            y = row * tile_height
            board.paste(tile, (x, y))
            draw.text((column * tile_width + 15, y + tile_height - 28), label, fill="black")
        draw.text((15, tile_height * 4 + 5), caption, fill="black")
        output = ROOT / f"{stem}_Review.png"
        board.save(output)
        print(output)

    ctx_w, ctx_h = 900, 620
    context = Image.new("RGB", (ctx_w * 2, ctx_h + 26), "white")
    cdraw = ImageDraw.Draw(context)
    for column, (suffix, label) in enumerate((("iso", "isometric"), ("side", "side"))):
        with Image.open(ROOT / f"Phantom_R5_Context_Retracted_{suffix}.png") as image:
            tile = ImageOps.contain(image.convert("RGB"), (ctx_w, ctx_h))
        context.paste(tile, (column * ctx_w, 0))
        cdraw.text((column * ctx_w + 12, ctx_h + 4), f"retracted with pylon pad: {label}", fill="black")
    context_output = ROOT / "Phantom_R5_Context_Board.png"
    context.save(context_output)
    print(context_output)


if __name__ == "__main__":
    main()
