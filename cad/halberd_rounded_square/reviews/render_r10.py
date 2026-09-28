"""R10 review of the single continuous intake, split at the stage seam."""
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]


def render(revision=10):
    views={
        "side":("halberd_r10_focus",[0,-1,0],None,1800,800),
        "oblique":("halberd_r10_focus",[.3,-1,.6],None,1800,850),
        "top":("halberd_r10_focus",[0,0,1],[0,1,0],1800,650),
        "whole":("halberd_r10",[.35,1,.65],None,2200,850),
        "separated":("halberd_r10_separated",[.3,1,.65],None,2200,850),
    }
    jobs=[]
    for name,(stem,direction,up,w,h) in views.items():
        stem=stem.replace("r10",f"r{revision}")
        camera={"projection":"orthographic","direction":direction}
        if up:
            camera["up"]=up
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",
                         display={"mode":"shaded_edges"},output={"padding":.08,"viewLabels":False},
                         outputs=[dict(path=str(ROOT/"reviews"/f"Halberd_R{revision}_{name}.png"),
                                       camera=camera,width=w,height=h)]))
    job=ROOT/"reviews"/f"halberd_R{revision}_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    board=Image.new("RGB",(1800,2500),"#edf2f7")
    draw=ImageDraw.Draw(board)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",28)
    title=("ORIGINAL INTAKE LENGTHENED, THEN SPLIT AT THE STAGE JOINT" if revision==10
           else "INTAKE END ALIGNED TO FIN RIDGE / HEIGHTS PRESERVED")
    draw.text((20,15),f"HALBERD R{revision} / {title}",font=font,fill="#24394a")
    y=65
    for name in ("side","oblique","top"):
        draw.text((20,y),name.upper(),font=font,fill="#24394a")
        image=Image.open(ROOT/"reviews"/f"Halberd_R{revision}_{name}.png").convert("RGB")
        board.paste(image,(0,y+35))
        y+=image.height+45
    board.save(ROOT/"reviews"/f"Halberd_R{revision}_Continuous_Intake.png")
    print(ROOT/"reviews"/f"Halberd_R{revision}_Continuous_Intake.png")


if __name__=="__main__":
    render()
