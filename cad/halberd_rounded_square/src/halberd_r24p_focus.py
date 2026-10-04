"""Review-only crops of the saved R24p model around the booster_fin_fairing_1 lip seats.

Fin: a 120 mm cube centred on the fairing at X -1232, r 140, clock 45 (keeps the
neighbouring fins out of the view). Macro: a 30 mm cube centred on each seat frame
origin (from the R24p metadata). Reads the saved R24p STEP only; no geometry is
authored (crop rule in cad/shared/review_crop.py).
"""
import json
import sys
from pathlib import Path

from cadgen import step

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from review_crop import crop_scene, cube_at, radial_point  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "STEP" / "r24p_flank_seats.step"
META = ROOT / "reviews" / "halberd_r24p_flank_lip_seats.json"


def _origin(side):
    seats = json.loads(META.read_text(encoding="utf-8"))["seats"]
    return seats[f"booster_r24p_F11_1{side}"]["frame_origin_mm"]


@step(out="../STEP/r24p_fin_focus.step")
def r24p_fin_focus():
    return crop_scene(SAVED, cube_at(radial_point(-1232.0, 140.0, 45.0), 120.0),
                      "Halberd_R24p_LipSeats_Fin_Focus")


@step(out="../STEP/r24p_macro_p.step")
def r24p_macro_p():
    return crop_scene(SAVED, cube_at(_origin("p"), 30.0), "Halberd_R24p_LipSeat_P_Macro")


@step(out="../STEP/r24p_macro_m.step")
def r24p_macro_m():
    return crop_scene(SAVED, cube_at(_origin("m"), 30.0), "Halberd_R24p_LipSeat_M_Macro")


if __name__ == "__main__":
    r24p_fin_focus()
    r24p_macro_p()
    r24p_macro_m()
