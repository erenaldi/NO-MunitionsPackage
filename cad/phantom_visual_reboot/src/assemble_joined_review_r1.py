"""Review layout from directly rendered CAD views; no geometry illustration."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

root=Path(__file__).resolve().parents[1]/'reviews'
board=Image.new('RGB',(2400,1400),'#e9eef2')
draw=ImageDraw.Draw(board)
font=ImageFont.load_default(size=28)
small=ImageFont.load_default(size=23)
draw.text((24,16),'PHANTOM | JOINED FORE/AFT PANELS + SLIDING REAR ROOT',font=font,fill='#253b46')
draw.text((24,54),'One joined side for review. Phantom-adapted motion; not an exact GBU-39 production mechanism.',font=small,fill='#253b46')
for column,(state,title) in enumerate([('stowed','STOWED'),('midfold','INTERMEDIATE | 50% carriage travel'),('deployed','DEPLOYED')]):
    for row,view in enumerate(['module_top','body_iso']):
        x=column*800
        y=100+row*640
        draw.text((x+16,y),title+(' / MODULE TOP' if row==0 else ' / ON BODY'),font=small,fill='#253b46')
        image=Image.open(root/f'L_{state}_{view}.png').convert('RGB')
        image.thumbnail((780,585),Image.Resampling.LANCZOS)
        board.paste(image,(x+(800-image.width)//2,y+34+(585-image.height)//2))
board.save(root/'L_JoinedWing_R1_Review.png')
