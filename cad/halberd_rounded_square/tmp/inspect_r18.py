import sys
from pathlib import Path
sys.path.insert(0, "src")
from halberd_r18_access_shapes import load_saved_parts
scene, saved = load_saved_parts(Path("STEP/halberd_r18_access.step"))
print("doc hash", scene.document_hash, len(saved), "parts")
rows=[]
for label, sh in saved.items():
    b = sh.bounding_box()
    rows.append((label, b.min.X, b.max.X, b.min.Y, b.max.Y, b.min.Z, b.max.Z, sh.volume))
rows.sort(key=lambda r: -r[1])
for r in rows:
    print(f"{r[0]:46s} X[{r[1]:9.2f},{r[2]:9.2f}] Y[{r[3]:8.2f},{r[4]:8.2f}] Z[{r[5]:8.2f},{r[6]:8.2f}] V={r[7]:12.1f}")
