"""Isolate the single body solid for the CAD Viewer mesher regression check."""
from pathlib import Path
from cadgen import read_step, step


@step(out="Halberd_Hybrid_BodyAudit.step")
def body_audit():
    model=read_step(Path(__file__).with_name("Halberd_Shoulder_Hybrid.step"))
    return next(part for part in model.children if part.label=="sustainer_body")


if __name__=="__main__": body_audit()
