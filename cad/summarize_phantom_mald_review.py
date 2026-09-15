"""Assemble the compact MALD-inspired Phantom silhouette review packet."""

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
    ("intake_grazing", "dorsal intake grazing view"),
)


def main():
    tile_width, tile_height = 900, 650
    board = Image.new("RGB", (tile_width * 2, tile_height * 4), "white")
    draw = ImageDraw.Draw(board)
    for index, (suffix, label) in enumerate(VIEWS):
        column, row = index % 2, index // 2
        with Image.open(ROOT / f"Phantom_MALD_{suffix}.png") as image:
            tile = ImageOps.contain(image.convert("RGB"), (tile_width, tile_height - 35))
        x = column * tile_width + (tile_width - tile.width) // 2
        y = row * tile_height
        board.paste(tile, (x, y))
        draw.text((column * tile_width + 15, y + tile_height - 28), label, fill="black")

    output = ROOT / "Phantom_MALD_Review.png"
    board.save(output)
    print(output)


if __name__ == "__main__":
    main()
