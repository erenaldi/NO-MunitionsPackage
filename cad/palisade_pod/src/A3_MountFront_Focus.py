"""Isolated front sensor fairing from the A3 study, not a separate design."""
from cadgen import build123d as bd, step
from mount_front import study


@step(out="../STEP/A3_MountFront_Focus.step")
def a3_mount_front_focus():
    return bd.Compound(children=[item for item in study(False).children
                                 if item.label.startswith("forward_")])


if __name__ == "__main__":
    a3_mount_front_focus()
