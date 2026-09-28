"""Compute matched OLD/NEW cameras for the R2 review renders and write the job.

Each matched pair renders the saved L (R1) and M (R2) artifacts with the SAME
camera (direction, target, orthographicHalfHeight, projection), so scale and
framing are identical within every pair. Framing is fit to the union bounding
box of the two artifacts (or to the isolated module for the on-body views).
"""
import json
import math
from pathlib import Path
import build123d as bd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
STEP = ROOT / 'STEP'
WIDTH, HEIGHT = 1600, 1200
ASPECT = WIDTH / HEIGHT
PADDING = 0.10

# name, L input, M input, frame files (L, M), direction, up, fixed camera
VIEWS = [
    ('stowed_module_top',
     'L_JoinedWing_R1_Module_Stowed.step', 'M_JoinedWing_R2_Module_Stowed.step',
     'L_JoinedWing_R1_Module_Stowed.step', 'M_JoinedWing_R2_Module_Stowed.step',
     [0, 0, 1], [0, 1, 0], None),
    ('stowed_module_iso',
     'L_JoinedWing_R1_Module_Stowed.step', 'M_JoinedWing_R2_Module_Stowed.step',
     'L_JoinedWing_R1_Module_Stowed.step', 'M_JoinedWing_R2_Module_Stowed.step',
     [1, -1, 0.7], [0, 0, 1], None),
    ('stowed_body_iso',
     'L_JoinedWing_R1_Stowed.step', 'M_JoinedWing_R2_Stowed.step',
     'L_JoinedWing_R1_Module_Stowed.step', 'M_JoinedWing_R2_Module_Stowed.step',
     [1, -1, 0.7], [0, 0, 1], None),
    ('stowed_body_end_env',
     'L_JoinedWing_R1_Stowed.step', 'M_JoinedWing_R2_Stowed.step',
     'L_JoinedWing_R1_Stowed.step', 'M_JoinedWing_R2_Stowed.step',
     [-1, 0, 0], [0, 0, 1], {'target': [0.0, 0.0, 0.0], 'orthographicHalfHeight': 140.0}),
    ('midfold_module_top',
     'L_JoinedWing_R1_Module_Midfold.step', 'M_JoinedWing_R2_Module_Midfold.step',
     'L_JoinedWing_R1_Module_Midfold.step', 'M_JoinedWing_R2_Module_Midfold.step',
     [0, 0, 1], [0, 1, 0], None),
    ('midfold_module_iso',
     'L_JoinedWing_R1_Module_Midfold.step', 'M_JoinedWing_R2_Module_Midfold.step',
     'L_JoinedWing_R1_Module_Midfold.step', 'M_JoinedWing_R2_Module_Midfold.step',
     [1, -1, 0.7], [0, 0, 1], None),
    ('midfold_body_iso',
     'L_JoinedWing_R1_Midfold.step', 'M_JoinedWing_R2_Midfold.step',
     'L_JoinedWing_R1_Module_Midfold.step', 'M_JoinedWing_R2_Module_Midfold.step',
     [1, -1, 0.7], [0, 0, 1], None),
    ('deployed_module_top',
     'L_JoinedWing_R1_Module_Deployed.step', 'M_JoinedWing_R2_Module_Deployed.step',
     'L_JoinedWing_R1_Module_Deployed.step', 'M_JoinedWing_R2_Module_Deployed.step',
     [0, 0, 1], [0, 1, 0], None),
    ('deployed_module_iso',
     'L_JoinedWing_R1_Module_Deployed.step', 'M_JoinedWing_R2_Module_Deployed.step',
     'L_JoinedWing_R1_Module_Deployed.step', 'M_JoinedWing_R2_Module_Deployed.step',
     [1, -1, 0.7], [0, 0, 1], None),
    ('deployed_body_iso',
     'L_JoinedWing_R1_Deployed.step', 'M_JoinedWing_R2_Deployed.step',
     'L_JoinedWing_R1_Module_Deployed.step', 'M_JoinedWing_R2_Module_Deployed.step',
     [1, -1, 0.7], [0, 0, 1], None),
    ('deployed_module_opposed',
     'L_JoinedWing_R1_Module_Deployed.step', 'M_JoinedWing_R2_Module_Deployed.step',
     'L_JoinedWing_R1_Module_Deployed.step', 'M_JoinedWing_R2_Module_Deployed.step',
     [-1, 1, -0.7], [0, 0, 1],
     {'target': [-175.0, 630.294, 97.5], 'orthographicHalfHeight': 220.0}),
]


def union_bbox(files):
    lo = [1e18] * 3
    hi = [-1e18] * 3
    for name in files:
        box = bd.import_step(STEP / name).bounding_box()
        for i, axis in enumerate(('X', 'Y', 'Z')):
            lo[i] = min(lo[i], getattr(box.min, axis))
            hi[i] = max(hi[i], getattr(box.max, axis))
    return lo, hi


def projected_extent(lo, hi, direction, up, target):
    d = np.array(direction, float)
    d /= np.linalg.norm(d)
    u = np.array(up, float)
    u /= np.linalg.norm(u)
    forward = -d
    right = np.cross(forward, u)
    right /= np.linalg.norm(right)
    up2 = np.cross(right, forward)
    up2 /= np.linalg.norm(up2)
    corners = [[sx, sy, sz]
               for sx in (lo[0], hi[0]) for sy in (lo[1], hi[1]) for sz in (lo[2], hi[2])]
    v = np.array(corners) - np.array(target)
    r = v @ right
    uu = v @ up2
    return r.max() - r.min(), uu.max() - uu.min()


def fit_camera(files, direction, up):
    lo, hi = union_bbox(files)
    target = [(lo[i] + hi[i]) / 2 for i in range(3)]
    extent_right, extent_up = projected_extent(lo, hi, direction, up, target)
    hh = max(extent_up / 2, extent_right / (2 * ASPECT)) * (1 + PADDING)
    return target, hh, lo, hi, extent_right, extent_up


def camera_dict(direction, up, target, hh):
    return {'direction': direction, 'up': up, 'target': [round(v, 3) for v in target],
            'orthographicHalfHeight': round(hh, 3), 'projection': 'orthographic'}


job = []
summary = []
for name, l_in, m_in, l_frame, m_frame, direction, up, fixed in VIEWS:
    frame_files = (l_frame, m_frame)
    if fixed is None:
        target, hh, lo, hi, er, eu = fit_camera(frame_files, direction, up)
    else:
        target = fixed['target']
        hh = fixed['orthographicHalfHeight']
        lo, hi = union_bbox(frame_files)
        er, eu = projected_extent(lo, hi, direction, up, target)
    cam = camera_dict(direction, up, target, hh)
    summary.append({'view': name, 'target': cam['target'], 'hh': cam['orthographicHalfHeight'],
                    'frame_extent_right': round(float(er), 1), 'frame_extent_up': round(float(eu), 1),
                    'fits': bool(er / 2 <= hh * ASPECT and eu / 2 <= hh)})
    job.append({'input': 'STEP/' + l_in, 'mode': 'view', 'output': {'tightFrame': False},
                'outputs': [{'path': 'reviews/L2_' + name + '.png', 'camera': cam}]})
    job.append({'input': 'STEP/' + m_in, 'mode': 'view', 'output': {'tightFrame': False},
                'outputs': [{'path': 'reviews/M2_' + name + '.png', 'camera': cam}]})

(ROOT / 'src/render_joined_review_r2.json').write_text(json.dumps(job, indent=1) + '\n', encoding='utf-8')
print(json.dumps(summary, indent=1))