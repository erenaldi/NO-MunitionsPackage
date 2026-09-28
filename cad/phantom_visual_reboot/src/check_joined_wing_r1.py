"""Independent exported-shape checks for the reference-led joined-side study."""
import json
import math
from pathlib import Path
import build123d as bd
from OCP.BRepAdaptor import BRepAdaptor_Surface
from joined_wing_r1 import pose, STATES, FRONT_Z, REAR_Z

ROOT=Path(__file__).resolve().parents[1]
BODY='RDM9_R7_symmetric_body_20mm_wedge_R4'
FRONT='forward_lifting_panel'
REAR='rear_lifting_panel'
SLIDER='sliding_rear_root_carriage'
JOIN='outboard_join_pin'
STATIC={'joined_wing_dorsal_housing','fixed_forward_root'}
EXPECTED=STATIC|{FRONT,REAR,SLIDER,JOIN}


def volume(shape):
    return 0 if shape is None else shape.volume


def difference(a,b):
    return volume(a-b)+volume(b-a)


def bore_centers(part):
    centers=set()
    for face in part.faces():
        if face.geom_type==bd.GeomType.CYLINDER:
            cyl=BRepAdaptor_Surface(face.wrapped).Cylinder()
            if abs(cyl.Radius()-3.75)<.0001:
                centers.add((round(cyl.Location().X(),6),round(cyl.Location().Y(),6)))
    assert len(centers)==2,centers
    return centers


def assert_center(centers,point):
    assert min(math.dist(p,point) for p in centers)<.001,(centers,point)


def local(part,label,data):
    if label in (FRONT,REAR):
        key='front' if label==FRONT else 'rear'
        x,y=data[key]
        z=FRONT_Z if label==FRONT else REAR_Z
        return part.translate((-x,-y,-z)).rotate(bd.Axis.Z,-data[key+'_angle'])
    if label in (SLIDER,JOIN):
        x,y=data['rear' if label==SLIDER else 'joint']
        return part.translate((-x,-y,0))
    return part


def place(part,label,data):
    if label in (FRONT,REAR):
        key='front' if label==FRONT else 'rear'
        z=FRONT_Z if label==FRONT else REAR_Z
        return part.rotate(bd.Axis.Z,data[key+'_angle']).translate((*data[key],z))
    if label in (SLIDER,JOIN):
        return part.translate((*data['rear' if label==SLIDER else 'joint'],0))
    return part


baseline=bd.import_step(ROOT/'STEP/J_Symmetric_Body_R7.step')
reference={}
report={'states':{}}
for state,fraction in STATES.items():
    print('Checking saved',state,flush=True)
    assembly=bd.import_step(ROOT/('STEP/L_JoinedWing_R1_'+state+'.step'))
    module=bd.import_step(ROOT/('STEP/L_JoinedWing_R1_Module_'+state+'.step'))
    parts={p.label:p for p in assembly.children}
    module_parts={p.label:p for p in module.children}
    assert set(parts)==EXPECTED|{BODY} and set(module_parts)==EXPECTED
    for part in [*parts.values(),*module_parts.values()]:
        assert part.is_valid and len(part.solids())==1 and part.volume>0,part.label
    assert abs(assembly.bounding_box().size.X-2800)<.001
    assert difference(parts[BODY],baseline)<.01
    data=pose(fraction)
    for label in EXPECTED:
        assert difference(parts[label],module_parts[label])<.01,label
        canonical=local(parts[label],label,data)
        if state=='Stowed':
            reference[label]=canonical
        else:
            assert difference(canonical,reference[label])<.01,label
    for label,key,length in [(FRONT,'front',900),(REAR,'rear',600)]:
        centers=bore_centers(parts[label])
        assert_center(centers,data[key])
        assert_center(centers,data['joint'])
        assert abs(math.dist(*centers)-length)<.001
    bounds={}
    if state=='Stowed':
        for label,part in parts.items():
            box=part.bounding_box()
            bound=math.hypot(max(abs(box.min.Y),abs(box.max.Y)),
                             max(abs(box.min.Z),abs(box.max.Z)))
            assert bound<125,(label,bound)
            bounds[label]=bound
    report['states'][state]={'valid_solids':7,'module_valid_solids':6,
                            'pose':data,'stowed_radial_bounds_mm':bounds}

# Pose intermediate points from the saved parts, never regenerating a panel.
sampled=[]
minimum_clearance=1e9
last_rear=1e9
for i in range(21):
    fraction=i/20
    print('Checking motion sample',i,'of 20',flush=True)
    data=pose(fraction)
    assert data['rear'][0]<last_rear
    last_rear=data['rear'][0]
    parts={label:place(part,label,data) for label,part in reference.items()}
    for label,key,length in [(FRONT,'front',900),(REAR,'rear',600)]:
        assert abs(math.dist(data[key],data['joint'])-length)<.0001
        for other in [baseline,*[p for name,p in parts.items() if name!=label]]:
            assert volume(parts[label] & other)<.001,(fraction,label,other.label)
            clearance=parts[label].distance_to(other)
            assert clearance>.2,(fraction,label,other.label,clearance)
            minimum_clearance=min(minimum_clearance,clearance)
    assert volume(parts[SLIDER] & parts['joined_wing_dorsal_housing'])<.001
    assert volume(parts[JOIN] & parts['joined_wing_dorsal_housing'])<.001
    sampled.append({'fraction':fraction,'rear_root_x':data['rear'][0],
                    'outboard_joint':data['joint']})
report['sampled_motion']=sampled
report['minimum_sampled_panel_clearance_mm']=minimum_clearance
report['rearward_carriage_travel_mm']=pose(0)['rear'][0]-pose(1)['rear'][0]
report['all_rigid_parts_identical_after_inverse_pose']=True
print(json.dumps(report,indent=2))
(ROOT/'reviews/joined_wing_r1_checks.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
