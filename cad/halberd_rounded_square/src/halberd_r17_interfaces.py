"""Cropped, local R17 gate-1 review artifacts; no production propagation."""
from cadgen import step


@step(out="../STEP/halberd_r17_interfaces_main_fin.step")
def halberd_r17_interfaces_main_fin():
    from halberd_r17_interface_shapes import build_review_artifact
    return build_review_artifact("main_fin")[0]


@step(out="../STEP/halberd_r17_interfaces_booster_fin.step")
def halberd_r17_interfaces_booster_fin():
    from halberd_r17_interface_shapes import build_review_artifact
    return build_review_artifact("booster_fin")[0]


@step(out="../STEP/halberd_r17_interfaces_nozzles.step")
def halberd_r17_interfaces_nozzles():
    from halberd_r17_interface_shapes import build_review_artifact
    return build_review_artifact("nozzles")[0]


if __name__ == "__main__":
    halberd_r17_interfaces_main_fin()
    halberd_r17_interfaces_booster_fin()
    halberd_r17_interfaces_nozzles()
