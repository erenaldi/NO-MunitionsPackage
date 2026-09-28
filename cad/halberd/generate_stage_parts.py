import math
import cadquery as cq

MM = 1000.0

def ogive_r(x_m):
    R = 0.14
    L = 0.9
    rho = (R * R + L * L) / (2 * R)
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
    .val()
)

fin_pts = [
    (2.325 * MM, 0.136 * MM),
    (2.82 * MM, 0.136 * MM),
    (2.72 * MM, 0.32 * MM),
    (2.50 * MM, 0.32 * MM),
]
fin_up = cq.Workplane("XY").polyline(fin_pts).close().extrude(0.006 * MM, both=True).val()

fins = [fin_up.rotate((0, 0, 0), (1, 0, 0), 45)]
for angle in (135, 225, 315):
    fins.append(fin_up.rotate((0, 0, 0), (1, 0, 0), angle))

upper = cq.Compound.makeCompound([body] + fins)
print("upper stage solids:", len(upper.Solids()))
print("upper valid:", upper.isValid())
print("upper volume m^3: %.6f" % (upper.Volume() / 1e9))
bb = upper.BoundingBox()
print("upper bbox mm: X %.0f Y %.0f Z %.0f" % (bb.xlen, bb.ylen, bb.zlen))
cq.exporters.export(cq.Workplane(obj=upper), "Halberd_UpperStage.step")

booster = cq.Solid.makeCylinder(0.14 * MM, 1.88 * MM, cq.Vector(2.82 * MM, 0, 0), cq.Vector(1, 0, 0))
print("booster valid:", booster.isValid())
print("booster volume m^3: %.6f" % (booster.Volume() / 1e9))
bb = booster.BoundingBox()
print("booster bbox mm: X %.0f Y %.0f Z %.0f" % (bb.xlen, bb.ylen, bb.zlen))
cq.exporters.export(cq.Workplane(obj=booster), "Halberd_Booster_Cylinder.step")
print("exported")
