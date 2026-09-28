"""Build intake and separated-stage reviews for four Halberd concepts."""
import json
from pathlib import Path

from cadgen import step

from halberd_four_intake_concepts import (
    build_intake_review,
    build_petal_intake_prototype,
    build_petal_intake_prototype_closeup,
    build_separated_review,
)


ROOT = Path(__file__).resolve().parent
CONCEPTS = (
    ("C1", "Razorback"),
    ("C2", "Manta"),
    ("C3", "Citadel"),
    ("C4", "Petal"),
)


@step(out="Halberd_C1_Razorback_Intakes.step")
def razorback_intakes(): return build_intake_review("Razorback")


@step(out="Halberd_C1_Razorback_Separated.step")
def razorback_separated(): return build_separated_review("Razorback")


@step(out="Halberd_C2_Manta_Intakes.step")
def manta_intakes(): return build_intake_review("Manta")


@step(out="Halberd_C2_Manta_Separated.step")
def manta_separated(): return build_separated_review("Manta")


@step(out="Halberd_C3_Citadel_Intakes.step")
def citadel_intakes(): return build_intake_review("Citadel")


@step(out="Halberd_C3_Citadel_Separated.step")
def citadel_separated(): return build_separated_review("Citadel")


@step(out="Halberd_C4_Petal_Intakes.step")
def petal_intakes(): return build_intake_review("Petal")


@step(out="Halberd_C4_Petal_Separated.step")
def petal_separated(): return build_separated_review("Petal")


@step(out="Halberd_C4_Petal_Intake_Prototype.step")
def petal_intake_prototype(): return build_petal_intake_prototype()


@step(out="Halberd_C4_Petal_Intake_Prototype_Closeup.step")
def petal_intake_prototype_closeup(): return build_petal_intake_prototype_closeup()


def write_snapshot_job():
    jobs = []
    master_views = {
        "iso": [-1, -1, 0.7],
        "opposite": [1, 1, -0.7],
        "side": [0, -1, 0],
        "top": [0, 0, 1],
        "nose": [1, 0, 0],
        "tail": [-1, 0, 0],
    }
    intake_views = {
        "intakes": [1, -1, 0.7],
        "mouths": [1, 0, 0],
        "grazing": [0.15, -1, 0.12],
    }
    for code, name in CONCEPTS:
        stem = f"Halberd_{code}_{name}"
        for suffix, views in (
            ("", master_views),
            ("_Intakes", intake_views),
            ("_Separated", {"separated": [-1, -1, 0.7]}),
        ):
            jobs.append({
                "input": f"{stem}{suffix}.step",
                "mode": "view",
                "theme": "snapshot",
                "display": {"mode": "rendered"},
                "outputs": [
                    {
                        "path": f"{stem}_{view}.png",
                        "camera": {"direction": direction},
                    }
                    for view, direction in views.items()
                ],
                "render": {
                    "sizeProfile": "diagnostic",
                    "padding": 0.1,
                    "viewLabels": False,
                },
            })
    path = ROOT / "halberd_four_intake_snapshot_job.json"
    path.write_text(json.dumps(jobs, indent=2) + "\n", encoding="utf-8")
    print(path)


if __name__ == "__main__":
    razorback_intakes(); razorback_separated()
    manta_intakes(); manta_separated()
    citadel_intakes(); citadel_separated()
    petal_intakes(); petal_separated()
    petal_intake_prototype()
    petal_intake_prototype_closeup()
    write_snapshot_job()
