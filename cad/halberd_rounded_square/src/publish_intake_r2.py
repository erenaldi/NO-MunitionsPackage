"""Collect explicit R2 artifact facts, identity hashes and a matched progress board."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
FILES=("Selected_Intake_R2","Selected_Intake_R2_Covered","Selected_Intake_R2_Separated")
VIEWS=("context","opposite","side","top","front","rear","mouth","grazing",
       "aft_join","separated","covered_context","covered_mouth")

if __name__=="__main__":
    manifest={"revision":"R2","state":"concept-review","user_approved":False,"artifacts":[]}
    for name in FILES:
        path=ROOT/"STEP"/(name+".step")
        result=subprocess.run([sys.executable,"-m","cadgen.cli","step","inspect","refs",str(path),
                               "--facts","--planes","--positioning"],capture_output=True,text=True,check=True)
        facts=json.loads(result.stdout)
        (ROOT/"reviews"/(name+"_facts.json")).write_text(json.dumps(facts,indent=2)+"\n")
        manifest["artifacts"].append({"path":path.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    for view in VIEWS:
        path=ROOT/"reviews"/f"Intake_R2_{view}.png"
        with Image.open(path) as image:
            image.verify()
        manifest["artifacts"].append({"path":path.relative_to(ROOT).as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()})
    (ROOT/"reviews"/"intake_R2_manifest.json").write_text(json.dumps(manifest,indent=2)+"\n")
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",26)
    board=Image.new("RGB",(2400,1700),"#edf2f7")
    draw=ImageDraw.Draw(board)
    draw.text((20,15),"HALBERD / R1 TO R2 / SAME NOSE, FINS AND 45-DEGREE INTAKE STATION",font=font,fill="#24394a")
    for col,revision in enumerate(("R1","R2")):
        x=col*1200
        draw.text((x+20,65),revision+" / full context",font=font,fill="#24394a")
        image=Image.open(ROOT/"reviews"/f"Intake_{revision}_context.png").convert("RGB")
        image.thumbnail((1200,450))
        board.paste(image,(x,110))
        draw.text((x+20,600),revision+" / inlet and forward fairing",font=font,fill="#24394a")
        image=Image.open(ROOT/"reviews"/f"Intake_{revision}_mouth.png").convert("RGB")
        image.thumbnail((1200,750))
        board.paste(image,(x,650))
    draw.text((20,1490),"R2: wider structured mouth, covered-reference view, aft-rising strake, fin-leading-edge seat.",font=font,fill="#24394a")
    draw.text((20,1540),"One intake only. Other three stations await visual approval. No engine/runtime claim.",font=font,fill="#24394a")
    output=ROOT/"reviews"/"Intake_R2_Progression.png"
    board.save(output)
    print("R2: three STEP fact reports, 15 artifact hashes, 12 readable snapshots.")
    print(output)
