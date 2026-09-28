"""Review the actual low-profile fin silhouette and its mounted context."""
import json
import subprocess
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]

if __name__=="__main__":
    specs={
        "fin_side":("Selected_Booster_Fin_R7",{"direction":[0,-1,0]},1600,700,"solid"),
        "fin_iso":("Selected_Booster_Fin_R7",{"direction":[.4,-1,.6]},1600,900,"rendered"),
        "mounted":("Selected_Halberd_R7",{"position":[-1000,650,-350],"target":[-1510,95,95],"zoom":1.3},1600,1100,"solid"),
        "profile":("Selected_Halberd_R7",{"direction":[0,1,-1]},2400,850,"solid"),
        "rear":("Selected_Halberd_R7",{"direction":[-1,0,0]},1400,1400,"rendered"),
        "context":("Selected_Halberd_R7",{"direction":[.35,1,.65]},2400,850,"rendered"),
        "opposite":("Selected_Halberd_R7",{"direction":[-.35,-1,-.65]},2400,850,"rendered"),
        "separated":("Selected_Halberd_R7_Separated",{"direction":[-.4,1,.65]},2400,850,"rendered"),
    }
    jobs=[]
    for view,(stem,camera,w,h,display) in specs.items():
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",theme="snapshot",
                         display={"mode":display},width=w,height=h,
                         outputs=[{"path":str(ROOT/"reviews"/f"Booster_R7_{view}.png"),"camera":camera}],
                         render={"padding":.08,"viewLabels":False}))
    job=ROOT/"reviews"/"booster_R7_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
    font=ImageFont.truetype("C:/Windows/Fonts/arial.ttf",25)
    for title,items in (("Fin",("fin_side","fin_iso","mounted","rear")),
                        ("Context",("context","profile","opposite","separated"))):
        w,h=1100,650
        board=Image.new("RGB",(2*w,1490),"#edf2f7")
        draw=ImageDraw.Draw(board)
        draw.text((18,14),"HALBERD R7 / LOW-PROFILE TRAPEZOID / ONE BOOSTER FIN PROTOTYPE",font=font,fill="#24394a")
        draw.text((18,49),"295 mm root / 220 mm centered tip / 53 mm height; other three fins retained for context",font=font,fill="#24394a")
        for i,view in enumerate(items):
            x=(i%2)*w; y=90+(i//2)*(h+50)
            draw.text((x+18,y+10),view.upper(),font=font,fill="#24394a")
            image=Image.open(ROOT/"reviews"/f"Booster_R7_{view}.png").convert("RGB")
            image.thumbnail((w,h))
            board.paste(image,(x+(w-image.width)//2,y+50+(h-image.height)//2))
        out=ROOT/"reviews"/f"Booster_R7_{title}.png"
        board.save(out)
        print(out)
