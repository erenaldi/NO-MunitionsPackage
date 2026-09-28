"""Independent cadgen reader checks for the six explicitly named STEP exports."""
import json
import subprocess
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
STEMS=("A_Trace","B_Chine","C_Shoulder")

if __name__ == "__main__":
    results=[]
    for stem in STEMS:
        for suffix in ("", "_Separated"):
            name=stem+suffix
            target=ROOT/"STEP"/(name+".step")
            cmd=[sys.executable,"-m","cadgen.cli","step","inspect"]
            result=subprocess.run(cmd+["validate",str(target),"--every-placement"],capture_output=True,text=True)
            if result.returncode:
                raise RuntimeError(result.stderr or result.stdout)
            data=json.loads(result.stdout)
            results.append(data)
            print(name, "PASS" if data.get("ok") else "FAIL", "failures", data.get("failureCount"),flush=True)
            (ROOT/"reviews"/"native_validation.json").write_text(json.dumps(results,indent=2)+"\n")
            if not data.get("ok"):
                raise RuntimeError(data)
            facts=subprocess.run(cmd+["refs",str(target),"--facts","--planes","--positioning"],capture_output=True,text=True,check=True)
            parsed=json.loads(facts.stdout)
            (ROOT/"reviews"/(name+"_facts.json")).write_text(json.dumps(parsed,indent=2)+"\n")
    print("All six exports pass strict every-placement validation.")
