"""Assemble the round-2 Phantom review packet: candidate boards, comparison, context."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).parent
CANDIDATES = (
    ("Sled", "Candidate A - Sled: long stowed-panel wings, emitter insets, low dorsal spine"),
    ("Rails", "Candidate B - Rails: heavier mid-body slivers, tail surfaces, tall dorsal fin"),
    ("Dart", "Candidate C - Dart: clean body, four real-span tail fins, mid-body emitter panels"),
)
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


def candidate_board(name, caption):
    tile_width, tile_height = 900, 650
    board = Image.new("RGB", (tile_width * 2, tile_height * 4 + 30), "white")
    draw = ImageDraw.Draw(board)
    for index, (suffix, label) in enumerate(VIEWS):
        column, row = index % 2, index // 2
        with Image.open(ROOT / f"Phantom_R2_{name}_{suffix}.png") as image:
            tile = ImageOps.contain(image.convert("RGB"), (tile_width, tile_height - 35))
        x = column * tile_width + (tile_width - tile.width) // 2
        y = row * tile_height
        board.paste(tile, (x, y))
        draw.text((column * tile_width + 15, y + tile_height - 28), label, fill="black")
    draw.text((15, tile_height * 4 + 5), caption, fill="black")
    output = ROOT / f"Phantom_R2_{name}_Review.png"
    board.save(output)
    print(output)


def comparison_board():
    tile_w, tile_h = 760, 500
    board = Image.new("RGB", (tile_w * 3, (tile_h + 26) * 3 + 30), "white")
    draw = ImageDraw.Draw(board)
    for row, (name, caption) in enumerate(CANDIDATES):
        for column, (suffix, label) in enumerate((("side", "side"), ("iso", "iso"), ("tail", "tail/exhaust"))):
            with Image.open(ROOT / f"Phantom_R2_{name}_{suffix}.png") as image:
                tile = ImageOps.contain(image.convert("RGB"), (tile_w, tile_h))
            x = column * tile_w
            y = row * (tile_h + 26)
            board.paste(tile, (x, y))
            draw.text((x + 12, y + tile_h + 4), f"{name}: {label}", fill="black")
    draw.text((12, (tile_h + 26) * 3 + 8), "RDM-9 Phantom round-2 candidates - shared wedge-nose airframe, same scale", fill="black")
    output = ROOT / "Phantom_R2_Comparison.png"
    board.save(output)
    print(output)


def context_board():
    tile_w, tile_h = 900, 620
    board = Image.new("RGB", (tile_w * 2, (tile_h + 26) * 3 + 10), "white")
    draw = ImageDraw.Draw(board)
    for row, (name, _) in enumerate(CANDIDATES):
        for column, (suffix, label) in enumerate((("iso", "isometric"), ("side", "side"))):
            with Image.open(ROOT / f"Phantom_R2_Context_{name}_{suffix}.png") as image:
                tile = ImageOps.contain(image.convert("RGB"), (tile_w, tile_h))
            x = column * tile_w
            y = row * (tile_h + 26)
            board.paste(tile, (x, y))
            draw.text((x + 12, y + tile_h + 4), f"{name} with pylon pad: {label}", fill="black")
    draw.text((12, (tile_h + 26) * 3 + 2), "Carriage-context mockups: 700 x 80 mm dorsal pylon pad, 1 mm above the body crown", fill="black")
    output = ROOT / "Phantom_R2_Context_Board.png"
    board.save(output)
    print(output)


if __name__ == "__main__":
    for name, caption in CANDIDATES:
        candidate_board(name, caption)
    comparison_board()
    context_board()
