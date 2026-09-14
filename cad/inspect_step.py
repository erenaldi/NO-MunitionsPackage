import sys
import cadquery as cq

for path in sys.argv[1:]:
    wp = cq.importers.importStep(path)
    solids = wp.solids().vals()
    shape = cq.Compound.makeCompound(solids)
    bb = shape.BoundingBox()
    print("==", path.split("\\")[-1])
    print("  solids:", len(solids))
    print("  valid:", shape.isValid())
    print("  summed volume m^3: %.6f" % (sum(solid.Volume() for solid in solids) / 1e9))
    print("  bbox mm: X %.1f  Y %.1f  Z %.1f" % (bb.xlen, bb.ylen, bb.zlen))
    print("  bbox min: (%.1f, %.1f, %.1f)" % (bb.xmin, bb.ymin, bb.zmin))
    print("  bbox max: (%.1f, %.1f, %.1f)" % (bb.xmax, bb.ymax, bb.zmax))
    for index, solid in enumerate(solids, start=1):
        solid_bb = solid.BoundingBox()
        center = solid.Center()
        print("  solid %d:" % index)
        print("    volume m^3: %.9f" % (solid.Volume() / 1e9))
        print("    bbox mm: X %.1f  Y %.1f  Z %.1f" % (solid_bb.xlen, solid_bb.ylen, solid_bb.zlen))
        print("    bbox min: (%.1f, %.1f, %.1f)" % (solid_bb.xmin, solid_bb.ymin, solid_bb.zmin))
        print("    bbox max: (%.1f, %.1f, %.1f)" % (solid_bb.xmax, solid_bb.ymax, solid_bb.zmax))
        print("    center: (%.1f, %.1f, %.1f)" % (center.x, center.y, center.z))
