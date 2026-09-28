"""R18 gate-2 full access candidate, preserving the saved 28-part base."""
from cadgen import step

from halberd_r18_access_build import build_r18_access, materials_for_labels


ACCESS_LABELS = (
    "main_r18_F02_cover",
    *(f"main_r18_F02_fastener_{i}" for i in range(1, 5)),
    "main_r18_F04A_cover",
    *(f"main_r18_F04A_fastener_{i}" for i in range(1, 7)),
    "main_r18_F04B_cover",
    *(f"main_r18_F04B_fastener_{i}" for i in range(1, 5)),
    "main_r18_F05_terminal_left",
    "main_r18_F05_center_strip",
    "main_r18_F05_terminal_right",
    "main_r18_F05_fastener_1",
    "main_r18_F05_fastener_2",
    "main_r18_F03A_ring",
    "main_r18_F03A_disc",
    "main_r18_F03A_fastener_1",
    "main_r18_F03A_fastener_2",
    "booster_r18_F03B_keyed_cap",
    "booster_r18_F10_cover",
    *(f"booster_r18_F10_fastener_{i}" for i in range(1, 4)),
    "main_r18_nozzle_ring",
    *(f"main_r18_nozzle_fastener_{i}" for i in range(1, 9)),
    "booster_r18_nozzle_ring",
    *(f"booster_r18_nozzle_fastener_{i}" for i in range(1, 9)),
)
MATERIALS = materials_for_labels(ACCESS_LABELS, include_all_base=True)


@step(out="../STEP/halberd_r18_access.step", materials=MATERIALS)
def halberd_r18_access():
    return build_r18_access().compound


if __name__ == "__main__":
    halberd_r18_access()
