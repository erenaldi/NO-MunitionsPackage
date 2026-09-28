"""Align the continuous intake's end plane to the actual fin-section ridge."""
from halberd_r10_shapes import build_r10, focus, MATERIALS
from halberd_r9_shapes import ROOT_AFT, ROOT_FORWARD, MIDPOINT, TIP_CHORD, ROOT_RADIUS, HEIGHT

# study_shapes.fin puts its maximum-thickness ridge at 45% from the aft edge,
# not at the geometric mid-chord. Follow that line at each radial height.
RIDGE_ROOT_X=ROOT_AFT+.45*(ROOT_FORWARD-ROOT_AFT)
RIDGE_TIP_X=MIDPOINT-TIP_CHORD/2+.45*TIP_CHORD
END_LEAN=(RIDGE_TIP_X-RIDGE_ROOT_X)/HEIGHT
END_ROOF_X=RIDGE_ROOT_X+END_LEAN*(136.-ROOT_RADIUS)


def build_r11(separated=False):
    model=build_r10(separated=separated,end_x=END_ROOF_X,end_lean=END_LEAN)
    model.label="Halberd_R11_Ridge_Aligned"+("_Separated" if separated else "")
    # Stable occurrence labels preserve comparison and material references.
    return model
