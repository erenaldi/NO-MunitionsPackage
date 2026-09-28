"""Review-only cameras for the unpatterned corner intake prototype."""
import json
import argparse
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--revision",choices=("R1","R2"),default="R1")
    args=parser.parse_args()
    revision=args.revision
    stem="Selected_Intake_Prototype" if revision=="R1" else "Selected_Intake_R2"
    cameras={
        "context":{"direction":[.35,1,.65]},
        "opposite":{"direction":[-.35,-1,-.65]},
        "side":{"direction":[0,1,0]},
        "top":{"preset":"top"},
        "front":{"direction":[1,0,0]},
        "rear":{"direction":[-1,0,0]},
        "mouth":{"position":[1250,680,700],"target":[570,85,85],"zoom":2.4},
        "grazing":{"position":[200,200,1250],"target":[-100,60,60],"zoom":.95},
    }
    if revision=="R2":
        cameras["aft_join"]={"position":[-300,750,750],"target":[-870,95,95],"zoom":2.1}
    jobs=[]
    for view,camera in cameras.items():
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",theme="snapshot",
                         display={"mode":"solid" if view in ("mouth","grazing","aft_join") else "rendered"},
                         outputs=[{"path":str(ROOT/"reviews"/f"Intake_{revision}_{view}.png"),"camera":camera}],
                         width=1600 if view in ("mouth","grazing","front","rear","aft_join") else 2400,
                         height=1000 if view in ("mouth","grazing","front","rear","aft_join") else 900,
                         render={"padding":.08,"viewLabels":False}))
    jobs.append(dict(input=str(ROOT/"STEP"/(stem+"_Separated.step")),mode="view",theme="snapshot",
                     display={"mode":"rendered"},
                     outputs=[{"path":str(ROOT/"reviews"/f"Intake_{revision}_separated.png"),"camera":{"direction":[-.3,1,.65]}}],
                     width=2400,height=900,render={"padding":.08,"viewLabels":False}))
    if revision=="R2":
        for view in ("context","mouth"):
            jobs.append(dict(input=str(ROOT/"STEP"/(stem+"_Covered.step")),mode="view",theme="snapshot",
                             display={"mode":"solid" if view=="mouth" else "rendered"},
                             outputs=[{"path":str(ROOT/"reviews"/f"Intake_R2_covered_{view}.png"),"camera":cameras[view]}],
                             width=1600 if view=="mouth" else 2400,height=1000 if view=="mouth" else 900,
                             render={"padding":.08,"viewLabels":False}))
    job=ROOT/"reviews"/f"intake_{revision}_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",24)
    boards=[("Overview",("context","side","top","separated")),
            ("Details",("mouth","grazing","front","rear")),("Opposite",("opposite",))]
    if revision=="R2":
        boards.extend([("Covered",("covered_context","covered_mouth")),("Aft",("aft_join",))])
    for title,views in boards:
        w,h=(1200,750) if title in ("Details","Covered","Aft") else (1200,450)
        cols=2 if len(views)>1 else 1
        rows=(len(views)+cols-1)//cols
        board=Image.new("RGB",(w*cols,(h+48)*rows+75),"#edf2f7")
        draw=ImageDraw.Draw(board)
        draw.text((18,15),f"HALBERD / {revision} ONE INTAKE PROTOTYPE / 45-degree corner aligned with A fins",font=font,fill="#24394a")
        for i,view in enumerate(views):
            x=(i%cols)*w; y=75+(i//cols)*(h+48)
            draw.text((x+18,y+8),view.upper()+" - other three intake stations intentionally absent",font=font,fill="#24394a")
            im=Image.open(ROOT/"reviews"/f"Intake_{revision}_{view}.png").convert("RGB")
            im.thumbnail((w,h))
            board.paste(im,(x+(w-im.width)//2,y+48+(h-im.height)//2))
        target=ROOT/"reviews"/f"Intake_{revision}_{title}.png"
        board.save(target)
        print(target)
