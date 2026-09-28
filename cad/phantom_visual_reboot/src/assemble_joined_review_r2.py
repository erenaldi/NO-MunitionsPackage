"""Matched OLD/NEW review board for the R2 inward-biased chord doubling.

Draws the 125 mm stowed envelope circle onto the stowed end views (world
scale: end camera is orthographic, target (0,0,0), half-height 140 mm, so
pixels_per_mm = height/(2*140)) and composes the board from the rendered
L2_*/M2_* comparison PNGs. Every OLD/NEW pair shares one camera, so scale and
framing are identical within each pair.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1] / 'reviews'
W = 2400
MARGIN = 24
GAP = 16
CELL_W = (W - 2 * MARGIN - 3 * GAP) // 4
CELL_H = int(CELL_W * 1200 / 1600)
ROW_H = CELL_H + 130
BODY_CELL_W = (W - 2 * MARGIN - GAP) // 2
BODY_CELL_H = int(BODY_CELL_W * 1200 / 1600)
BODY_ROW_H = BODY_CELL_H + 130

font = ImageFont.load_default(size=30)
small = ImageFont.load_default(size=22)


def envelope(png):
    """Draw the 125 mm radius envelope circle on a stowed end view."""
    image = Image.open(png).convert('RGB')
    draw = ImageDraw.Draw(image)
    ppm = image.height / (2 * 140.0)
    radius = int(125 * ppm)
    cx, cy = image.width // 2, image.height // 2
    draw.ellipse((cx - radius, cy - radius, cx + radius, cy + radius),
                 outline='#B03030', width=3)
    draw.text((cx + radius + 12, cy - 14), 'R125', font=ImageFont.load_default(size=26),
              fill='#B03030')
    image.save(png)


def paste(image, box, target):
    image.thumbnail((box[2], box[3]), Image.Resampling.LANCZOS)
    target.paste(image, (box[0] + (box[2] - image.width) // 2,
                         box[1] + (box[3] - image.height) // 2))


def label(draw, x, y, text, fill='#253b46'):
    draw.text((x, y), text, font=small, fill=fill)


rows = []
for state, title in [('stowed', 'STOWED'), ('midfold', 'INTERMEDIATE | 50% carriage travel'),
                     ('deployed', 'DEPLOYED')]:
    rows.append((title + ' / MODULE TOP + ISO', [
        ('L2_' + state + '_module_top.png', 'OLD'),
        ('M2_' + state + '_module_top.png', 'NEW'),
        ('L2_' + state + '_module_iso.png', 'OLD'),
        ('M2_' + state + '_module_iso.png', 'NEW')]))
rows.append(('STOWED END (125 mm envelope) + DEPLOYED OPPOSED CLOSEUP', [
    ('L2_stowed_body_end_env.png', 'OLD'),
    ('M2_stowed_body_end_env.png', 'NEW'),
    ('L2_deployed_module_opposed.png', 'OLD'),
    ('M2_deployed_module_opposed.png', 'NEW')]))
body_rows = [
    ('STOWED / ON BODY', [('L2_stowed_body_iso.png', 'OLD'), ('M2_stowed_body_iso.png', 'NEW')]),
    ('INTERMEDIATE / ON BODY', [('L2_midfold_body_iso.png', 'OLD'), ('M2_midfold_body_iso.png', 'NEW')]),
    ('DEPLOYED / ON BODY', [('L2_deployed_body_iso.png', 'OLD'), ('M2_deployed_body_iso.png', 'NEW')]),
]

# Draw the envelope onto the stowed end comparison PNGs first.
envelope(root / 'L2_stowed_body_end_env.png')
envelope(root / 'M2_stowed_body_end_env.png')

height = 130 + len(rows) * ROW_H + len(body_rows) * BODY_ROW_H + 20
board = Image.new('RGB', (W, height), '#e9eef2')
draw = ImageDraw.Draw(board)
draw.text((MARGIN, 16), 'PHANTOM | JOINED WING R2 — INWARD-BIASED CHORD DOUBLING (OLD L vs NEW M)',
          font=font, fill='#253b46')
draw.text((MARGIN, 58), 'Matched pairs share camera target/scale/framing. Outer stowed edge retained; extra chord added toward centreline.',
          font=small, fill='#253b46')

y = 130
for title, cells in rows:
    label(draw, MARGIN, y, title)
    y += 34
    for i, (name, tag_text) in enumerate(cells):
        x = MARGIN + i * (CELL_W + GAP)
        label(draw, x + 8, y, tag_text, fill='#7a4a2b' if tag_text == 'OLD' else '#2b6a4a')
        paste(Image.open(root / name), (x, y + 26, CELL_W, CELL_H), board)
    y += CELL_H + 26
    y += 70

for title, cells in body_rows:
    label(draw, MARGIN, y, title)
    y += 34
    for i, (name, tag_text) in enumerate(cells):
        x = MARGIN + i * (BODY_CELL_W + GAP)
        label(draw, x + 8, y, tag_text, fill='#7a4a2b' if tag_text == 'OLD' else '#2b6a4a')
        paste(Image.open(root / name), (x, y + 26, BODY_CELL_W, BODY_CELL_H), board)
    y += BODY_CELL_H + 26
    y += 70

board.save(root / 'M_JoinedWing_R2_Review.png')
print('saved', root / 'M_JoinedWing_R2_Review.png', board.size)
