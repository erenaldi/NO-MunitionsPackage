"""Review-only crops of the saved R24 model (lip seats on all four rear booster fins).

Fin n: a 120 mm cube centred on the fairing at X -1232, r 140, at the fin clock.
Macro: a 30 mm cube centred on a seat frame origin (from the R24 metadata).
Overview: an X slice -1300..-1170 of the whole model, holding all four rear fins.
Reads the saved R24 STEP only; no geometry is authored (crop rule in cad/shared/review_crop.py).
"""
import json
import sys
from pathlib import Path

from cadgen import step

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from review_crop import crop_scene, cube_at, radial_point, x_window  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SAVED = ROOT / "STEP" / "r24_booster_seats.step"
META = ROOT / "reviews" / "halberd_r24_booster_seats.json"


def _origin(n, side):
    fin = json.loads(META.read_text(encoding="utf-8"))["fins"][f"booster_fin_fairing_{n}"]
    return fin["seats"][f"booster_r24_F11_{n}{side}"]["frame_origin_mm"]


def _fin(n, clock):
    return crop_scene(SAVED, cube_at(radial_point(-1232.0, 140.0, clock), 120.0),
                      f"Halberd_R24_LipSeats_Fin{n}_Focus")


@step(out="../STEP/r24_overview.step")
def r24_overview():
    return crop_scene(SAVED, x_window(-1300.0, -1170.0), "Halberd_R24_RearFins_Overview")


@step(out="../STEP/r24_fin2.step")
def r24_fin2():
    return _fin(2, 135.0)


@step(out="../STEP/r24_fin3.step")
def r24_fin3():
    return _fin(3, 225.0)


@step(out="../STEP/r24_fin4.step")
def r24_fin4():
    return _fin(4, 315.0)


@step(out="../STEP/r24_macro_2p.step")
def r24_macro_2p():
    return crop_scene(SAVED, cube_at(_origin(2, "p"), 30.0), "Halberd_R24_LipSeat_2P_Macro")


@step(out="../STEP/r24_macro_3m.step")
def r24_macro_3m():
    return crop_scene(SAVED, cube_at(_origin(3, "m"), 30.0), "Halberd_R24_LipSeat_3M_Macro")


@step(out="../STEP/r24_macro_4p.step")
def r24_macro_4p():
    return crop_scene(SAVED, cube_at(_origin(4, "p"), 30.0), "Halberd_R24_LipSeat_4P_Macro")


if __name__ == "__main__":
    r24_overview()
    r24_fin2()
    r24_fin3()
    r24_fin4()
    r24_macro_2p()
    r24_macro_3m()
    r24_macro_4p()
