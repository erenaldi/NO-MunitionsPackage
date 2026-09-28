"""R4 interior depth/material evidence and explicit artifact manifest."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]

if __name__=="__main__":
    views={
        "context":("Selected_Intake_R4",{"direction":[.35,1,.65]},2400,850),
        "front":("Selected_Intake_R4",{"direction":[1,0,0]},1400,1400),
        "inlet":("Selected_Intake_R4",{"position":[1280,680,720],"target":[600,80,80],"zoom":2.0},1600,1100),
        "down_channel":("Selected_Intake_R4",{"position":[1000,86,86],"target":[350,86,86],"zoom":1.6},1600,1100),
        "booster_nozzle":("Selected_Intake_R4",{"position":[-2150,160,130],"target":[-1660,0,0],"zoom":1.6},1400,1100),
        "main_nozzle":("Selected_Intake_R4_Separated",{"position":[-1550,170,140],"target":[-1100,0,0],"zoom":1.8},1400,1100),
        "separated":("Selected_Intake_R4_Separated",{"direction":[-.4,1,.65]},2400,850),
        "cutaway":("Selected_Intake_R4_Cutaway",{"direction":[0,1,0]},2400,750),
    }
    jobs=[]
    for view,(stem,camera,w,h) in views.items():
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",theme="snapshot",
                         display={"mode":"rendered"},width=w,height=h,
                         outputs=[{"path":str(ROOT/"reviews"/f"Intake_R4_{view}.png"),"camera":camera}],
                         render={"padding":.08,"viewLabels":False}))
    job=ROOT/"reviews"/"intake_R4_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",25)
    for title,items,w,h in (
        ("Nozzles",("booster_nozzle","main_nozzle"),1100,865),
        ("Intake",("inlet","down_channel","front","cutaway"),1100,760),
        ("Context",("context","separated"),1200,425),
    ):
        board=Image.new("RGB",(w*2,90+((len(items)+1)//2)*(h+50)),"#edf2f7")
        draw=ImageDraw.Draw(board)
        draw.text((18,14),"HALBERD R4 / EXTENDED CHANNEL AND RECESSED CHARCOAL INTERIORS",font=font,fill="#24394a")
        draw.text((18,49),"Approved R3 exterior retained / one intake station",font=font,fill="#24394a")
        for i,view in enumerate(items):
            x=(i%2)*w; y=90+(i//2)*(h+50)
            draw.text((x+18,y+10),view.upper().replace("_"," "),font=font,fill="#24394a")
            image=Image.open(ROOT/"reviews"/f"Intake_R4_{view}.png").convert("RGB")
            image.thumbnail((w,h))
            board.paste(image,(x+(w-image.width)//2,y+50+(h-image.height)//2))
        out=ROOT/"reviews"/f"Intake_R4_{title}.png"
        board.save(out)
        print(out)
    entries=[]
    targets=[ROOT/"STEP"/(stem+".step") for stem in
             ("Selected_Intake_R4","Selected_Intake_R4_Separated","Selected_Intake_R4_Cutaway")]
    targets.extend(ROOT/"reviews"/f"Intake_R4_{view}.png" for view in views)
    for target in targets:
        entries.append(dict(path=target.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
    (ROOT/"reviews"/"intake_R4_manifest.json").write_text(json.dumps(dict(revision="R4",state="concept-review",user_approved=False,artifacts=entries),indent=2)+"\n")
