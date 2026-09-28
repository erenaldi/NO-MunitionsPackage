"""Read the independent concept masters to produce staged and intake reviews."""
import json
from pathlib import Path
from cadgen import build123d as bd, read_step, step

ROOT = Path(__file__).resolve().parent


def review(concept, mode):
    master = read_step(ROOT / f"Halberd_Concept_{concept}.step")
    children = []
    for part in master.children:
        booster = part.label.startswith("booster_")
        if mode == "Separated":
            children.append(part.moved(bd.Location((-350, 0, 0))) if booster else part)
        elif mode == "Upper" and not booster or mode == "Booster" and booster:
            children.append(part)
        elif mode == "Intake" and (part.label.startswith("intake_") or part.label == "sustainer_body"):
            crop = bd.Box(680, 400, 400).translate((475, 0, 0))
            piece = part & crop
            if piece is not None and piece.volume > 0:
                piece.label, piece.color = part.label, part.color
                children.append(piece)
    return bd.Compound(children=children, label=f"{concept}_{mode}_Review")


@step(out="Halberd_Concept_Pod_Separated.step")
def pod_separated():
    return review("Pod", "Separated")


@step(out="Halberd_Concept_Shoulder_Separated.step")
def shoulder_separated():
    return review("Shoulder", "Separated")


@step(out="Halberd_Concept_Pod_Intake.step")
def pod_intake():
    return review("Pod", "Intake")


@step(out="Halberd_Concept_Shoulder_Intake.step")
def shoulder_intake():
    return review("Shoulder", "Intake")


@step(out="Halberd_Concept_Pod_Upper.step")
def pod_upper():
    return review("Pod", "Upper")


@step(out="Halberd_Concept_Pod_Booster.step")
def pod_booster():
    return review("Pod", "Booster")


@step(out="Halberd_Concept_Shoulder_Upper.step")
def shoulder_upper():
    return review("Shoulder", "Upper")


@step(out="Halberd_Concept_Shoulder_Booster.step")
def shoulder_booster():
    return review("Shoulder", "Booster")


def snapshot_jobs():
    jobs = []
    for name in ("Pod", "Shoulder"):
        for suffix, views in (
            ("", {"iso": [-1, -1, .7], "opposite": [1, 1, -.7],
                  "side": [0, -1, 0], "top": [0, 0, 1], "nose": [1, 0, 0], "tail": [-1, 0, 0]}),
            ("_Separated", {"separated": [-1, -1, .7], "separated_opposite": [1, 1, -.7]}),
            ("_Intake", {"intake": [1, -1, .7], "mouth": [1, 0, 0], "grazing": [.15, -1, .12]}),
            ("_Upper", {"upper_aft": [-1, -.5, .4]}),
            ("_Booster", {"booster_face": [1, -.5, .4]}),
        ):
            jobs.append({"input": f"Halberd_Concept_{name}{suffix}.step", "mode": "view",
                         "theme": "snapshot", "display": {"mode": "rendered"},
                         "outputs": [{"path": f"Halberd_Concept_{name}_{view}.png", "camera": {"direction": direction}}
                                     for view, direction in views.items()],
                         "render": {"sizeProfile": "diagnostic", "padding": .1, "viewLabels": False}})
    (ROOT / "halberd_concepts_snapshot_job.json").write_text(json.dumps(jobs, indent=2) + "\n")


if __name__ == "__main__":
    for model in (pod_separated, shoulder_separated, pod_intake, shoulder_intake,
                  pod_upper, pod_booster, shoulder_upper, shoulder_booster):
        model()
    snapshot_jobs()
