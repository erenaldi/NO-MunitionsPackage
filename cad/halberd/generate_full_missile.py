import cadquery as cq

MM = 1000.0

def ogive_r(x_m):
    R = 0.14
    L = 0.9
    rho = (R * R + L * L) / (2 * R)
    import math
    return math.sqrt(max(rho * rho - (L - x_m) ** 2, 0.0)) + R - rho

ogive_pts = [(i / 12.0 * 0.9 * MM, ogive_r(i / 12.0 * 0.9) * MM) for i in range(1, 13)]

body = (
    cq.Workplane("XY")
    .moveTo(0, 0)
    .spline(ogive_pts, includeCurrent=True)
    .lineTo(2.82 * MM, 0.14 * MM)
    .lineTo(2.82 * MM, 0)
    .close()
    .revolve(360, (0, 0), (1, 0))
)

booster = (
    cq.Workplane("XY")
    .polyline([
        (2.82 * MM, 0),
        (2.82 * MM, 0.14 * MM),
        (2.84 * MM, 0.148 * MM),
        (2.92 * MM, 0.148 * MM),
        (2.95 * MM, 0.14 * MM),
        (4.48 * MM, 0.14 * MM),
        (4.601 * MM, 0.0932 * MM),
        (4.70 * MM, 0.075 * MM),
        (4.70 * MM, 0),
    ])
    .close()
    .revolve(360, (0, 0), (1, 0))
)

band = (
    cq.Workplane("XY")
    .polyline([
        (2.74 * MM, 0.14 * MM),
        (2.74 * MM, 0.152 * MM),
        (2.82 * MM, 0.152 * MM),
        (2.82 * MM, 0.14 * MM),
    ])
    .close()
    .revolve(360, (0, 0), (1, 0))
)

fin_pts = [
    (2.32 * MM, 0.136 * MM),
    (2.82 * MM, 0.136 * MM),
    (2.72 * MM, 0.32 * MM),
    (2.50 * MM, 0.32 * MM),
]
fin_up = cq.Workplane("XY").polyline(fin_pts).close().extrude(0.006 * MM, both=True)
fins = fin_up
for angle in (90, 180, 270):
    fins = fins.union(fin_up.rotate((0, 0, 0), (1, 0, 0), angle))

airframe = body.union(booster).union(band).union(fins)
shape = airframe.val()
print("valid:", shape.isValid())
print("solids:", len(airframe.solids().vals()))
print("volume m^3:", shape.Volume() / 1e9)

cq.exporters.export(airframe, "Halberd_Missile_NoIntake.step")
print("exported")
