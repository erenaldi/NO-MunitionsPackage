"""Label verified CAD snapshots for the local symmetry/one-wing review."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root=Path(__file__).resolve().parents[1]/'reviews'
board=Image.new('RGB',(1800,1480),'#e9eef2')
draw=ImageDraw.Draw(board)
font=ImageFont.load_default(size=26)
draw.text((24,16),'RDM-9 | MIRRORED LOWER SHOULDERS + ONE-WING FOLD STUDY',font=font,fill='#253b46')
panels=[('J_front.png','LOWER SHOULDERS | mirrored geometry; equal face areas'),
        ('K_deployed_iso.png','DEPLOYED | one 650 mm-span prototype panel'),
        ('K_midfold_iso.png','MID-FOLD | same panel, 45 degrees about the pin'),
        ('K_stowed_iso.png','STOWED | same panel, 90 degrees; visibly external')]
for index,(name,title) in enumerate(panels):
    x=(index%2)*900
    y=64+(index//2)*704
    draw.text((x+16,y+6),title,font=font,fill='#253b46')
    image=Image.open(root/name).convert('RGB')
    image.thumbnail((880,660),Image.Resampling.LANCZOS)
    board.paste(image,(x+(900-image.width)//2,y+42+(660-image.height)//2))
board.save(root/'JK_Symmetry_OneWing_Review.png')
