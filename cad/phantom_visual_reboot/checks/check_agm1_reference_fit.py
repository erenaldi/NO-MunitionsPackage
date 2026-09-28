"""Static donor-pylon surface check at the unchanged mounted-missile origin.

Reference meshes are not assumed watertight; report intersection AREA, not a
fabricated penetration volume. No model or runtime placement is modified.
"""
import json
import hashlib
from pathlib import Path
import numpy as np
import build123d as bd
from cadgen import read_scene
from OCP.BRepClass3d import BRepClass3d_SolidClassifier
from OCP.gp import gp_Pnt
from OCP.TopAbs import TopAbs_IN

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT/'reference/agm1_mount'


def main():
    manifest = json.loads((REF/'manifest.json').read_text(encoding='utf-8'))
    assert manifest['extracted'] and len(manifest['roots']) == 1
    nodes = {n['path']:n for n in manifest['roots'][0]['nodes']}
    mount = nodes['AGM1_single/pylon/agm1']
    pylon = nodes['AGM1_single/pylon']
    assert pylon['renderer_present'] and pylon['renderer_enabled'] == [True] and len(pylon['meshes']) == 1
    mesh_path = REF/pylon['meshes'][0]['reference_file']
    mesh_bytes = mesh_path.read_bytes()
    mesh_hash = hashlib.sha256(mesh_bytes).hexdigest()
    assert mesh_hash == pylon['meshes'][0]['reference_sha256']
    raw = json.loads(mesh_bytes)
    world = np.array(raw['vertices_mount_root_unity_m'],dtype=float)
    inverse = np.linalg.inv(np.array(mount['local_to_mount_root'],dtype=float))
    local = (inverse[:3,:3] @ world.T).T + inverse[:3,3]
    # Native Unity (+Z forward,+Y up,+X lateral) to CAD (+X,+Z,+Y).
    points = local[:,[2,0,1]]*1000.
    path = ROOT/'STEP/S_AftExhaust_R1_Stowed.step'
    parts = {o.label:o.shape() for o in read_scene(path).leaves()}
    boxes = {n:p.bounding_box() for n,p in parts.items()}
    classifiers = {n:BRepClass3d_SolidClassifier(p.wrapped) for n,p in parts.items()}
    hits = {}
    degenerate = 0
    for indices in raw['triangles']:
        tri = points[indices]
        lo,hi = tri.min(axis=0),tri.max(axis=0)
        candidates = [n for n,b in boxes.items() if all(lo[k] <= tuple(b.max)[k] and hi[k] >= tuple(b.min)[k] for k in range(3))]
        if not candidates:
            continue
        if np.linalg.norm(np.cross(tri[1]-tri[0],tri[2]-tri[0])) < 1e-9:
            degenerate += 1
            continue
        face = bd.Face(bd.Wire.make_polygon([tuple(v) for v in tri],close=True))
        for name in candidates:
            common = face & parts[name]
            area = 0. if common is None else float(common.area)
            if area > 1e-6:
                entry = hits.setdefault(name,{'triangle_count':0,'intersection_area_mm2':0.})
                entry['triangle_count'] += 1
                entry['intersection_area_mm2'] += area
                if 'strict_interior_witness_CAD_mm' not in entry:
                    for patch in common.faces():
                        point = patch.center()
                        classifiers[name].Perform(gp_Pnt(point.X,point.Y,point.Z),1e-7)
                        if classifiers[name].State() == TopAbs_IN:
                            entry['strict_interior_witness_CAD_mm'] = [point.X,point.Y,point.Z]
                            break
    max_z = max(b.max.Z for b in boxes.values())
    min_z = float(points[:,2].min())
    report = {
        'scope':'Actual extracted donor pylon surface versus saved stowed candidate at the unchanged donor missile-local origin; aircraft/bay clearance not assessed.',
        'source_manifest':'reference/agm1_mount/manifest.json','candidate_step':str(path.relative_to(ROOT)),
        'pylon_reference_sha256':mesh_hash,'candidate_step_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'candidate_component_count':len(parts),'pylon_mesh_name':raw['mesh_name'],
        'pylon_vertex_count':len(points),'pylon_triangle_count':len(raw['triangles']),
        'axis_map':'CAD X=Unity Z, CAD Y=Unity X, CAD Z=Unity Y, metres to mm, after inverse mounted-missile transform',
        'pylon_bounds_candidate_CAD_mm':[points.min(axis=0).tolist(),points.max(axis=0).tolist()],
        'degenerate_triangles_ignored':degenerate,'surface_intersections':hits,
        'static_pylon_surface_check_passed':not hits,
        'candidate_max_z_mm':float(max_z),'pylon_min_z_mm':min_z,
        'vertical_bbox_overlap_mm':float(max(0,max_z-min_z)),
        'unapplied_candidate_lowering_for_1mm_vertical_bbox_gap_mm':float(max(0,max_z-min_z+1)),
        'placement_change_applied':False,
        'limits':'Surface-area evidence, not closed-volume penetration; no donor replacement or game installation; final attachment offset and real aircraft fit pending.'}
    (ROOT/'reviews/agm1_reference_fit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    (REF/'pylon_candidate_frame.json').write_text(json.dumps({'vertices_CAD_mm':points.tolist(),'triangles':raw['triangles']},separators=(',',':'))+'\n',encoding='utf-8')
    print(json.dumps(report,indent=2))
    if hits:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
