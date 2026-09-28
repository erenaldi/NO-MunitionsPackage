"""R5 linework and rear-face appearance in rendered and solid CAD modes."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]

if __name__=="__main__":
    views={
        "context":("Selected_Intake_R5",{"direction":[.35,1,.65]},2400,850,"rendered"),
        "taper":("Selected_Intake_R5",{"direction":[0,1,1]},2400,850,"solid"),
        "profile":("Selected_Intake_R5",{"direction":[0,1,-1]},2400,850,"solid"),
        "edges":("Selected_Intake_R5",{"position":[1280,680,720],"target":[450,80,80],"zoom":1.9},1600,1100,"solid"),
        "front_solid":("Selected_Intake_R5",{"direction":[1,0,0]},1400,1400,"solid"),
        "front_rendered":("Selected_Intake_R5",{"direction":[1,0,0]},1400,1400,"rendered"),
        "booster_solid":("Selected_Intake_R5",{"position":[-2150,160,130],"target":[-1660,0,0],"zoom":1.6},1400,1100,"solid"),
        "booster_rendered":("Selected_Intake_R5",{"position":[-2150,160,130],"target":[-1660,0,0],"zoom":1.6},1400,1100,"rendered"),
        "main_solid":("Selected_Intake_R5_Separated",{"position":[-1550,170,140],"target":[-1100,0,0],"zoom":1.8},1400,1100,"solid"),
        "main_rendered":("Selected_Intake_R5_Separated",{"position":[-1550,170,140],"target":[-1100,0,0],"zoom":1.8},1400,1100,"rendered"),
        "separated":("Selected_Intake_R5_Separated",{"direction":[-.4,1,.65]},2400,850,"rendered"),
    }
    jobs=[]
    for view,(stem,camera,w,h,display) in views.items():
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",theme="snapshot",
                         display={"mode":display},width=w,height=h,
                         outputs=[{"path":str(ROOT/"reviews"/f"Intake_R5_{view}.png"),"camera":camera}],
                         render={"padding":.08,"viewLabels":False}))
    job=ROOT/"reviews"/"intake_R5_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",25)
    for title,items,w,h in (
        ("Geometry",("edges","taper","profile","context"),1200,680),
        ("Back_Faces",("front_solid","front_rendered","booster_solid","booster_rendered","main_solid","main_rendered"),1000,780),
        ("Separated",("separated",),1600,570),
    ):
        cols=2 if len(items)>1 else 1
        board=Image.new("RGB",(w*cols,90+((len(items)+cols-1)//cols)*(h+50)),"#edf2f7")
        draw=ImageDraw.Draw(board)
        draw.text((18,14),"HALBERD R5 / STRAIGHT DESIGN EDGES / UNIFORM REAR TAPER",font=font,fill="#24394a")
        draw.text((18,49),"Black rear faces only; channel and nozzle sides retain R4 materials",font=font,fill="#24394a")
        for i,view in enumerate(items):
            x=(i%cols)*w; y=90+(i//cols)*(h+50)
            draw.text((x+18,y+10),view.upper().replace("_"," "),font=font,fill="#24394a")
            image=Image.open(ROOT/"reviews"/f"Intake_R5_{view}.png").convert("RGB")
            image.thumbnail((w,h))
            board.paste(image,(x+(w-image.width)//2,y+50+(h-image.height)//2))
        out=ROOT/"reviews"/f"Intake_R5_{title}.png"
        board.save(out)
        print(out)
    paths=[ROOT/"STEP"/(s+".step") for s in ("Selected_Intake_R5","Selected_Intake_R5_Separated")]
    paths.extend(ROOT/"reviews"/f"Intake_R5_{v}.png" for v in views)
    records=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    (ROOT/"reviews"/"intake_R5_manifest.json").write_text(json.dumps(dict(revision="R5",state="concept-review",user_approved=False,artifacts=records),indent=2)+"\n")
