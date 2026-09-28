"""Single-corner concept comparison at matched camera scales."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
R = ROOT/'reviews'
board = Image.new('RGB',(1800,2100),'#e9eff3')
d = ImageDraw.Draw(board)
font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
small = ImageFont.truetype('C:/Windows/Fonts/arial.ttf',18)
d.text((20,15),'PHANTOM REAR FIN - ONE CORNER ONLY - ROUGH PLANFORM SELECTION',font=font,fill='#263c49')
for col,(name,title) in enumerate([('Compact','COMPACT / 70 mm span'),('Swept','STRONGLY SWEPT / 90 mm span'),('Tall','TALL CLIPPED / 110 mm span')]):
    x = col*600
    d.text((x+15,60),title,font=font,fill='#263c49')
    for row,(suffix,label) in enumerate([('Deployed_close','DEPLOYED / DIAGONAL OUTWARD'),
                                        ('Stowed_close','STOWED / FLAT ON BODY FACE'),
                                        ('Midfold_close','MID-FOLD / SAME PHYSICAL FIN'),
                                        ('context','WHOLE-VEHICLE CONTEXT')]):
        y = 105+row*480
        d.text((x+15,y),label,font=small,fill='#263c49')
        im = Image.open(R/f'Q_Tail_R1_{name}_{suffix}.png').convert('RGB')
        im.thumbnail((580,435))
        board.paste(im,(x+(600-im.width)//2,y+30))
d.text((20,2040),'Shared 240 mm root; 3 mm panel; 135-degree fold. All three pass 31 sampled fold positions.',font=small,fill='#263c49')
d.text((20,2070),'Choose a planform before detailing or four-corner replication. A5 wing/pocket/cover baseline unchanged.',font=small,fill='#263c49')
board.save(R/'Q_Tail_R1_Comparison.png')
