import cadquery as cq

MM = 1000.0

profile = [
    (0.0, 0.0),
    (0.0, 0.14),
    (0.02, 0.148),
    (0.10, 0.148),
    (0.13, 0.14),
    (1.66, 0.14),
    (1.781, 0.0932),
    (1.88, 0.075),
    (1.88, 0.0),
]

pts_mm = [(x * MM, r * MM) for (x, r) in profile]

solid = (
    cq.Workplane("XY")
    .polyline(pts_mm)
    .close()
    .revolve(360, (0, 0), (1, 0))
)

shape = solid.val()
print("valid:", shape.isValid())
print("volume mm^3:", shape.Volume())
print("volume m^3:", shape.Volume() / 1e9)

cq.exporters.export(solid, "Halberd_Booster_Stage2.step")
cq.exporters.export(solid, "Halberd_Booster_Stage2.stl", tolerance=0.05, angularTolerance=0.1)
print("exported")
