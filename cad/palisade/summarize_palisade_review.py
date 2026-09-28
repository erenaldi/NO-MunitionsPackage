"""Assemble the HKP-1 Palisade interceptor silhouette review packet."""

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
    ("tail", "tail / cap end view"),
    ("cap_interface", "body/cap interface grazing view"),
    ("separated", "turning cap separated"),
    ("main_nozzle", "main nozzle exposed after separation"),
)


def main():
    tile_width, tile_height = 900, 650
    rows = (len(VIEWS) + 1) // 2
    board = Image.new("RGB", (tile_width * 2, tile_height * rows), "white")
    draw = ImageDraw.Draw(board)
    for index, (suffix, label) in enumerate(VIEWS):
        column, row = index % 2, index // 2
        with Image.open(ROOT / f"Palisade_{suffix}.png") as image:
            tile = ImageOps.contain(image.convert("RGB"), (tile_width, tile_height - 35))
        x = column * tile_width + (tile_width - tile.width) // 2
        y = row * tile_height
        board.paste(tile, (x, y))
        draw.text((column * tile_width + 15, y + tile_height - 28), label, fill="black")

    output = ROOT / "Palisade_Review.png"
    board.save(output)
    print(output)


if __name__ == "__main__":
    main()
