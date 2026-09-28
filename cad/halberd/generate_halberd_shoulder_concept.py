"""Independent four-intake Halberd silhouette study."""
from cadgen import step
from halberd_concept_shapes import shoulder


@step(out="Halberd_Concept_Shoulder.step")
def halberd_shoulder_concept():
    return shoulder()


if __name__ == "__main__":
    halberd_shoulder_concept()
