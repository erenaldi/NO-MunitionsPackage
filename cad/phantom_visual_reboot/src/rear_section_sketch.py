"""Plain rear-section reference for hand sketching: saved R1 assemblies clipped to X-1400..-100, full width, no engine."""
from cadgen import build123d as bd, read_step, step
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def leaves(n):
    c = list(getattr(n, "children", ()) or ())
    return [l for k in c for l in leaves(k)] if c else [n]


def clipped(state, half=False):
    src = read_step(str(ROOT / "STEP" / f"S_AftExhaust_R1_{state}.step"))
    clip = bd.Box(1300.0, 500.0, 500.0).translate((-750.0, 250.0 if half else 0.0, 0.0))
    out = []
    for p in leaves(src):
        c = p & clip
        if c is not None and c.volume > 1e-4:
            c.label = str(p.label)
            c.color = p.color
            out.append(c)
    return bd.Compound(children=out, label=f"Rear{'Cutaway' if half else 'Section'}_{state}_Reference")


@step(out="../STEP/S_RearSection_Deployed_Reference.step")
def deployed():
    return clipped("Deployed")


@step(out="../STEP/S_RearSection_Stowed_Reference.step")
def stowed():
    return clipped("Stowed")


@step(out="../STEP/S_RearCutaway_Deployed_Reference.step")
def cutaway_deployed():
    return clipped("Deployed", half=True)


@step(out="../STEP/S_RearCutaway_Stowed_Reference.step")
def cutaway_stowed():
    return clipped("Stowed", half=True)


if __name__ == "__main__":
    deployed()
    stowed()
    cutaway_deployed()
    cutaway_stowed()
