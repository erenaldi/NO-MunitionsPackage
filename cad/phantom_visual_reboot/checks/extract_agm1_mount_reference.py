"""Read installed donor mount assets; export reference-only native Unity geometry."""
import hashlib
import json
from pathlib import Path
import numpy as np
import UnityPy
from UnityPy.helpers.MeshHelper import MeshHandler

ROOT = Path(__file__).resolve().parents[1]
GAME = Path(r'C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option\NuclearOption_Data')
SOURCE = GAME/'resources.assets'
OUT = ROOT/'reference'/'agm1_mount'


def xyz(v):
    return [float(v.x),float(v.y),float(v.z)]


def matrix(t):
    q = t.m_LocalRotation
    x,y,z,w = float(q.x),float(q.y),float(q.z),float(q.w)
    n = x*x+y*y+z*z+w*w
    if abs(n-1)>1e-4:
        raise ValueError(f'Non-unit transform quaternion: {n}')
    r = np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],
                  [2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],
                  [2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
    result = np.eye(4)
    result[:3,:3] = r @ np.diag(xyz(t.m_LocalScale))
    result[:3,3] = xyz(t.m_LocalPosition)
    return result


def component_pointers(go):
    return [(item.component if hasattr(item,'component') else item[1])
            for item in go.m_Component]


def main():
    UnityPy.config.FALLBACK_UNITY_VERSION = '2022.3.62f2'
    env = UnityPy.load(str(SOURCE))
    matches = []
    for obj in env.objects:
        if obj.type.name == 'GameObject':
            go = obj.read()
            if go.m_Name == 'AGM1_single':
                matches.append((obj,go))
    with SOURCE.open('rb') as stream:
        source_hash = hashlib.file_digest(stream,'sha256').hexdigest()
    report = {'source':str(SOURCE),'source_sha256':source_hash,
              'target':'AGM1_single','matching_roots':len(matches),
              'coordinate_contract':'Unreflected native Unity XYZ in metres; matrices map local to mount-root space. Reference only, not distributable game art.',
              'roots':[], 'errors':[]}
    OUT.mkdir(parents=True,exist_ok=True)
    for index,(obj,go) in enumerate(matches):
        root = {'path_id':int(obj.path_id),'nodes':[]}
        def visit(node,parent,path,is_root=False):
            pointers = component_pointers(node)
            types = [p.type.name for p in pointers]
            # Mesh/transform extraction does not require parsing MonoBehaviours
            # or AudioSource payloads. Preserve their type inventory explicitly.
            comps = [p.read() for p in pointers if p.type.name in ('Transform','MeshFilter')]
            transform = next(c for c in comps if type(c).__name__ == 'Transform')
            local = matrix(transform)
            world = np.eye(4) if is_root else parent @ local
            row = {'path':path,'component_types':types,'renderer_present':'MeshRenderer' in types,
                   'local_position':xyz(transform.m_LocalPosition),'local_scale':xyz(transform.m_LocalScale),
                   'local_rotation_xyzw':[float(getattr(transform.m_LocalRotation,k)) for k in ('x','y','z','w')],
                   'local_to_mount_root':world.tolist(),'meshes':[]}
            row['renderer_enabled'] = [bool(p.read().m_Enabled) for p in pointers if p.type.name == 'MeshRenderer']
            for c in comps:
                if type(c).__name__ == 'MeshFilter' and c.m_Mesh.path_id:
                    mesh_reader = c.m_Mesh.deref()
                    mesh = c.m_Mesh.read()
                    handler = MeshHandler(mesh)
                    handler.process()
                    v = np.array(handler.m_Vertices,dtype=float)[:,:3]
                    mapped = (world[:3,:3] @ v.T).T + world[:3,3]
                    triangles = [list(map(int,tri)) for group in handler.get_triangles() for tri in group]
                    if not np.isfinite(mapped).all() or not len(triangles):
                        raise ValueError(f'Invalid mesh at {path}')
                    name = f'root{index}_'+path.replace('/','_')+'.mesh.json'
                    payload = {'hierarchy_path':path,'mesh_name':mesh.m_Name,
                               'mesh_path_id':int(c.m_Mesh.path_id),'mesh_file_id':int(c.m_Mesh.file_id),
                               'mesh_container':str(mesh_reader.assets_file.name),
                               'mesh_serialized_object_sha256':hashlib.sha256(mesh_reader.get_raw_data()).hexdigest(),
                               'vertices_mount_root_unity_m':mapped.tolist(),
                               'triangles':triangles}
                    text = json.dumps(payload,separators=(',',':'))+'\n'
                    (OUT/name).write_text(text,encoding='utf-8')
                    row['meshes'].append({'mesh_name':mesh.m_Name,'path_id':int(c.m_Mesh.path_id),
                                         'vertex_count':len(mapped),'triangle_count':len(triangles),
                                         'bounds_mount_root_unity_m':[mapped.min(axis=0).tolist(),mapped.max(axis=0).tolist()],
                                         'reference_file':name,'reference_sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest(),
                                         'mesh_file_id':payload['mesh_file_id'],'mesh_container':payload['mesh_container']})
            root['nodes'].append(row)
            for child_ptr in transform.m_Children:
                child_transform = child_ptr.read()
                child_go = child_transform.m_GameObject.read()
                visit(child_go,world,path+'/'+child_go.m_Name)
        try:
            visit(go,np.eye(4),'AGM1_single',True)
        except Exception as exc:
            report['errors'].append({'root_index':index,'error':repr(exc)})
        report['roots'].append(root)
    report['extracted'] = bool(matches) and not report['errors']
    (OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'extracted':report['extracted'],'source_sha256':source_hash,
                      'matching_roots':len(matches),'node_counts':[len(r['nodes']) for r in report['roots']],
                      'errors':report['errors'],'manifest':str(OUT/'manifest.json')},indent=2))
    if not report['extracted']:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
