"""Four-station review plus fresh saved-Kris detail reference views."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


if __name__=="__main__":
    views={
        "R12_iso":("halberd_r12",[.35,1,.65],2200,850),
        "R12_opposite":("halberd_r12",[-.35,-1,-.65],2200,850),
        "R12_front":("halberd_r12",[1,0,0],1200,1200),
        "R12_separated":("halberd_r12_separated",[.3,1,.65],2200,850),
        "Kris_detail_oblique":("kris_detail_reference",[.25,-.6,1],1600,1100),
        "Kris_detail_top":("kris_detail_reference",[0,0,1],1600,1100),
    }
    jobs=[]
    for name,(stem,direction,w,h) in views.items():
        camera={"projection":"orthographic","direction":direction}
        if direction==[0,0,1]:
            camera["up"]=[0,1,0]
        jobs.append(dict(input=str(ROOT/"STEP"/(stem+".step")),mode="view",
                         display={"mode":"shaded_edges"},output={"padding":.08,"viewLabels":False},
                         outputs=[dict(path=str(ROOT/"reviews"/(name+".png")),camera=camera,width=w,height=h)]))
    job=ROOT/"reviews"/"r12_reference_snapshot.json"
    job.write_text(json.dumps(jobs,indent=2)+"\n")
    subprocess.run([sys.executable,"-m","cadgen.cli","step","snapshot","--job",str(job)],check=True)
