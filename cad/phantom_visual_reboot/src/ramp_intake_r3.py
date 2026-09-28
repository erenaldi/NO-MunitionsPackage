"""35 mm forward outer-lip travel, retaining the saved R1 intake geometry."""
import math
from cadgen import build123d as bd, step
from ramp_intake_r1 import ROOT, HINGE_X, HINGE_Z, STATE_FRACTIONS, _read_parts

TARGET_DROP_MM = 35.0
DEPLOYMENT_DEG = math.degrees(math.asin((TARGET_DROP_MM + 3.0) / math.hypot(660.0,3.0))
                              - math.atan2(3.0,660.0))


def assembly(state, module=False):
    parts = _read_parts(ROOT/'STEP'/f'R_RampIntake_R1_{state}.step')
    ramp = parts['intake_r1_ramp'].rotate(
        bd.Axis((HINGE_X,0,HINGE_Z),(0,1,0)),
        (DEPLOYMENT_DEG-5.0)*STATE_FRACTIONS[state])
    ramp.label = 'intake_r1_ramp'
    parts['intake_r1_ramp'] = ramp
    return bd.Compound(children=[p for name,p in parts.items()
                                 if not module or name.startswith('intake_r1_')],
                       label='R_RampIntake_R3_'+state)


@step(out='../STEP/R_RampIntake_R3_Stowed.step')
def stowed():
    return assembly('Stowed')


@step(out='../STEP/R_RampIntake_R3_Midfold.step')
def midfold():
    return assembly('Midfold')


@step(out='../STEP/R_RampIntake_R3_Deployed.step')
def deployed():
    return assembly('Deployed')


@step(out='../STEP/R_RampIntake_R3_Module_Deployed.step')
def module_deployed():
    return assembly('Deployed',True)


if __name__ == '__main__':
    print({'target_lip_drop_mm':TARGET_DROP_MM,'deployment_deg':DEPLOYMENT_DEG},flush=True)
    stowed()
    midfold()
    deployed()
    module_deployed()
