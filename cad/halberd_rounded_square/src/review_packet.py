"""Explicit CAD snapshot jobs and contact sheets; run from any working directory."""
import argparse
import json
import subprocess
import sys
import math
import itertools
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from cadgen import read_step

ROOT=Path(__file__).resolve().parents[1]
STEMS={"A":"A_Trace","B":"B_Chine","C":"C_Shoulder"}
VIEWS={"iso":[.35,-1,.55],"opposite":[-.35,1,-.55],
       "side":[0,-1,0],"top":[0,0,1],"front":[1,0,0],"rear":[-1,0,0]}


def framing(bounds, direction, width, height, top=False):
    """Match cadgen's projected-bounds orthographic fit, then lock across studies."""
    def unit(v):
        length=math.sqrt(sum(x*x for x in v))
        return [x/length for x in v]
    def cross(a,b):
        return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
    direction=unit(direction)
    right=unit(cross(direction,[0,1,0] if top else [0,0,1]))
    up=unit(cross(right,direction))
    corners=list(itertools.product((bounds.min.X,bounds.max.X),(bounds.min.Y,bounds.max.Y),(bounds.min.Z,bounds.max.Z)))
    spans=[]
    for axis in (right,up):
        values=[sum(a*b for a,b in zip(p,axis)) for p in corners]
        spans.append(max(values)-min(values))
    return max(spans[1]/(2*.84),spans[0]/(2*width/height*.84))


def jobs(keys):
    result=[]
    bounds={key:read_step(ROOT/"STEP"/(STEMS[key]+".step")).bounding_box() for key in keys}
    common={view:max(framing(bounds[key],direction,1000 if view in ("front","rear") else 2400,
                            1000 if view in ("front","rear") else 900,view=="top") for key in keys)
            for view,direction in VIEWS.items()}
    separated_bounds={key:read_step(ROOT/"STEP"/(STEMS[key]+"_Separated.step")).bounding_box() for key in keys}
    separated_frames={key:framing(b,[-.25,-1,.55],2400,900) for key,b in separated_bounds.items()}
    for key in keys:
        stem=STEMS[key]
        outputs=[{"path":str(ROOT/"reviews"/f"{key}_{view}.png"),
                  "camera":({"preset":"top"} if view=="top" else {"direction":direction}),
                  **({"width":1000,"height":1000} if view in ("front","rear") else {})}
                 for view,direction in VIEWS.items()]
        for output,view in zip(outputs,VIEWS):
            output["camera"]["zoom"]=framing(bounds[key],VIEWS[view],output.get("width",2400),
                                              output.get("height",900),view=="top")/common[view]
        # Explicit perspective cameras keep the local feature large in frame.
        details=[
            {"path":str(ROOT/"reviews"/f"{key}_nose_detail.png"),
             "camera":{"position":[1650,-1400,800],"target":[1080,0,0],"zoom":2.1}},
            {"path":str(ROOT/"reviews"/f"{key}_intake_detail.png"),
             "camera":{"position":[1400,-900,600],"target":[550,0,90],"zoom":2.8}},
        ]
        result.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",
                           theme="snapshot",display={"mode":"rendered"},outputs=outputs,
                           width=2400,height=900,
                           render={"padding":.08,"viewLabels":False}))
        result.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",
                           theme="snapshot",display={"mode":"solid"},outputs=details,
                           width=1400,height=1000,render={"padding":.08,"viewLabels":False}))
        result.append(dict(input=str(ROOT/"STEP"/(stem+"_Separated.step")),mode="view",
                           theme="snapshot",display={"mode":"rendered"},
                           outputs=[{"path":str(ROOT/"reviews"/f"{key}_separated.png"),
                                     "camera":{"direction":[-.25,-1,.55],
                                               "zoom":separated_frames[key]/max(separated_frames.values())}}],
                           width=2400,height=900,
                           render={"padding":.08,"viewLabels":False}))
    return result


def board(keys, views, name, cell=(1000,375)):
    w,h=cell
    out=Image.new("RGB",(w*len(views), (h+48)*len(keys)+64),"#edf2f7")
    d=ImageDraw.Draw(out)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",24)
    d.text((22,18),"HALBERD / ROUNDED-SQUARE STUDIES / geometry-only",font=font,fill="#24394a")
    for row,key in enumerate(keys):
        for col,view in enumerate(views):
            image=Image.open(ROOT/"reviews"/f"{key}_{view}.png").convert("RGB")
            image.thumbnail((w,h))
            x=col*w; y=64+row*(h+48)
            d.text((x+18,y+10),f"{STEMS[key].replace('_',' / ')} - {view.replace('_',' ')}",font=font,fill="#24394a")
            out.paste(image,(x+(w-image.width)//2,y+48+(h-image.height)//2))
    path=ROOT/"reviews"/name
    out.save(path)
    print(path)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("keys",nargs="*",default=list(STEMS))
    p.add_argument("--boards-only",action="store_true")
    args=p.parse_args()
    if not args.boards_only:
        job=ROOT/"reviews"/("snapshot_"+"".join(args.keys)+".json")
        job.write_text(json.dumps(jobs(args.keys),indent=2)+"\n")
        subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    prefix="".join(args.keys)
    board(args.keys,["side","iso"],prefix+"_Overview.png")
    board(args.keys,["top","opposite"],prefix+"_Opposed.png")
    board(args.keys,["front","rear"],prefix+"_Ends.png",(800,400))
    board(args.keys,["nose_detail","intake_detail"],prefix+"_Details.png",(1000,715))
    board(args.keys,["separated"],prefix+"_Separated.png",(1600,600))
