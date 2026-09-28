"""Contact sheets of the declared hybrid snapshot packet."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps


def main():
    root=Path(__file__).resolve().parent
    jobs=json.loads((root/"halberd_shoulder_hybrid_snapshot_job.json").read_text())
    names=[out["path"] for job in jobs for out in job["outputs"]]
    for start in range(0,len(names),9):
        sheet=Image.new("RGB",(1800,1440),"white")
        draw=ImageDraw.Draw(sheet)
        for i,name in enumerate(names[start:start+9]):
            x,y=(i%3)*600,(i//3)*480
            with Image.open(root/name) as image:
                tile=ImageOps.contain(image.convert("RGB"),(600,450))
            sheet.paste(tile,(x,y))
            draw.text((x+10,y+458),name,fill="black")
        path=root/f"Halberd_Hybrid_Board_{start//9+1}.png"
        sheet.save(path)
        print(path)


if __name__=="__main__": main()
