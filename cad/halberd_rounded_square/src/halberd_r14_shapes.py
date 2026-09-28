"""R14: booster fin/fairing topology cleanup at all four approved stations.

Each station's fin and intake fairing are Boolean-unioned into one contiguous
solid, then ONLY the buried volume inside the unchanged booster body is
trimmed away. The combined outer shape is preserved exactly (union identity),
while the fin/fairing/body mesh intersections that caused the jagged
light/dark strip at the fin root are eliminated. No silhouette, ridge, roof,
stage seam, inlet, main body or R13 cover geometry is changed.
"""
from cadgen import build123d as bd
from halberd_r13 import halberd_r13
from halberd_r13_shapes import MATERIALS
from halberd_r12_shapes import MAIN_LABEL
from study_shapes import tag, SEPARATION

FIN_LABELS = tuple(f"booster_fin_{i}" for i in range(1, 5))
FAIRING_LABELS = tuple(f"booster_intake_fairing_{i}" for i in range(1, 5))
CLEAN_LABELS = tuple(f"booster_fin_fairing_{i}" for i in range(1, 5))
# Consolidated existing fin gray; the fairing's former #B5BDC3 is retired.
FIN_COLOR = "#929DA5"


def clean_station(fin, fairing, body):
    combined = fin + fairing
    cleaned = combined - body
    if not cleaned.is_valid or len(cleaned.solids()) != 1 or cleaned.volume <= 0:
        raise ValueError("Fin/fairing union-trim must yield one valid solid")
    return cleaned


def build_r14(separated=False):
    model = halberd_r13()
    by_label = {p.label: p for p in model.children}
    body = by_label["booster_body"]
    parts = [p for label, p in by_label.items()
             if label not in FIN_LABELS and label not in FAIRING_LABELS]
    for i in range(1, 5):
        cleaned = clean_station(by_label[f"booster_fin_{i}"],
                                by_label[f"booster_intake_fairing_{i}"], body)
        parts.append(tag(cleaned, f"booster_fin_fairing_{i}", FIN_COLOR))
    if len(parts) != 27:
        raise ValueError("Unexpected R14 part count")
    if separated:
        parts = [p.moved(bd.Location((-SEPARATION, 0, 0)))
                 if p.label.startswith("booster") else p for p in parts]
    return bd.Compound(children=parts, label="Halberd_R14_Clean_Fin_Fairing" +
                       ("_Separated" if separated else ""))


def booster_focus(model, fin_labels, label):
    # Cropped context is review-only. Unclock the selected station to +Z.
    clip = bd.Box(720., 450., 450.).translate((-1240., 0, 0))
    parts = []
    for p in model.children:
        if p.label not in (MAIN_LABEL, "booster_body", *fin_labels):
            continue
        shape = p.rotate(bd.Axis.X, 45.) & clip
        shape.label = p.label
        shape.color = p.color
        parts.append(shape)
    return bd.Compound(children=parts, label=label)