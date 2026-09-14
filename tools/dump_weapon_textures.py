#!/usr/bin/env python3
"""Extract weapon-related textures and a material inventory from Nuclear Option game assets.

Exports the shared weapon atlases (weapons1..5 families) as PNG into
reference/vanilla_textures/ and writes:
  - inventory.json          all Texture2D / Material objects per container
  - materials.json          material -> shader, texture bindings, colors, floats
  - prefabs.json            weapon-prefab GameObject -> renderer -> material mapping
  - placeholder_check.json  exported textures vs Blueprinter _donotship copies

Read-only against the game install; writes only under reference/.
"""

import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

import UnityPy

GAME_DATA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\Nuclear Option\NuclearOption_Data")
REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "reference" / "vanilla_textures"
PLACEHOLDER_DIR = (
    REPO
    / "unity"
    / "BlueprinterEditor"
    / "Blueprinter-Editor"
    / "Assets"
    / "Blueprinter"
    / "_donotship"
    / "Texture2D"
)

TEX_NAME_RE = re.compile(r"^(weapons|missiles\d|bombs\d|ballisticMissile\d)", re.I)
# Vanilla weapon-prefab-ish names for the offline prefab->material pass.
PREFAB_RE = re.compile(
    r"^(AAM\d+|AGM\w*|ARM\d*|AShM\d*|IRMS?\w*|MMR[-_]S\d+|GPO\w*|AGR\w*|rocket\d*|"
    r"bomb\w*|missile\w*|KEM\d*|Piledriver\w*|cruise\w*|ballistic\w*|demolition\w*|"
    r"RAM\d+|Decoy\w*|torpedo\w*|ALND\w*|ALM[-_]?C?\w*|Tusko\w*|Lynchpin\w*|Auger\w*)$",
    re.I,
)


def containers():
    paths = []
    assets = GAME_DATA / "StreamingAssets" / "aa" / "StandaloneWindows64"
    for pattern in ("resources.assets", "sharedassets*.assets"):
        paths.extend(sorted(GAME_DATA.glob(pattern)))
    if assets.is_dir():
        paths.extend(sorted(assets.glob("*.bundle")))
    return [p for p in paths if p.is_file()]


def pair_items(seq, name_attr="m_Name"):
    """UnityPy pair lists arrive as tuples or typed objects; normalize to (name, value)."""
    for item in seq or []:
        if isinstance(item, (tuple, list)) and len(item) == 2:
            yield item[0], item[1]
        else:
            yield getattr(item, name_attr, getattr(item, "first", None)), item


def tex_name_of(pptr, material_names):
    if pptr is None:
        return ""
    try:
        target = pptr.read()
        return getattr(target, "m_Name", "") or ""
    except Exception:
        pid = getattr(pptr, "path_id", None)
        if pid is None:
            return ""
        return material_names.get(pid, "?unresolved:%d" % pid)


def color_dict(c):
    try:
        return {"r": round(c.r, 4), "g": round(c.g, 4), "b": round(c.b, 4), "a": round(c.a, 4)}
    except Exception:
        return str(c)


def main():
    UnityPy.config.FALLBACK_UNITY_VERSION = "2022.3.62f2"
    if not GAME_DATA.is_dir():
        sys.exit("Game data folder not found: %s" % GAME_DATA)
    OUT.mkdir(parents=True, exist_ok=True)

    inventory = {
        "generatedUtc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "containers": {},
    }
    materials_doc = {}
    prefabs_doc = {}
    exported = {}
    errors = []

    for cpath in containers():
        rel = str(cpath.relative_to(GAME_DATA.parent))
        print("scanning %s ..." % rel)
        env = UnityPy.load(str(cpath))
        tex_list = []
        material_names = {}
        material_objs = []
        renderer_by_go = {}
        go_names = {}

        for obj in env.objects:
            tname = obj.type.name
            try:
                if tname == "Texture2D":
                    d = obj.read()
                    name = d.m_Name or "<unnamed>"
                    entry = {
                        "name": name,
                        "width": d.m_Width,
                        "height": d.m_Height,
                        "format": str(d.m_TextureFormat),
                    }
                    tex_list.append(entry)
                    if TEX_NAME_RE.match(name):
                        img = d.image
                        dest = OUT / ("%s.png" % name)
                        img.save(dest)
                        exported[name] = {
                            "container": rel,
                            "width": d.m_Width,
                            "height": d.m_Height,
                            "png": str(dest.relative_to(REPO)),
                            "md5": hashlib.md5(dest.read_bytes()).hexdigest(),
                        }
                        entry["exported"] = True
                elif tname == "Material":
                    d = obj.read()
                    name = d.m_Name or "<unnamed>"
                    material_names[obj.path_id] = name
                    material_objs.append((name, d))
                elif tname in ("MeshRenderer", "SkinnedMeshRenderer"):
                    d = obj.read()
                    go_ptr = d.m_GameObject
                    mats = []
                    for mp in getattr(d, "m_Materials", []) or []:
                        try:
                            mats.append(mp.read().m_Name or "")
                        except Exception:
                            mats.append(material_names.get(mp.path_id, "?unresolved:%d" % mp.path_id))
                    renderer_by_go.setdefault(go_ptr.path_id, []).append(mats)
                elif tname == "GameObject":
                    d = obj.read()
                    go_names[obj.path_id] = d.m_Name or "<unnamed>"
            except Exception as exc:  # per-object failure must not abort the dump
                errors.append({"container": rel, "object": tname, "pathId": obj.path_id, "error": repr(exc)})

        mat_summary = []
        for name, d in material_objs:
            texenvs = {}
            for prop, te in pair_items(getattr(d.m_SavedProperties, "m_TexEnvs", None)):
                if te is not None and not isinstance(te, (tuple, list)):
                    pptr = getattr(te, "m_Texture", getattr(te, "second", None))
                else:
                    pptr = te
                tname_ = tex_name_of(pptr, material_names)
                if tname_:
                    texenvs[prop] = tname_
            colors = {
                prop: color_dict(val)
                for prop, val in pair_items(getattr(d.m_SavedProperties, "m_Colors", None), name_attr="m_Name")
                if prop
            }
            floats = {
                prop: round(val, 4)
                for prop, val in pair_items(getattr(d.m_SavedProperties, "m_Floats", None), name_attr="m_Name")
                if prop
            }
            shader = ""
            try:
                shader = d.m_Shader.read().m_Name or ""
            except Exception:
                pass
            materials_doc["%s@%s" % (name, rel)] = {
                "material": name,
                "container": rel,
                "shader": shader,
                "textures": texenvs,
                "colors": colors,
                "floats": floats,
            }
            mat_summary.append({"name": name, "shader": shader})

        prefab_summary = []
        for path_id, go_name in go_names.items():
            if PREFAB_RE.match(go_name) and path_id in renderer_by_go:
                prefab_summary.append({"gameObject": go_name, "renderers": renderer_by_go[path_id]})
        if prefab_summary:
            prefabs_doc[rel] = prefab_summary

        inventory["containers"][rel] = {
            "textureCount": len(tex_list),
            "materialCount": len(mat_summary),
            "textures": tex_list,
            "materials": mat_summary,
        }
        print("  textures=%d materials=%d exported=%d" % (len(tex_list), len(mat_summary), len(exported)))

    (OUT / "inventory.json").write_text(json.dumps(inventory, indent=1), encoding="utf-8")
    (OUT / "materials.json").write_text(json.dumps(materials_doc, indent=1), encoding="utf-8")
    (OUT / "prefabs.json").write_text(json.dumps(prefabs_doc, indent=1), encoding="utf-8")

    # Cross-check exported textures against Blueprinter placeholder copies.
    checks = []
    for name, info in sorted(exported.items()):
        ph = PLACEHOLDER_DIR / ("%s_PLACEHOLDER.png" % name)
        entry = {"name": name, "exported": info["png"]}
        if ph.is_file():
            entry["placeholder"] = str(ph.relative_to(REPO))
            entry["placeholderBytes"] = ph.stat().st_size
            entry["placeholderMd5"] = hashlib.md5(ph.read_bytes()).hexdigest()
            entry["identicalPng"] = entry["placeholderMd5"] == info["md5"]
        else:
            entry["placeholder"] = None
        checks.append(entry)
    (OUT / "placeholder_check.json").write_text(json.dumps(checks, indent=1), encoding="utf-8")

    print("exported %d textures -> %s" % (len(exported), OUT))
    if errors:
        print("%d object read errors (see inventory errors log)" % len(errors))
        (OUT / "read_errors.json").write_text(json.dumps(errors, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
