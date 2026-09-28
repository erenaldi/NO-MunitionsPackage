"""Matched R5/R6 plan-view evidence, with a crop preserving the same pixel scale."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]

if __name__=="__main__":
    specs={
        "taper":("Selected_Intake_R6",{"direction":[0,1,1]},2400,850,"solid"),
        "R5_comparison":("Selected_Intake_R5",{"direction":[0,1,1]},2400,850,"solid"),
        "profile":("Selected_Intake_R6",{"direction":[0,1,-1]},2400,850,"solid"),
        "context":("Selected_Intake_R6",{"direction":[.35,1,.65]},2400,850,"rendered"),
        "opposite":("Selected_Intake_R6",{"direction":[-.35,-1,-.65]},2400,850,"rendered"),
        "front":("Selected_Intake_R6",{"direction":[1,0,0]},1400,1400,"solid"),
        "rear":("Selected_Intake_R6",{"direction":[-1,0,0]},1400,1400,"rendered"),
        "edges":("Selected_Intake_R6",{"position":[-100,2000,2000],"target":[-470,90,90],"zoom":2.1},1800,1100,"solid"),
        "separated":("Selected_Intake_R6_Separated",{"direction":[-.4,1,.65]},2400,850,"rendered"),
    }
    jobs=[]
    for view,(stem,camera,w,h,display) in specs.items():
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",theme="snapshot",
                         display={"mode":display},width=w,height=h,
                         outputs=[{"path":str(ROOT/"reviews"/f"Intake_R6_{view}.png"),"camera":camera}],
                         render={"padding":.08,"viewLabels":False}))
    job=ROOT/"reviews"/"intake_R6_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",26)
    board=Image.new("RGB",(2000,1270),"#edf2f7")
    draw=ImageDraw.Draw(board)
    draw.text((22,18),"HALBERD R6 / BROAD FIRST, AGGRESSIVE NARROWING NEAR THE SEAM",font=font,fill="#24394a")
    for row,(view,label) in enumerate((("R5_comparison","R5 / prior linear taper"),("taper","R6 / controlled late curved taper"))):
        image=Image.open(ROOT/"reviews"/f"Intake_R6_{view}.png").convert("RGB")
        # Same source camera, image dimensions and crop: no shape-specific warping.
        crop=image.crop((1010,285,1930,565))
        crop=crop.resize((1840,560),Image.Resampling.LANCZOS)
        y=65+row*580
        draw.text((22,y),label,font=font,fill="#24394a")
        board.paste(crop,(80,y+38))
    out=ROOT/"reviews"/"Intake_R6_Comparison.png"
    board.save(out)
    print(out)
    for title,items,w,h in (
        ("Geometry",("taper","profile","edges","context"),1200,640),
        ("Coverage",("front","rear","opposite","separated"),1100,650),
    ):
        board=Image.new("RGB",(w*2,90+((len(items)+1)//2)*(h+50)),"#edf2f7")
        draw=ImageDraw.Draw(board)
        draw.text((18,14),"HALBERD R6 / CUBIC LATE TAPER / ONE INTAKE STATION",font=font,fill="#24394a")
        draw.text((18,49),"Straight inlet, unchanged side-height profile and black backs",font=font,fill="#24394a")
        for i,view in enumerate(items):
            x=(i%2)*w; y=90+(i//2)*(h+50)
            draw.text((x+18,y+10),view.upper(),font=font,fill="#24394a")
            image=Image.open(ROOT/"reviews"/f"Intake_R6_{view}.png").convert("RGB")
            image.thumbnail((w,h))
            board.paste(image,(x+(w-image.width)//2,y+50+(h-image.height)//2))
        out=ROOT/"reviews"/f"Intake_R6_{title}.png"
        board.save(out)
        print(out)
    paths=[ROOT/"STEP"/(stem+".step") for stem in ("Selected_Intake_R6","Selected_Intake_R6_Separated")]
    paths.extend(ROOT/"reviews"/f"Intake_R6_{view}.png" for view in specs)
    records=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    (ROOT/"reviews"/"intake_R6_manifest.json").write_text(json.dumps(dict(revision="R6",state="concept-review",user_approved=False,artifacts=records),indent=2)+"\n")
