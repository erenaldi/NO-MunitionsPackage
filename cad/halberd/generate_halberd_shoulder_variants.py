"""Build five explicit Shoulder concept variants and their separated views."""
from cadgen import step, read_step, build123d as bd
from pathlib import Path
from halberd_shoulder_variants import build_variant


@step(out="Halberd_B1_Needle.step")
def needle(): return build_variant("B1_Needle")

@step(out="Halberd_B2_Broadhead.step")
def broadhead(): return build_variant("B2_Broadhead")

@step(out="Halberd_B3_Chisel.step")
def chisel(): return build_variant("B3_Chisel")

@step(out="Halberd_B4_Manta.step")
def manta(): return build_variant("B4_Manta")

@step(out="Halberd_B5_Sculpted.step")
def sculpted(): return build_variant("B5_Sculpted")


def separated(key):
    model=read_step(Path(__file__).with_name(f"Halberd_{key}.step"))
    return bd.Compound(children=[p.moved(bd.Location((-350,0,0))) if p.label.startswith("booster_") else p
                                 for p in model.children],label=f"{key}_Separated")

@step(out="Halberd_B1_Needle_Separated.step")
def needle_separated(): return separated("B1_Needle")

@step(out="Halberd_B2_Broadhead_Separated.step")
def broadhead_separated(): return separated("B2_Broadhead")

@step(out="Halberd_B3_Chisel_Separated.step")
def chisel_separated(): return separated("B3_Chisel")

@step(out="Halberd_B4_Manta_Separated.step")
def manta_separated(): return separated("B4_Manta")

@step(out="Halberd_B5_Sculpted_Separated.step")
def sculpted_separated(): return separated("B5_Sculpted")

if __name__=="__main__":
    for model in (needle,broadhead,chisel,manta,sculpted,needle_separated,broadhead_separated,
                  chisel_separated,manta_separated,sculpted_separated):
        model()
