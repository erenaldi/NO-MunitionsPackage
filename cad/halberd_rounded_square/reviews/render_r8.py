"""R8 complete-layout review using the cadgen 0.6.6 snapshot contract."""
import hashlib
import argparse
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]

if __name__=="__main__":
    views={
        "iso":("Selected_Halberd_R8",{"direction":[.35,1,.65]},2400,900,"shaded"),
        "opposite":("Selected_Halberd_R8",{"direction":[-.35,-1,-.65]},2400,900,"shaded"),
        "side":("Selected_Halberd_R8",{"direction":[0,1,-1]},2400,900,"shaded_edges"),
        "taper":("Selected_Halberd_R8",{"direction":[0,1,1]},2400,900,"shaded_edges"),
        "front":("Selected_Halberd_R8",{"direction":[1,0,0]},1400,1400,"shaded"),
        "rear":("Selected_Halberd_R8",{"direction":[-1,0,0]},1400,1400,"shaded"),
        "booster_shift":("Selected_Halberd_R8",{"projection":"orthographic","direction":[.2,1,-.8],"target":[-1370,0,0],"orthographicHalfHeight":250.},1600,1100,"shaded_edges"),
        "separated":("Selected_Halberd_R8_Separated",{"direction":[-.4,1,.65]},2400,900,"shaded"),
    }
    parser=argparse.ArgumentParser()
    parser.add_argument("--only",choices=tuple(views))
    args=parser.parse_args()
    jobs=[]
    for view,(stem,camera,w,h,mode) in views.items():
        if args.only and view!=args.only:
            continue
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",display={"mode":mode},
                         output={"padding":.08,"viewLabels":False},
                         outputs=[{"path":str(ROOT/"reviews"/f"Halberd_R8_{view}.png"),"camera":camera,"width":w,"height":h}]))
    job=ROOT/"reviews"/("halberd_R8_snapshot"+("_"+args.only if args.only else "")+".json")
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",25)
    for title,names,w,h in (
        ("Overview",("iso","opposite","side","taper"),1200,450),
        ("Ends",("front","rear"),900,900),
        ("Stages",("booster_shift","separated"),1200,825),
    ):
        board=Image.new("RGB",(2*w,90+((len(names)+1)//2)*(h+50)),"#edf2f7")
        draw=ImageDraw.Draw(board)
        draw.text((18,14),"HALBERD R8 / FOUR COMPLETE STATIONS / BOOSTER FINS +170 mm FORWARD",font=font,fill="#24394a")
        draw.text((18,49),"45 / 135 / 225 / 315 degrees - approved intake, main-fin and booster-fin geometry",font=font,fill="#24394a")
        for i,view in enumerate(names):
            x=(i%2)*w; y=90+(i//2)*(h+50)
            draw.text((x+18,y+10),view.upper().replace("_"," "),font=font,fill="#24394a")
            image=Image.open(ROOT/"reviews"/f"Halberd_R8_{view}.png").convert("RGB")
            image.thumbnail((w,h))
            board.paste(image,(x+(w-image.width)//2,y+50+(h-image.height)//2))
        output=ROOT/"reviews"/f"Halberd_R8_{title}.png"
        board.save(output)
        print(output)
    paths=[ROOT/"STEP"/(s+suffix) for s in ("Selected_Halberd_R8","Selected_Halberd_R8_Separated") for suffix in (".step",".step.json")]
    paths.extend(ROOT/"reviews"/f"Halberd_R8_{v}.png" for v in views)
    records=[dict(path=p.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths]
    (ROOT/"reviews"/"halberd_R8_manifest.json").write_text(json.dumps(dict(revision="R8",runtime="cadgen 0.6.6",state="cad-review",user_approved=False,artifacts=records),indent=2)+"\n")
