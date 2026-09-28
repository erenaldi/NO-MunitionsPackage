"""First detail prototype with selected Kris reference comparison."""
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]


if __name__=="__main__":
    views={
        "detail_oblique":("halberd_r13_focus",[.3,-.45,1],1600,1100),
        "detail_top":("halberd_r13_focus",[0,0,1],1600,1100),
        "detail_grazing":("halberd_r13_focus",[1,0,.3],1600,1100),
        "whole":("halberd_r13",[.3,1,.8],2200,850),
        "separated":("halberd_r13_separated",[.3,1,.8],2200,850),
    }
    jobs=[]
    for name,(stem,direction,w,h) in views.items():
        camera={"projection":"orthographic","direction":direction}
        if direction==[0,0,1]:
            camera["up"]=[0,1,0]
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",
                         display={"mode":"shaded_edges"},output={"padding":.08,"viewLabels":False},
                         outputs=[dict(path=str(ROOT/"reviews"/f"R13_{name}.png"),camera=camera,width=w,height=h)]))
    job=ROOT/"reviews"/"r13_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    board=Image.new("RGB",(2400,980),"#edf2f7")
    draw=ImageDraw.Draw(board)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",30)
    for i,(file,title) in enumerate((("Kris_detail_oblique.png","KRIS HYBRID / SELECTED DETAIL REFERENCE"),
                                     ("R13_detail_oblique.png","HALBERD / FIRST RECESSED COVER PROTOTYPE"))):
        draw.text((i*1200+20,20),title,font=font,fill="#24394a")
        image=Image.open(ROOT/"reviews"/file).convert("RGB")
        image.thumbnail((1200,900))
        board.paste(image,(i*1200+(1200-image.width)//2,70))
    board.save(ROOT/"reviews"/"R13_Kris_Detail_Comparison.png")
