"""Audit actual triangulation, not only the BREP's solid-validity flag."""
import json
from pathlib import Path
import numpy as np
import trimesh
from cadgen import read_step

ROOT=Path(__file__).resolve().parent


def inspect_part(part):
    points,triangles=part.tessellate(.12,.12)
    mesh=trimesh.Trimesh(vertices=[(p.X,p.Y,p.Z) for p in points],faces=triangles,process=False)
    result=inspect_mesh(mesh,part.label)
    result["cad_volume_mm3"]=float(part.volume)
    return result


def inspect_mesh(mesh,label,digits=6):
    mesh=mesh.copy()
    mesh.merge_vertices(digits_vertex=digits,merge_tex=True,merge_norm=True)
    counts=np.bincount(mesh.edges_unique_inverse)
    boundary=mesh.edges_unique[counts==1]
    overused=mesh.edges_unique[counts>2]
    vertices=mesh.vertices[np.unique(boundary)] if len(boundary) else np.empty((0,3))
    result={"label":label,"vertices":len(mesh.vertices),"triangles":len(mesh.faces),
            "watertight":bool(mesh.is_watertight),"consistent_winding":bool(mesh.is_winding_consistent),
            "boundary_edges":len(boundary),"overused_edges":len(overused),
            "mesh_volume":float(mesh.volume)}
    if len(vertices):
        result["boundary_bounds_source_units"]=[vertices.min(axis=0).tolist(),vertices.max(axis=0).tolist()]
    return result


def main():
    model=read_step(ROOT/"Halberd_Shoulder_Hybrid.step")
    records=[inspect_part(part) for part in model.children]
    for record in records: print(json.dumps(record))
    # Native GLB combines same-color parts. Isolate one CAD solid first, so
    # touching booster/body end faces cannot produce a false non-manifold result.
    viewer=trimesh.load_scene(ROOT/"Halberd_Hybrid_BodyAudit.glb",process=False)
    viewer_records=[inspect_mesh(mesh,name,digits=8) for name,mesh in viewer.geometry.items()]
    for record in viewer_records: print("VIEWER",json.dumps(record))
    ok=all(r["watertight"] and r["consistent_winding"] and r["mesh_volume"]>0 for r in records+viewer_records)
    report={"ok":ok,"occt_tessellation_mm":.12,"angular_tolerance":.12,
            "occt_weld_decimal_places_mm":6,"viewer_weld_decimal_places_m":8,
            "parts":records,"viewer_glb_geometries":viewer_records}
    (ROOT/"Halberd_Hybrid_Mesh_Checks.json").write_text(json.dumps(report,indent=2)+"\n")
    assert ok, "Hybrid tessellation has open, non-manifold, inverted or inconsistently wound parts"


if __name__=="__main__": main()
