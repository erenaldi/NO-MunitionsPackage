"""True orthographic front/profile/taper views for the annotated R3 brief."""
import json
import hashlib
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]

if __name__=="__main__" and "--manifest-only" not in sys.argv:
    cameras={
        "context":{"direction":[.35,1,.65]},
        "opposite":{"direction":[-.35,-1,-.65]},
        "front":{"direction":[1,0,0]},
        "rear":{"direction":[-1,0,0]},
        # With Z-up, these two normals project local radial/tangent axes as
        # screen-up. Direction-only specifications retain true orthographic.
        "profile":{"direction":[0,1,-1]},
        "taper":{"direction":[0,1,1]},
        "mouth":{"position":[1280,680,720],"target":[600,80,80],"zoom":2.0},
        "fin_seat":{"position":[-650,700,-350],"target":[-1010,100,100],"zoom":1.5},
    }
    jobs=[]
    for view,camera in cameras.items():
        close=view in ("mouth","fin_seat","front","rear")
        jobs.append(dict(input=str(ROOT/"STEP"/"Selected_Intake_R3.step"),mode="view",theme="snapshot",
                         display={"mode":"solid" if view in ("mouth","fin_seat") else "rendered"},
                         outputs=[{"path":str(ROOT/"reviews"/f"Intake_R3_{view}.png"),"camera":camera}],
                         width=1600 if close else 2400,height=1100 if close else 850,
                         render={"padding":.08,"viewLabels":False}))
    jobs.extend([
        dict(input=str(ROOT/"STEP"/"Selected_Intake_R3_Separated.step"),mode="view",theme="snapshot",
             display={"mode":"rendered"},width=2400,height=850,
             outputs=[{"path":str(ROOT/"reviews"/"Intake_R3_separated.png"),"camera":{"direction":[-.3,1,.65]}}],
             render={"padding":.08,"viewLabels":False}),
        dict(input=str(ROOT/"STEP"/"Selected_Intake_R3_Section.step"),mode="view",theme="snapshot",
             display={"mode":"solid"},width=1400,height=1400,
             outputs=[{"path":str(ROOT/"reviews"/"Intake_R3_section.png"),"camera":{"direction":[1,0,0]}}],
             render={"padding":.08,"viewLabels":False}),
    ])
    path=ROOT/"reviews"/"intake_R3_snapshot.json"
    path.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(path)],check=True)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",25)
    packets=(
        ("Drawing_Views",("front","profile","section","taper"),1100,650),
        ("Details",("mouth","fin_seat"),1200,825),
        ("Context",("context","opposite","rear","separated"),1200,550),
    )
    for title,views,w,h in packets:
        board=Image.new("RGB",(2*w,90+((len(views)+1)//2)*(h+50)),"#edf2f7")
        draw=ImageDraw.Draw(board)
        draw.text((18,14),"HALBERD R3 / DRAWING-LED INTAKE + FIN / SINGLE STATION PROTOTYPE",font=font,fill="#24394a")
        draw.text((18,48),"Thin curved-floor mouth; taper reaches stage seam; fin sits on rear housing",font=font,fill="#24394a")
        for i,view in enumerate(views):
            x=(i%2)*w; y=90+(i//2)*(h+50)
            draw.text((x+18,y+10),view.upper().replace("_"," "),font=font,fill="#24394a")
            image=Image.open(ROOT/"reviews"/f"Intake_R3_{view}.png").convert("RGB")
            image.thumbnail((w,h))
            board.paste(image,(x+(w-image.width)//2,y+50+(h-image.height)//2))
        out=ROOT/"reviews"/f"Intake_R3_{title}.png"
        board.save(out)
        print(out)

if __name__=="__main__":
    checks=ROOT/"reviews"/"intake_R3_checks.json"
    assert json.loads(checks.read_text())["ok"],"Cannot publish failed/incomplete checks"
    targets=[ROOT/"STEP"/(name+".step") for name in
             ("Selected_Intake_R3","Selected_Intake_R3_Separated","Selected_Intake_R3_Section")]
    targets.extend(ROOT/"reviews"/f"Intake_R3_{view}.png" for view in
                   ("context","opposite","front","rear","profile","taper","mouth","fin_seat",
                    "separated","section","Drawing_Views","Details","Context"))
    targets.append(checks)
    targets.extend(ROOT/"src"/name for name in
                   ("intake_r3_shapes.py","intake_r3.py","intake_r3_separated.py","intake_r3_section.py",
                    "check_intake_r3.py","review_intake_r3.py","study_shapes.py","check_intake_revision.py"))
    entries=[]
    for path in targets:
        if path.suffix==".png":
            with Image.open(path) as image:
                image.verify()
        entries.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest=dict(revision="R3",state="concept-review",user_approved=False,intakes_prototyped=1,
                  contract="R3_DRAWING_CONTRACT.md",artifacts=entries)
    output=ROOT/"reviews"/"intake_R3_manifest.json"
    output.write_text(json.dumps(manifest,indent=2)+"\n")
    print(f"Published {len(entries)} artifact/source hashes: {output}")
