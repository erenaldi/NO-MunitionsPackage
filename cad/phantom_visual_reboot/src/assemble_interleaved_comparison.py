"""Matched N/A board; source PNGs retain identical camera settings."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
R = ROOT/'reviews'
board = Image.new('RGB', (1600, 1900), '#e9eff3')
d = ImageDraw.Draw(board)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 22)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 18)
d.text((20, 15), 'PHANTOM - MATCHED N / A COMPARISON - CAD REVIEW, USER ACCEPTANCE PENDING', fill='#263c49', font=font)
for col, prefix, label in [(0, 'N3_', 'N / R3: 10.5 mm corresponding-panel offset'),
                            (1, 'O_A_', 'A / Interleaved: 5.5 mm offset (47.6% reduction)')]:
    d.text((col*800+20, 55), label, fill='#263c49', font=small)
    for row, (name, title) in enumerate([('module_end','STOWED STACK / SUPPORT'),
                                         ('module_iso','ISOLATED STOWED'),
                                         ('deployed_iso','DEPLOYED'),
                                         ('deployed_top','DEPLOYED TOP / SAME PLANFORM')]):
        y = 100+row*430
        d.text((col*800+20,y), title, fill='#263c49', font=small)
        im = Image.open(R/(prefix+name+'.png')).convert('RGB')
        im.thumbnail((780,390))
        board.paste(im, (col*800+(800-im.width)//2,y+30))
d.text((20,1840), 'A: R <= 124.271 mm; 21 sampled poses pass; minimum panel clearance 0.25 mm.', fill='#263c49', font=small)
d.text((20,1870), 'B: clearance probe only. Supported levelling assembly remains unverified.', fill='#263c49', font=small)
board.save(R/'O_A_vs_N_Comparison.png')
