"""Independent three-intake Halberd silhouette study."""
from cadgen import step
from halberd_concept_shapes import pod


@step(out="Halberd_Concept_Pod.step")
def halberd_pod_concept():
    return pod()


if __name__ == "__main__":
    halberd_pod_concept()
