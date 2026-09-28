"""Create a labeled review board from the generated Phantom snapshots."""

from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).parent
WIDTHS = (180, 220, 260)
TILE_WIDTH = 720
TILE_HEIGHT = 500


def load_tile(path, size):
    with Image.open(path) as image:
        return ImageOps.contain(image.convert("RGB"), size)


def main():
    board = Image.new("RGB", (TILE_WIDTH * 3, TILE_HEIGHT * 3), "white")
    draw = ImageDraw.Draw(board)
    for column, width in enumerate(WIDTHS):
        x = column * TILE_WIDTH
        draw.text((x + 20, 15), f"{width} mm lens width", fill="black")

        iso = load_tile(ROOT / f"Phantom_Lens{width}_iso.png", (TILE_WIDTH, 440))
        board.paste(iso, (x + (TILE_WIDTH - iso.width) // 2, 45))

        side_path = ROOT / f"Phantom_Lens{width}_side.png"
        side = load_tile(side_path, (TILE_WIDTH, 440))
        board.paste(side, (x + (TILE_WIDTH - side.width) // 2, TILE_HEIGHT + 45))

        with Image.open(side_path) as image:
            source = image.convert("RGB")
            center_x, center_y = source.width // 2, source.height // 2
            lens = source.crop((center_x - 210, center_y - 170, center_x + 210, center_y + 170))
            lens = ImageOps.contain(lens, (TILE_WIDTH - 40, 400))
        board.paste(
            lens,
            (x + (TILE_WIDTH - lens.width) // 2, TILE_HEIGHT * 2 + 55),
        )

    for row, label in enumerate(("opposed isometric", "side orthographic", "mid-body lens close-up")):
        draw.text((20, row * TILE_HEIGHT + 475), label, fill="black")

    output = ROOT / "Phantom_Lens_Comparison.png"
    board.save(output)
    print(output)


if __name__ == "__main__":
    main()
