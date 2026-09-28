"""Focused R9 prototype views; dimensions are in each output record."""
import json
import argparse
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]


if __name__=="__main__":
    views={
        "side":("halberd_r9_focus",[0,-1,0],[-1260,0,125],130.,1800,850),
        "oblique":("halberd_r9_focus",[.3,-1,.6],[-1260,0,80],190.,1800,850),
        "top_taper":("halberd_r9_focus",[0,0,1],[-1235,0,136],24.,1800,600),
        "whole":("halberd_r9",[.35,1,.65],None,None,2200,850),
        "separated":("halberd_r9_separated",[.3,1,.65],[-1350,0,0],350.,1800,850),
    }
    parser=argparse.ArgumentParser()
    parser.add_argument("--only",choices=tuple(views))
    args=parser.parse_args()
    jobs=[]
    for name,(stem,direction,target,half,w,h) in views.items():
        if args.only and name!=args.only:
            continue
        camera={"projection":"orthographic","direction":direction}
        if name=="top_taper":
            camera["up"]=[0,1,0]
        if target is not None:
            camera.update(target=target,orthographicHalfHeight=half)
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",
                         display={"mode":"shaded_edges"},output={"padding":.08,"viewLabels":False},
                         outputs=[dict(path=str(ROOT/"reviews"/f"Halberd_R9_{name}.png"),
                                       camera=camera,width=w,height=h)]))
    job=ROOT/"reviews"/"halberd_R9_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    board=Image.new("RGB",(1800,2500),"#edf2f7")
    draw=ImageDraw.Draw(board)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",28)
    draw.text((20,15),"HALBERD R9 / ONE-STATION PROTOTYPE / 80 mm FIN + CURVED TRANSITION",font=font,fill="#24394a")
    y=65
    for name in ("side","oblique","top_taper"):
        draw.text((20,y),name.upper().replace("_"," "),font=font,fill="#24394a")
        image=Image.open(ROOT/"reviews"/f"Halberd_R9_{name}.png").convert("RGB")
        board.paste(image,(0,y+35))
        y+=image.height+45
    board.save(ROOT/"reviews"/"Halberd_R9_Prototype.png")
    print(ROOT/"reviews"/"Halberd_R9_Prototype.png")
