"""Selected clipped fin; complete one-corner unit translated 80 mm aft."""
from cadgen import build123d as bd, read_step, step
from tail_fin_r1 import ROOT, A5_STATES, tail_components

AFT_SHIFT = -80.0


def assembly(state):
    filename, fraction = A5_STATES[state]
    base = read_step(ROOT/'STEP'/filename)
    tail = [p.translate((AFT_SHIFT,0,0)) for p in tail_components('Tall',fraction)]
    return bd.Compound(children=[base,*tail],label='Q_Tail_R2_Clipped_'+state)


@step(out='../STEP/Q_Tail_R2_Clipped_Stowed.step')
def stowed():
    return assembly('Stowed')


@step(out='../STEP/Q_Tail_R2_Clipped_Midfold.step')
def midfold():
    return assembly('Midfold')


@step(out='../STEP/Q_Tail_R2_Clipped_Deployed.step')
def deployed():
    return assembly('Deployed')


if __name__ == '__main__':
    stowed()
    midfold()
    deployed()
