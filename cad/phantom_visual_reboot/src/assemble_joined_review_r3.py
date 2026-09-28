"""R3 review board with orthographic carriage-envelope overlay."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
ROOT=Path(__file__).resolve().parents[1]/'reviews'
end=Image.open(ROOT/'N3_end.png').convert('RGB')
d=ImageDraw.Draw(end)
r=125*end.height/280
x,y=end.width/2,end.height/2
d.ellipse((x-r,y-r,x+r,y+r),outline='#B03030',width=3)
d.text((x+r+8,y),'R125',fill='#B03030',font=ImageFont.load_default(size=24))
end.save(ROOT/'N3_end_envelope.png')
cells=[('STOWED / FOUR LAYERS + SIDE SUPPORT','N3_module_end.png'),
       ('STOWED / 250 mm ENVELOPE','N3_end_envelope.png'),
       ('STOWED / ON UNCHANGED BODY','N3_body_iso.png'),
       ('DEPLOYED / BOTH JOINED SETS','N3_deployed_iso.png'),
       ('INTERMEDIATE / SIMULTANEOUS MOTION','N3_mid_top.png'),
       ('DEPLOYED / MATCHED AXIAL STATIONS','N3_deployed_top.png')]
board=Image.new('RGB',(2000,2500),'#e9eef2')
d=ImageDraw.Draw(board)
d.text((20,16),'PHANTOM N / R3 — TWO SETS, UNCHANGED BODY AND R2 PANELS',fill='#253b46',font=ImageFont.load_default(size=28))
d.text((20,56),'Packaging prototype: four layers, side-supported upper carriage. Visual approval pending.',fill='#253b46',font=ImageFont.load_default(size=22))
for i,(title,name) in enumerate(cells):
    x=(i%2)*1000
    y=110+(i//2)*795
    d.text((x+16,y),title,fill='#253b46',font=ImageFont.load_default(size=21))
    im=Image.open(ROOT/name).convert('RGB')
    im.thumbnail((980,735))
    board.paste(im,(x+10,y+35))
board.save(ROOT/'N_JoinedWing_R3_Review.png')
