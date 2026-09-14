import sys
import cadquery as cq

def import_union(path):
    solids = cq.importers.importStep(path).solids().vals()
    if not solids:
        raise ValueError("No solids found in %s" % path)
    if len(solids) == 1:
        return solids[0].clean()
    return solids[0].fuse(*solids[1:]).clean()


mine = import_union(sys.argv[1])
theirs = import_union(sys.argv[2])

def report_lumps(name, solid):
    vol = solid.Volume() / 1e9
    print("%s volume m^3: %.6f" % (name, vol))
    lumps = solid.Solids()
    print("%s lumps: %d" % (name, len(lumps)))
    for i, lump in enumerate(lumps):
        bb = lump.BoundingBox()
        print("  lump %d vol %.6f m^3  x[%.0f..%.0f] y[%.0f..%.0f] z[%.0f..%.0f]"
              % (i, lump.Volume() / 1e9, bb.xmin, bb.xmax, bb.ymin, bb.ymax, bb.zmin, bb.zmax))

removed = mine.cut(theirs)
added = theirs.cut(mine)
mine_volume = mine.Volume()
theirs_volume = theirs.Volume()
if (
    mine.distance(theirs) == 0
    and removed.Volume() >= mine_volume * 0.99
    and added.Volume() >= theirs_volume * 0.99
):
    print("boolean difference inconclusive: coincident-face kernel failure")
    print("source volumes m^3: %.9f  %.9f" % (mine_volume / 1e9, theirs_volume / 1e9))
    sys.exit(2)
report_lumps("removed(from mine)", removed)
report_lumps("added(theirs only)", added)
