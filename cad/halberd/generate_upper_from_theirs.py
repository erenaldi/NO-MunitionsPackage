import cadquery as cq

SRC = r"C:\Users\erena\Downloads\Halberd_Missile_NoIntake - Part 1 V1.step"

solid = cq.importers.importStep(SRC).val()
print("src volume m^3: %.6f" % (solid.Volume() / 1e9))

def region_box(direction, x1, r0=140.8, r1=330.8, lat=40.0):
    dx, dy, dz = direction
    x0 = 2300.0
    if dy != 0:
        y0, y1 = (r0, r1) if dy > 0 else (-r1, -r0)
        return cq.Solid.makeBox(x1 - x0, y1 - y0, 2 * lat, cq.Vector(x0, y0, -lat))
    z0, z1 = (r0, r1) if dz > 0 else (-r1, -r0)
    return cq.Solid.makeBox(x1 - x0, 2 * lat, z1 - z0, cq.Vector(x0, -lat, z0))

directions = [(0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)]
fin_assemblies = []
for d in directions:
    fin = solid.intersect(region_box(d, 2830))
    fin = sorted(fin.Solids(), key=lambda s: s.Volume(), reverse=True)[0]
    pure = solid.intersect(region_box(d, 2735))
    pure = sorted(pure.Solids(), key=lambda s: s.Volume(), reverse=True)[0]
    bb = pure.BoundingBox()
    t = (bb.zmax - bb.zmin) if d[1] != 0 else (bb.ymax - bb.ymin)
    print("fin %s: pure x[%.0f..%.0f] thickness %.2f mm" % (str(d), bb.xmin, bb.xmax, t))
    filler_len = min(bb.xmax, 2735.0) - bb.xmin + 2.0
    if d[1] != 0:
        radial_sign = d[1]
        zc = (bb.zmin + bb.zmax) * 0.5
        r0f, r1f = (128.0, 146.0) if radial_sign > 0 else (-146.0, -128.0)
        filler = cq.Solid.makeBox(filler_len, r1f - r0f, t - 0.6,
                                  cq.Vector(bb.xmin - 1.0, r0f, zc - (t - 0.6) * 0.5))
    else:
        radial_sign = d[2]
        yc = (bb.ymin + bb.ymax) * 0.5
        r0f, r1f = (128.0, 146.0) if radial_sign > 0 else (-146.0, -128.0)
        filler = cq.Solid.makeBox(filler_len, t - 0.6, r1f - r0f,
                                  cq.Vector(bb.xmin - 1.0, yc - (t - 0.6) * 0.5, r0f))
    asm = fin.fuse(filler)
    print("  assembly valid:", asm.isValid(), "solids:", len(asm.Solids()),
          "volume m^3: %.6f" % (asm.Volume() / 1e9))
    fin_assemblies.append(asm.rotate((0, 0, 0), (1, 0, 0), 45))

cutter = cq.Solid.makeBox(2180, 700, 700, cq.Vector(2820, -350, -350))
cutter = cutter.fuse(
    cq.Workplane("XY")
    .polyline([(2735, 139.9), (2825, 139.9), (2825, 250), (2735, 250)])
    .close()
    .revolve(360, (0, 0), (1, 0))
    .val()
)
for d in directions:
    if d[1] != 0:
        y0 = 140.7 if d[1] > 0 else -330.0
        y1 = 330.0 if d[1] > 0 else -140.7
        cutter = cutter.fuse(cq.Solid.makeBox(530, y1 - y0, 50, cq.Vector(2300, y0, -25)))
    else:
        z0 = 140.7 if d[2] > 0 else -330.0
        z1 = 330.0 if d[2] > 0 else -140.7
        cutter = cutter.fuse(cq.Solid.makeBox(530, 50, z1 - z0, cq.Vector(2300, -25, z0)))

upper = solid.cut(cutter)
print("upper valid:", upper.isValid(), "solids:", len(upper.Solids()))
print("upper volume m^3: %.6f" % (upper.Volume() / 1e9))
bb = upper.BoundingBox()
print("upper bbox mm: X %.0f..%.0f Y %.0f..%.0f Z %.0f..%.0f"
      % (bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))

compound = cq.Compound.makeCompound([upper] + fin_assemblies)
print("compound solids:", len(compound.Solids()))
cq.exporters.export(cq.Workplane(obj=compound), "Halberd_UpperStage.step")
print("exported")
