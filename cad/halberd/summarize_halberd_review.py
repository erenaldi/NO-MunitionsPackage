"""Produce a labeled index of the exact snapshot packet; never alter source PNGs."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageOps


def main():
    root = Path(__file__).resolve().parent
    jobs = json.loads((root / "halberd_detailed_snapshot_job.json").read_text())
    paths = [output["path"] for job in jobs for output in job["outputs"]]
    destination = root.parent / "candidates" / "halberd"
    destination.mkdir(parents=True, exist_ok=True)
    for start in range(0, len(paths), 9):
        sheet = Image.new("RGB", (1800, 1440), "white")
        draw = ImageDraw.Draw(sheet)
        for index, name in enumerate(paths[start:start + 9]):
            x, y = (index % 3) * 600, (index // 3) * 480
            with Image.open(root / name) as image:
                tile = ImageOps.contain(image.convert("RGB"), (600, 450))
                sheet.paste(tile, (x + (600 - tile.width) // 2, y))
            draw.text((x + 10, y + 455), name, fill="black")
        path = destination / f"Halberd_review_sheet_{start // 9 + 1}.png"
        sheet.save(path)
        print(path)
    print(f"Indexed {len(paths)} snapshots")


if __name__ == "__main__":
    main()
