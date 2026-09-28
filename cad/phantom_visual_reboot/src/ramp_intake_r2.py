"""Halve the R1 forward outer-lip vertical travel; preserve all part shapes."""
import math
from cadgen import build123d as bd, step
from ramp_intake_r1 import ROOT, HINGE_X, HINGE_Z, STATE_FRACTIONS, _read_parts

R1_ANGLE_DEG = 5.0
FLOOR_LENGTH = 660.0
FLOOR_THICKNESS = 3.0
R1_DROP_MM = (FLOOR_LENGTH * math.sin(math.radians(R1_ANGLE_DEG))
              + FLOOR_THICKNESS * (math.cos(math.radians(R1_ANGLE_DEG)) - 1))
TARGET_DROP_MM = R1_DROP_MM / 2
DEPLOYMENT_DEG = math.degrees(
    math.asin((TARGET_DROP_MM + FLOOR_THICKNESS) / math.hypot(FLOOR_LENGTH, FLOOR_THICKNESS))
    - math.atan2(FLOOR_THICKNESS, FLOOR_LENGTH)
)


def assembly(state, module=False):
    parts = _read_parts(ROOT / 'STEP' / f'R_RampIntake_R1_{state}.step')
    fraction = STATE_FRACTIONS[state]
    ramp = parts['intake_r1_ramp'].rotate(
        bd.Axis((HINGE_X,0,HINGE_Z),(0,1,0)),
        (DEPLOYMENT_DEG - R1_ANGLE_DEG) * fraction,
    )
    ramp.label = 'intake_r1_ramp'
    parts['intake_r1_ramp'] = ramp
    selected = [p for name,p in parts.items() if not module or name.startswith('intake_r1_')]
    return bd.Compound(children=selected,label='R_RampIntake_R2_'+state)


@step(out='../STEP/R_RampIntake_R2_Stowed.step')
def stowed():
    return assembly('Stowed')


@step(out='../STEP/R_RampIntake_R2_Midfold.step')
def midfold():
    return assembly('Midfold')


@step(out='../STEP/R_RampIntake_R2_Deployed.step')
def deployed():
    return assembly('Deployed')


@step(out='../STEP/R_RampIntake_R2_Module_Deployed.step')
def module_deployed():
    return assembly('Deployed',True)


if __name__ == '__main__':
    print({'target_lip_drop_mm': TARGET_DROP_MM, 'deployment_deg': DEPLOYMENT_DEG},flush=True)
    stowed()
    midfold()
    deployed()
    module_deployed()
