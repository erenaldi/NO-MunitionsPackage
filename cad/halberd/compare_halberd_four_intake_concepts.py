"""Build labeled matched-camera render boards for four concepts."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


ROOT = Path(__file__).resolve().parent
CONCEPTS = (
    ("C1", "Razorback"),
    ("C2", "Manta"),
    ("C3", "Citadel"),
    ("C4", "Petal"),
)


def render_board(filename, views, tile_size=(600, 450)):
    tile_width, tile_height = tile_size
    board = Image.new("RGB", (tile_width * len(views), (tile_height + 30) * 4), "white")
    draw = ImageDraw.Draw(board)
    for row, (code, name) in enumerate(CONCEPTS):
        stem = f"Halberd_{code}_{name}"
        for column, view in enumerate(views):
            with Image.open(ROOT / f"{stem}_{view}.png") as image:
                tile = ImageOps.contain(image.convert("RGB"), tile_size)
            x = column * tile_width + (tile_width - tile.width) // 2
            y = row * (tile_height + 30) + (tile_height - tile.height) // 2
            board.paste(tile, (x, y))
            draw.text((column * tile_width + 10, row * (tile_height + 30) + tile_height + 7),
                      f"{name} / {view}", fill="black")
    path = ROOT / filename
    board.save(path)
    print(path)


def main():
    render_board("Halberd_Four_Intake_Overview.png", ("iso", "opposite", "side", "top"))
    render_board("Halberd_Four_Intake_Details.png", ("nose", "tail", "intakes", "mouths", "grazing"))
    render_board("Halberd_Four_Intake_Separated.png", ("separated",), tile_size=(1200, 600))
    # All candidates share exact axial bounds; fixed cameras, padding, and pixel
    # dimensions therefore preserve their relative side/top silhouette scale.
    render_board("Halberd_Four_Intake_MatchedScale.png", ("side", "top"), tile_size=(800, 600))


if __name__ == "__main__":
    main()
