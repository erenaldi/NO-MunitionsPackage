import cadquery as cq

SRC = r"C:\Users\erena\Downloads\Halberd_Missile_NoIntake - Part 1 V1.step"

solid = cq.importers.importStep(SRC).val()
print("src volume m^3: %.6f" % (solid.Volume() / 1e9))

capture_full = cq.Solid.makeBox(530, 190, 80, cq.Vector(2300, 140.8, -40))
fin_full = solid.intersect(capture_full)
fin_full_solids = sorted(fin_full.Solids(), key=lambda s: s.Volume(), reverse=True)
fin_full = fin_full_solids[0]
bb_full = fin_full.BoundingBox()
print("captured fin+band: vol %.6f m^3  x[%.0f..%.0f]"
      % (fin_full.Volume() / 1e9, bb_full.xmin, bb_full.xmax))

capture_pure = cq.Solid.makeBox(430, 190, 80, cq.Vector(2300, 140.8, -40))
fin_pure = solid.intersect(capture_pure)
fin_pure_solids = sorted(fin_pure.Solids(), key=lambda s: s.Volume(), reverse=True)
fin_pure = fin_pure_solids[0]
bb = fin_pure.BoundingBox()
print("pure fin: vol %.6f m^3  x[%.0f..%.0f] y[%.1f..%.0f] z[%.3f..%.3f]"
      % (fin_pure.Volume() / 1e9, bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))
fin_thickness = bb.zmax - bb.zmin
print("fin thickness: %.2f mm" % fin_thickness)

filler = cq.Solid.makeBox(
    min(bb.xmax, 2735.0) - bb.xmin + 2.0,
    146.0 - 128.0,
    fin_thickness - 0.6,
    cq.Vector(bb.xmin - 1.0, 128.0, bb.zmin + 0.3),
)
fin_asm = fin_full.fuse(filler)
print("fin assembly valid:", fin_asm.isValid(), "solids:", len(fin_asm.Solids()))

cutter = cq.Solid.makeBox(530, 189, 50, cq.Vector(2300, 141, -25))
cutter = cutter.fuse(cq.Solid.makeBox(530, 189, 50, cq.Vector(2300, -330, -25)))
cutter = cutter.fuse(cq.Solid.makeBox(530, 50, 189, cq.Vector(2300, -25, 141)))
cutter = cutter.fuse(cq.Solid.makeBox(530, 50, 189, cq.Vector(2300, -25, -330)))
body = solid.cut(cutter)
print("after fin removal: volume m^3: %.6f" % (body.Volume() / 1e9))

band = (
    cq.Workplane("XY")
    .polyline([(2740, 140), (2740, 152), (2820, 152), (2820, 140)])
    .close()
    .revolve(360, (0, 0), (1, 0))
    .val()
)

result = body.fuse(band)
for angle in (45, 135, 225, 315):
    result = result.fuse(fin_asm.rotate((0, 0, 0), (1, 0, 0), angle))

print("result valid:", result.isValid(), "solids:", len(result.Solids()))
print("result volume m^3: %.6f" % (result.Volume() / 1e9))
bb = result.BoundingBox()
print("bbox mm: X %.0f Y %.0f Z %.0f" % (bb.xlen, bb.ylen, bb.zlen))

cq.exporters.export(cq.Workplane(obj=result), "Halberd_Missile_XTail.step")
print("exported")
