"""Closed review GLB using OCCT tessellation rather than the failing STEP viewport mesher.

Does not repair/fill arbitrary mesh holes, edit CAD surfaces, or change Unity assets.
Every source part and every reloaded GLB mesh must already be closed and wound.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
import trimesh
from cadgen import read_step

ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/"Halberd_Shoulder_Hybrid.step"
OUTPUT=ROOT/"Halberd_Shoulder_Hybrid_Closed.glb"


def checked(mesh,label):
    test=mesh.copy()
    test.merge_vertices(digits_vertex=8,merge_tex=True,merge_norm=True)
    assert test.is_watertight, f"{label}: open mesh"
    assert test.is_winding_consistent, f"{label}: inconsistent winding"
    assert test.volume>0, f"{label}: inverted/empty solid"
    return {"label":label,"vertices":len(test.vertices),"triangles":len(test.faces),
            "watertight":True,"consistent_winding":True,"volume_m3":float(test.volume)}


def export_closed(source,output,expected_count,report_path,expected_length=None):
    model=read_step(source)
    scene=trimesh.Scene()
    expected=set()
    for part in model.children:
        assert part.label not in expected
        expected.add(part.label)
        points,faces=part.tessellate(.12,.12)
        # Same geometric edge points must quantize identically in float32 GLB.
        cad=np.round([(v.X,v.Y,v.Z) for v in points],6)
        # glTF is Y-up; preserve CAD's +X-forward / +Z-dorsal appearance on import.
        vertices=np.column_stack((cad[:,0],cad[:,2],-cad[:,1]))*.001
        mesh=trimesh.Trimesh(vertices=vertices,faces=faces,process=False)
        checked(mesh,part.label)
        rgba=np.clip(np.round(np.asarray(tuple(part.color))*255),0,255).astype(np.uint8)
        material=trimesh.visual.material.PBRMaterial(name=part.label,
            baseColorFactor=rgba,metallicFactor=.08,roughnessFactor=.72,doubleSided=False)
        mesh.visual=trimesh.visual.TextureVisuals(material=material)
        scene.add_geometry(mesh,node_name=part.label,geom_name=part.label)
    # Validate all source meshes before publishing, then independently reload bytes.
    scene.export(output,file_type="glb",include_normals=True)
    loaded=trimesh.load_scene(output,process=False)
    assert set(loaded.geometry)==expected, "GLB lost semantic mesh labels"
    records=[checked(mesh,label) for label,mesh in loaded.geometry.items()]
    assert len(records)==expected_count
    if expected_length is not None:
        assert abs(loaded.bounds[1,0]-loaded.bounds[0,0]-expected_length)<1e-6
    report={"ok":True,"source":source.name,"source_sha256":hashlib.sha256(source.read_bytes()).hexdigest(),
            "output":output.name,"output_sha256":hashlib.sha256(output.read_bytes()).hexdigest(),
            "backend":"OCCT / build123d; native GLB review bypasses STEP viewport tessellation",
            "basis":"CAD (X,Y,Z) mm -> glTF (X,Z,-Y) metres; scale 0.001",
            "chord_tolerance_mm":.12,"angular_tolerance_rad":.12,"parts":records}
    report_path.write_text(json.dumps(report,indent=2)+"\n")
    print(f"PASS: {len(records)} labeled GLB meshes reload closed, consistently wound and positive-volume; {sum(r['triangles'] for r in records)} triangles.")
    print(output)


if __name__=="__main__":
    export_closed(SOURCE,OUTPUT,19,ROOT/"Halberd_Hybrid_ClosedMesh_Report.json",3.367)
    from review_halberd_shoulder_hybrid import intakes
    intakes()
    export_closed(ROOT/"Halberd_Shoulder_Hybrid_Intakes.step",
                  ROOT/"Halberd_Shoulder_Hybrid_Intakes_Closed.glb",7,
                  ROOT/"Halberd_Hybrid_Intakes_ClosedMesh_Report.json")
