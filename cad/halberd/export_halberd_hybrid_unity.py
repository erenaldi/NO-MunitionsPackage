"""Deterministic hybrid authoring meshes; explicit Unity basis, source labels, interior slots.

Writes only Assets/Blueprinter/Mods/HalberdHybrid/Models, not the shipped HalberdMod.
The body remains one closed mesh with two material submeshes (paint / intake interior).
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from cadgen import read_step
from generate_halberd_shoulder_hybrid import intake_passage, ANGLES
from halberd_concept_shapes import clock

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"Halberd_Shoulder_Hybrid.step"
DEST=ROOT.parent/"unity/BlueprinterEditor/Blueprinter-Editor/Assets/Blueprinter/Mods/HalberdHybrid/Models"


def main():
    model=read_step(SOURCE)
    expected={"sustainer_body","booster_body","radome","sustainer_nozzle","booster_nozzle","mount_1","mount_2"}
    expected.update(f"{prefix}_{i}" for prefix in ("intake_floor","sustainer_fin","booster_fin") for i in range(1,5))
    assert len(model.children)==len(expected) and {p.label for p in model.children}==expected
    passage=intake_passage()
    passages=[clock(passage,a).solids()[0] for a in ANGLES]
    records=[]
    for part in model.children:
        part.tessellate(.12,.12)  # seed shared-edge triangulations before extracting faces
        vertices=[]; triangles=[]; outer=[]; inner=[]
        for face in part.faces():
            points,faces=face.tessellate(.12,.12)
            if not len(faces):
                raise ValueError(f"Untessellated face in {part.label}")
            points=np.array([(v.X,v.Y,v.Z) for v in points])
            local=np.asarray(faces,dtype=int)
            tri=points[local]
            cross=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0])
            areas=np.linalg.norm(cross,axis=1)
            assert np.all(areas>1e-12), part.label
            largest=int(np.argmax(areas))
            witness=tri[largest].mean(axis=0)+cross[largest]/areas[largest]*.5
            interior=part.label=="sustainer_body" and any(p.is_inside(tuple(witness)) for p in passages)
            offset=len(vertices)
            ids=(local+offset).reshape(-1).tolist()
            vertices.extend(points.tolist()); triangles.extend(ids)
            (inner if interior else outer).extend(ids)
        mesh=trimesh.Trimesh(vertices=vertices,faces=np.asarray(triangles).reshape(-1,3),process=False)
        check=mesh.copy(); check.merge_vertices(digits_vertex=6)
        assert check.is_watertight and check.is_winding_consistent and check.volume>0, part.label
        points=np.asarray(vertices)[:,[1,2,0]]*.001
        normals=np.asarray(mesh.vertex_normals)[:,[1,2,0]]
        records.append({"label":part.label,"vertices":points.reshape(-1).tolist(),
                        "normals":normals.reshape(-1).tolist(),"exterior":outer,"interior":inner})
    body=next(p for p in records if p["label"]=="sustainer_body")
    assert len(body["interior"])>300 and len(body["exterior"])>300
    count=sum((len(p["interior"])+len(p["exterior"]))//3 for p in records)
    assert count<=75000
    payload={"sourceSha256":hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
             "triangleCount":count,"parts":records}
    DEST.mkdir(parents=True,exist_ok=True)
    (DEST/"HalberdHybridMeshData.json").write_text(json.dumps(payload,separators=(",",":"))+"\n")
    print(f"PASS: {len(records)} closed hybrid parts, {count} triangles, {len(body['interior'])//3} body-interior triangles; Unity basis (Y,Z,X)*.001.")
    print(DEST/"HalberdHybridMeshData.json")


if __name__=="__main__": main()
