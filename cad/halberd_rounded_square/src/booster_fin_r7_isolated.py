"""Rigidly reposition the actual prototype for direct silhouette review."""
from cadgen import build123d as bd, step
from booster_fin_r7_shapes import trapezoid_fin, MIDPOINT, ROOT_RADIUS

@step(out="../STEP/Selected_Booster_Fin_R7.step")
def booster_fin_r7_isolated():
    return trapezoid_fin().rotate(bd.Axis.X,45.).translate((-MIDPOINT,0,-ROOT_RADIUS))

if __name__=="__main__":
    booster_fin_r7_isolated()
