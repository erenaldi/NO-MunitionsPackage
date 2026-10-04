"""Review-only crops of the saved R26 nozzle-recess model (crop rule: cad/shared/review_crop.py)."""
import sys
from pathlib import Path

from cadgen import step

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT.parent / "shared"))
sys.path.insert(0, str(HERE))

import review_crop as rc  # noqa: E402
import halberd_r26_nozzle_recess as r26  # noqa: E402

SAVED = ROOT / "STEP" / "r26_nozzle_recess.step"
_MAT = r26._materials()


def _crop_materials(prefix):
    return {"definitions": {k: _MAT["definitions"][k] for k in ("nozzle_rust", "occlusion")},
            "assignments": [{"targets": [f"#{t}" for t in r26.TARGETS if t.startswith(prefix)],
                             "material": "nozzle_rust"},
                            {"targets": [f"#{prefix}_nozzle_dark_floor"], "material": "occlusion"}]}


@step(out="../STEP/r26_aft_focus.step", materials=_crop_materials("booster"))
def r26_aft_focus():
    return rc.crop_scene(SAVED, rc.x_window(-1700.0, -1440.0), "R26_aft_focus")


@step(out="../STEP/r26_main_focus.step", materials=_crop_materials("main"))
def r26_main_focus():
    return rc.crop_scene(SAVED, rc.x_window(-1135.0, -1060.0), "R26_main_focus")


if __name__ == "__main__":
    r26_aft_focus()
    r26_main_focus()
