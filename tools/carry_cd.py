#!/usr/bin/env python3
"""Deterministically carry Corn Delight's data and assets into this repo, uplifted from 1.21.1 to 26.3
(ADDONS_PLAN §5.4, CD-03).

Usage:
  carry_cd.py --cd <Corn-Delight checkout> --base <farmersdelight-horizon checkout> --vanilla <26.3 client jar>
  carry_cd.py ... --check          # verify the repo matches (CI)
  carry_cd.py ... --out <dir>      # write into another tree

Rules (tools/carry_rules_cd.toml.in): byte copies; asset upgrade; R1–R4 recipes (1.21.1 ingredient objects →
26.3 strings, `neoforge:compound` kept in vanilla recipes and written as `fabric:any` in FD recipes, cutting tools
as `#tag`); R5 prune of undefined tag alternatives; R6 advancements (`recipe_unlocked.recipe` → `recipes`, display
background as an asset id) and loot tables (port-pack's 26.3 shape: `condition`/`modifier`/`type`;
`block_state_property` → `match_block`); R7 client item definitions; R8 worldgen through the base's
`worldgen_rewrite.py` (BX-09); R9 overlay entries and drops; R10 26.3 block tag renames in worldgen predicates. Every tag a carried file references must be defined by
vanilla 26.3, the base or this output. The overlay goes to tools/overlay/corn_delight.json for the base carry
(BX-02); the uplift report (every rewritten file and its rules) to tools/uplift_report.md.
The base's carry_lib.py / worldgen_rewrite.py are imported from the --base checkout at the pinned commit.
"""
from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
import sys
import tempfile
import tomllib
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
RULES = REPO / "tools" / "carry_rules_cd.toml.in"
MANIFEST_REL = "tools/carry_manifest.json"
OVERLAY_REL = "tools/overlay/corn_delight.json"
REPORT_REL = "tools/uplift_report.md"
OWNED = {"corn_delight"}
NS = "corn_delight"
lib = None  # carry_lib from the base checkout
wg = None  # worldgen_rewrite from the base checkout


def load_base(base: Path, pinned: str):
    global lib, wg
    sys.path.insert(0, str(base / "tools"))
    import carry_lib  # noqa: E402
    import worldgen_rewrite  # noqa: E402

    lib, wg = carry_lib, worldgen_rewrite
    head = lib.git_head(base)
    if head != pinned:
        raise SystemExit(f"base checkout is at {head}, rules pin {pinned}")


# ---------------------------------------------------------------- ingredients (R1–R5)


class Uplift:
    """Per-file notes of what was rewritten (for the report)."""

    def __init__(self, prune: set[str]):
        self.prune = prune
        self.notes: list[str] = []
        self.pruned: list[str] = []

    def note(self, what: str):
        if what not in self.notes:
            self.notes.append(what)


def simple(v, up: Uplift):
    """A 1.21.1 `{"item": id}` / `{"tag": t}` → "id" / "#t" (port-pack `ingredient`); strings stay."""
    if isinstance(v, str):
        return v
    if isinstance(v, dict) and len(v) == 1:
        if isinstance(v.get("item"), str):
            up.note("R1 ingredient objects")
            return v["item"]
        if isinstance(v.get("tag"), str):
            up.note("R1 ingredient objects")
            return "#" + v["tag"]
    raise lib.CarryError(f"ingredient without a 26.3 form: {json.dumps(v)}")


def alternatives(children, up: Uplift) -> list:
    out = []
    for c in children:
        s = ingredient(c, up, nested=True)
        if isinstance(s, str) and s.startswith("#") and s[1:] in up.prune:
            up.note("R5 pruned undefined tag")
            up.pruned.append(s)
            continue
        out.append(s)
    return out


def ingredient(v, up: Uplift, fd: bool = False, nested: bool = False):
    """One ingredient. `fd`: inside an FD recipe (compound → `fabric:any`); vanilla keeps `neoforge:compound`."""
    if isinstance(v, dict) and v.get("type") == "neoforge:compound":
        kids = alternatives(v["children"], up)
        if fd:
            up.note("R3 neoforge:compound → fabric:any")
            return {"fabric:type": "fabric:any", "ingredients": kids}
        up.note("R2 neoforge:compound kept (children per R1)")
        return {"type": "neoforge:compound", "children": kids}
    if isinstance(v, list):
        up.note("R1 ingredient list")
        kids = alternatives(v, up)
        return kids[0] if len(kids) == 1 else kids
    return simple(v, up)


def upgrade_recipe(r: dict, up: Uplift) -> dict:
    r = copy.deepcopy(r)
    kind = r.get("type", "")
    fd = kind.startswith("farmersdelight:")
    if not (fd or kind.startswith("minecraft:")):
        raise lib.CarryError(f"unknown recipe type {kind}")
    if "key" in r:
        r["key"] = {k: ingredient(v, up) for k, v in r["key"].items()}
    if "ingredients" in r:
        r["ingredients"] = [ingredient(v, up, fd=fd) for v in r["ingredients"]]
    for field in ("ingredient", "base", "addition", "template"):
        if field in r:
            r[field] = ingredient(r[field], up)
    if kind == "farmersdelight:cutting" and "tool" in r:
        tool = r["tool"]
        if isinstance(tool, dict) and set(tool) == {"tag"}:
            r["tool"] = "#" + tool["tag"]
            up.note("R4 cutting tool tag → #tag")
        elif not isinstance(tool, str):
            r["tool"] = ingredient(tool, up)
    return r


# ---------------------------------------------------------------- advancements and loot (R6)


def upgrade_advancement(a: dict, up: Uplift) -> dict:
    a = copy.deepcopy(a)
    for c in a.get("criteria", {}).values():
        trig = c.get("trigger", "")
        cond = c.get("conditions", {})
        if trig == "minecraft:recipe_unlocked" and "recipe" in cond:
            cond["recipes"] = cond.pop("recipe")
            up.note("R6 recipe_unlocked recipe → recipes")
        elif trig in ("minecraft:enter_block",) and "block" in cond and "blocks" not in cond:
            cond["blocks"] = cond.pop("block")
            up.note("R6 enter_block block → blocks")
        elif trig not in ("minecraft:inventory_changed", "minecraft:recipe_unlocked"):
            raise lib.CarryError(f"advancement trigger without a checked 26.3 form: {trig}")
    bg = a.get("display", {}).get("background")
    if isinstance(bg, str):
        m = re.fullmatch(r"([a-z0-9_.-]+):textures/(.+)\.png", bg)
        if m:
            a["display"]["background"] = f"{m.group(1)}:{m.group(2)}"
            up.note("R6 display background texture path → asset id")
    return a


def type_number(n):
    if isinstance(n, dict):
        if "type" not in n and "min" in n and "max" in n:
            n["type"] = "minecraft:uniform"
        for k in ("min", "max", "n", "p"):
            if k in n:
                type_number(n[k])


NAMED_TOOL = {
    "silk": "minecraft:tool/can_silk_touch",
}


def named_tool(pred) -> str | None:
    """Port-pack's named tool conditions: silk touch alone, shears alone."""
    if not isinstance(pred, dict):
        return None
    if set(pred) == {"predicates"} and set(pred["predicates"]) == {"minecraft:enchantments"}:
        lst = pred["predicates"]["minecraft:enchantments"]
        if (
            len(lst) == 1
            and lst[0].get("enchantments") == "minecraft:silk_touch"
            and lst[0].get("levels", {}).get("min", 1) <= 1
            and "max" not in lst[0].get("levels", {})
        ):
            return "minecraft:tool/can_silk_touch"
    if set(pred) == {"items"} and pred["items"] in ("minecraft:shears", ["minecraft:shears"]):
        return "minecraft:tool/can_shear"
    return None


def upgrade_condition(c, up: Uplift, renames: dict):
    if isinstance(c, dict) and "condition" in c and "type" not in c:
        c["type"] = c.pop("condition")
    if not isinstance(c, dict):
        return c
    if "term" in c:
        c["term"] = upgrade_condition(c["term"], up, renames)
    if "terms" in c:
        c["terms"] = [upgrade_condition(t, up, renames) for t in c["terms"]]
    t = c.get("type")
    if t in renames:
        c["type"] = renames[t]
        up.note(f"R6 loot condition {t} → {renames[t]}")
    if t == "minecraft:block_state_property":
        out = {"type": "minecraft:match_block", "blocks": c["block"]}
        if "properties" in c:
            out["state"] = c["properties"]
        up.note("R6 block_state_property → match_block")
        return out
    if t == "minecraft:match_tool":
        named = named_tool(c.get("predicate"))
        if named:
            up.note("R6 match_tool → named tool condition")
            return named
    return c


def rename_block_tags(v, renames: dict, up: Uplift):
    """R10: `matching_block_tag` predicates naming a block tag 26.3 split get the 26.3 tag."""
    if isinstance(v, list):
        return [rename_block_tags(x, renames, up) for x in v]
    if not isinstance(v, dict):
        return v
    out = {k: rename_block_tags(x, renames, up) for k, x in v.items()}
    if out.get("type") == "minecraft:matching_block_tag" and out.get("tag") in renames:
        up.note(f"R10 block tag {out['tag']} → {renames[out['tag']]}")
        out["tag"] = renames[out["tag"]]
    return out


def one_or_list(lst):
    return lst[0] if len(lst) == 1 else lst


def upgrade_loot(v, up: Uplift, renames: dict):
    if isinstance(v, list):
        return [upgrade_loot(x, up, renames) for x in v]
    if not isinstance(v, dict):
        return v
    o = {}
    for k, x in v.items():
        if k == "conditions" and isinstance(x, list):
            conds = [upgrade_condition(copy.deepcopy(c), up, renames) for c in x]
            o["condition"] = conds[0] if len(conds) == 1 else {"type": "minecraft:all_of", "terms": conds}
            up.note("R6 loot conditions → condition")
        elif k == "functions" and isinstance(x, list):
            mods = []
            for f in x:
                f = copy.deepcopy(f)
                if "function" in f and "type" not in f:
                    f["type"] = f.pop("function")
                for key in ("count", "damage", "levels", "amplifier"):
                    if key in f:
                        type_number(f[key])
                if "conditions" in f:
                    f = upgrade_loot(f, up, renames)
                mods.append(f)
            o["modifier"] = one_or_list(mods)
            up.note("R6 loot functions → modifier")
        elif k in ("rolls", "bonus_rolls"):
            type_number(x)
            o[k] = x
        else:
            o[k] = upgrade_loot(x, up, renames)
    return o


# ---------------------------------------------------------------- assets


def upgrade_asset(v, up: Uplift, renames: dict | None = None):
    """Port-pack `renamed_assets` (no renamed vanilla id appears in CD) + typed variant fields + FD asset renames."""
    renames = renames or {}
    if isinstance(v, str):
        if v in renames:
            up.note(f"R6 FD asset {v} → {renames[v]}")
            return renames[v]
        return v
    if isinstance(v, list):
        return [upgrade_asset(x, up, renames) for x in v]
    if not isinstance(v, dict):
        return v
    o = {}
    for k, x in v.items():
        if "model" in v and k in ("x", "y", "weight") and isinstance(x, str):
            o[k] = int(x)
            up.note("R6 typed block state variant fields")
        elif "model" in v and k == "uvlock" and isinstance(x, str):
            o[k] = x == "true"
            up.note("R6 typed block state variant fields")
        else:
            o[k] = upgrade_asset(x, up, renames)
    if isinstance(o.get("parent"), str) and o["parent"].removeprefix("minecraft:") == "block/template_farmland":
        raise lib.CarryError("template_farmland model needs port-pack's farmland rewrite")
    return o


def item_ids(java: str) -> list[str]:
    """Item registrations of ItemRegistry.java in order (`ITEMS.register("x"` / `register("x"`)."""
    ids = []
    for line in java.splitlines():
        if line.lstrip().startswith("//"):
            continue
        ids += re.findall(r'\bregister\("([a-z0-9_]+)"', line)
    return ids


def item_definition(item: str, rules: dict) -> dict:
    special = rules["item_definitions"]["special"]
    flat = {"type": "minecraft:model", "model": f"{NS}:item/{item}"}
    if item not in special:
        return {"model": flat}
    return {
        "model": {
            "type": "minecraft:select",
            "property": "minecraft:display_context",
            "cases": [{"when": rules["item_definitions"]["flat_contexts"], "model": flat}],
            "fallback": {"type": "minecraft:model", "model": f"{NS}:item/{special[item]}"},
        }
    }


def asset_refs(rel: str, obj) -> set[tuple[str, str]]:
    """(kind, "ns:path") references of a block state, item definition or model: models and textures."""
    refs: set[tuple[str, str]] = set()

    def walk(v, key=None, in_textures=False):
        if isinstance(v, dict):
            for k, x in v.items():
                walk(x, k, in_textures or k == "textures")
        elif isinstance(v, list):
            for x in v:
                walk(x, key, in_textures)
        elif isinstance(v, str) and not v.startswith("#"):
            if in_textures:
                refs.add(("textures", v))
            elif key in ("model", "parent") and "/" in v:
                refs.add(("models", v))
    walk(obj)
    return refs


def unresolved_assets(out: Path, dests, base: Path, vanilla: Path) -> dict[str, list[str]]:
    """Model and texture references of the carried assets that neither vanilla 26.3, the base nor this output has.
    Vanilla's builtin parents (`builtin/…`, `item/generated`'s chain) are files in the jar too."""
    import zipfile

    with zipfile.ZipFile(vanilla) as z:
        have = set(z.namelist())
    def exists(kind: str, ref: str) -> bool:
        ns, path = ref.split(":", 1) if ":" in ref else ("minecraft", ref)
        if path.startswith("builtin/"):
            return True
        ext = ".png" if kind == "textures" else ".json"
        rel = f"assets/{ns}/{kind}/{path}{ext}"
        return rel in have or (base / rel).exists() or (out / rel).exists()
    bad = {}
    for d in dests:
        if d.startswith(f"assets/{NS}/") and d.endswith(".json") and "/lang/" not in d:
            missing = sorted(r for k, r in asset_refs(d, json.loads((out / d).read_text("utf-8"))) if not exists(k, r))
            if missing:
                bad[d] = missing
    return bad


# ---------------------------------------------------------------- the carry


def classify(rel: str, rules: dict) -> str:
    hits = []
    if any(rel == w["from"] for w in rules["worldgen"]):
        hits.append("worldgen")
    if any(rel == r["path"] for r in rules["overlay_tag"]):
        hits.append("overlay")
    if any(fnmatch.fnmatchcase(rel, d["glob"]) for d in rules["drop"]):
        hits.append("drop")
    if any(fnmatch.fnmatchcase(rel, p) for p in rules["exclude"]["patterns"]):
        hits.append("exclude")
    for kind in ("copy", "asset", "recipe", "advancement", "loot"):
        if any(rel.startswith(p) for p in rules[kind]["prefixes"]):
            hits.append(kind)
    # An excluded integration recipe also matches the recipe prefix; exclusion wins there.
    if hits == ["exclude", "recipe"]:
        hits = ["exclude"]
    if len(hits) != 1:
        raise lib.CarryError(f"{rel}: matches {hits or 'no'} rule(s); exactly one expected")
    return hits[0]


def carry(cd: Path, out: Path, rules: dict, base: Path, vanilla: Path):
    files = lib.collect(cd, rules["source"]["roots"], [""], [])
    entries, log, overlay_entries, report = [], [], [], []
    prune = set(rules["prune"]["tags"])
    renames = {r["from"]: r["to"] for r in rules.get("loot_condition_rename", [])}

    def emit(dest: str, data: bytes, src: str, src_data: bytes, rule: str):
        p = out / dest
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_bytes() != data:
            p.write_bytes(data)
        entries.append(
            {"source": src, "dest": dest, "sha256_source": lib.sha256(src_data),
             "sha256_dest": lib.sha256(data), "rule": rule}
        )

    def emit_json(dest, obj, src, src_data, rule, up: Uplift, original):
        if obj == original and not up.notes:
            emit(dest, src_data, src, src_data, "copy")
            return
        emit(dest, lib.dump_json(obj), src, src_data, rule)
        line = f"- `{dest}`: " + "; ".join(up.notes or ["reformatted"])
        if up.pruned:
            line += f" (pruned {', '.join(sorted(set(up.pruned)))})"
        report.append(line)

    for rel in sorted(files):
        root, path = files[rel]
        data = path.read_bytes()
        src = f"{root}/{rel}"
        kind = classify(rel, rules)
        up = Uplift(prune)
        if kind == "copy":
            emit(rel, data, src, data, "copy")
        elif kind in ("asset", "recipe", "advancement", "loot"):
            obj = json.loads(data.decode("utf-8"))
            new = {
                "asset": lambda o: upgrade_asset(o, up, rules.get("asset_rename", {})),
                "recipe": lambda o: upgrade_recipe(o, up),
                "advancement": lambda o: upgrade_advancement(o, up),
                "loot": lambda o: upgrade_loot(o, up, renames),
            }[kind](obj)
            emit_json(rel, new, src, data, kind, up, obj)
        elif kind == "worldgen":
            w = next(w for w in rules["worldgen"] if w["from"] == rel)
            obj = json.loads(data.decode("utf-8"))
            if w["kind"] == "wild_crop":
                new, _ = wg.wild_crop_to_vanilla(obj)
                up.note("R8 farmersdelight:wild_crop → minecraft:overlay (FD 26.3 shape)")
            elif w["kind"] == "placed":
                feature = json.loads((cd / files[w["feature"]][0] / w["feature"]).read_text("utf-8"))
                _, tries = wg.wild_crop_to_vanilla(feature)
                new = wg.placed_with_count(wg.drop_biome_tag(obj), tries)
                up.note(f"R8 biome_tag dropped, count {tries} after in_square")
            else:
                new = wg.biome_filter_to_neoforge(obj)
                up.note("R8 add_features_by_filter → neoforge:add_features")
            new = rename_block_tags(new, {r["from"]: r["to"] for r in rules.get("block_tag_rename", [])}, up)
            emit_json(w["to"], new, src, data, "worldgen", up, None)
        elif kind == "overlay":
            r = next(r for r in rules["overlay_tag"] if r["path"] == rel)
            ids = [v if isinstance(v, str) else v["id"] for v in json.loads(data)["values"]]
            overlay_entries.append(
                {"tag": r["tag"], "kind": r["kind"], "ids": ids,
                 "source": {"repo": rules["source"]["repo"], "commit": rules["source"]["sha"], "file": src,
                            "sha256": lib.sha256(data)}}
            )
            log.append(f"overlay {rel} -> {r['tag']} ({r['kind']}, {len(ids)} ids)")
        elif kind == "drop":
            d = next(d for d in rules["drop"] if fnmatch.fnmatchcase(rel, d["glob"]))
            log.append(f"dropped {rel}: {d['why']}")
        for c in rules.get("copy_as", []):
            if rel == c["from"]:
                emit(c["to"], data, src, data, "copy_as")

    # Generated suspicious-stew recipes (vanilla 26.3's per-flower form).
    for st in rules.get("stew_recipe", []):
        body = {"type": "minecraft:crafting_shapeless", "group": "suspicious_stew",
                "ingredients": ["minecraft:bowl", "#minecraft:mushrooms", "#minecraft:mushrooms", st["flower"]],
                "result": {"components": {"minecraft:suspicious_stew_effects": [
                    {"duration": st["duration"], "id": st["effect"]}]}, "id": "minecraft:suspicious_stew"}}
        rules_bytes = RULES.read_bytes()
        emit(st["dest"], lib.dump_json(body), "tools/carry_rules_cd.toml.in", rules_bytes, "stew_recipe")

    # R7: item definitions.
    java_rel = rules["source"]["item_registry"]
    java = (cd / java_rel).read_bytes()
    items = item_ids(java.decode("utf-8"))
    for item in items:
        body = lib.dump_json(item_definition(item, rules))
        emit(f"assets/{NS}/items/{item}.json", body, java_rel, java, "item_definition")

    overlay = {
        "addon": NS,
        "note": "Generated by corndelight-horizon tools/carry_cd.py; copy into the base's tools/addon_overlays/.",
        "entries": overlay_entries,
    }
    overlay_bytes = (json.dumps(overlay, indent=2) + "\n").encode("utf-8")
    p = out / OVERLAY_REL
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(overlay_bytes)

    dests = [e["dest"] for e in entries]
    if len(set(dests)) != len(dests):
        raise lib.CarryError("two rules wrote the same destination")
    bad = lib.fence_violations(dests, OWNED)
    if bad:
        raise lib.CarryError(f"outside the namespace fence: {bad}")
    broken = unresolved_assets(out, dests, base, vanilla)
    if broken:
        raise lib.CarryError(f"unresolved model/texture references: {broken}")
    defined = lib.tags_in_zip(vanilla) | lib.tags_in_tree(base) | lib.tags_in_rels(dests)
    refs = {}
    for d in dests:
        if d.startswith("data/") and d.endswith(".json"):
            r = lib.tag_references(json.loads((out / d).read_text("utf-8")))
            if r:
                refs[d] = r
    missing = lib.undefined_tags(refs, defined)
    if missing:
        raise lib.CarryError(f"undefined tags: {missing}")

    text = ["# Corn Delight uplift report (generated by tools/carry_cd.py; do not edit)", "",
            f"Source `{rules['source']['repo']}` @ `{rules['source']['sha']}`; base @ `{rules['base']['sha']}`.", "",
            "## Rewritten files", ""] + report + ["", "## Not carried as files", ""] + [f"- {x}" for x in log] + [""]
    report_bytes = "\n".join(text).encode("utf-8")
    p = out / REPORT_REL
    p.write_bytes(report_bytes)

    manifest = {
        "cd_repo": rules["source"]["repo"],
        "cd_sha": rules["source"]["sha"],
        "base_sha": rules["base"]["sha"],
        "rules_sha256": lib.sha256(RULES.read_bytes()),
        "overlay_sha256": lib.sha256(overlay_bytes),
        "report_sha256": lib.sha256(report_bytes),
        "items": items,
        "log": log,
        "files": sorted(entries, key=lambda e: e["dest"]),
    }
    return manifest, log


COUNTS = (
    ("assets/corn_delight/items/", "item definitions"),
    ("assets/corn_delight/blockstates/", "blockstates"),
    ("assets/corn_delight/models/", "models"),
    ("assets/corn_delight/textures/", "textures"),
    ("assets/corn_delight/lang/", "lang"),
    ("data/corn_delight/recipe/", "recipes"),
    ("data/corn_delight/advancement/", "advancements"),
    ("data/corn_delight/loot_table/", "loot tables"),
    ("data/corn_delight/structure/", "structures"),
    ("data/corn_delight/worldgen/", "worldgen"),
    ("data/corn_delight/neoforge/", "biome modifiers"),
    ("data/c/tags/", "c tag files"),
    ("data/minecraft/tags/", "minecraft tag files"),
)


def counts(manifest: dict) -> list[tuple[str, int]]:
    c: Counter[str] = Counter()
    for e in manifest["files"]:
        for prefix, name in COUNTS:
            if e["dest"].startswith(prefix):
                c[name] += 1
        c[f"rule {e['rule']}"] += 1
    c["total files"] = len(manifest["files"])
    return sorted(c.items())


def check(args, rules) -> int:
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        manifest, _ = carry(args.cd, t, rules, args.base, args.vanilla)
        lib.write_manifest(t / MANIFEST_REL, manifest)
        problems = []
        for rel in (MANIFEST_REL, OVERLAY_REL, REPORT_REL):
            if not (REPO / rel).exists() or (REPO / rel).read_bytes() != (t / rel).read_bytes():
                problems.append(f"{rel} differs")
        for e in manifest["files"]:
            ours = REPO / e["dest"]
            if not ours.exists():
                problems.append(f"missing {e['dest']}")
            elif lib.sha256(ours.read_bytes()) != e["sha256_dest"]:
                problems.append(f"drift {e['dest']}")
    for p in problems[:50]:
        print(p, file=sys.stderr)
    if problems:
        print(f"carry check FAILED: {len(problems)} problem(s)", file=sys.stderr)
        return 1
    print(f"carry check ok: {len(manifest['files'])} files")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cd", required=True, type=Path)
    ap.add_argument("--base", required=True, type=Path)
    ap.add_argument("--vanilla", required=True, type=Path, help="minecraft 26.3 client jar (read as a zip)")
    ap.add_argument("--out", type=Path, default=REPO)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    with RULES.open("rb") as f:
        rules = tomllib.load(f)
    load_base(args.base, rules["base"]["sha"])
    head = lib.git_head(args.cd)
    if head != rules["source"]["sha"]:
        print(f"Corn Delight checkout is at {head}, rules pin {rules['source']['sha']}", file=sys.stderr)
        return 2
    try:
        if args.check:
            return check(args, rules)
        old = lib.read_manifest(args.out / MANIFEST_REL)
        manifest, log = carry(args.cd, args.out, rules, args.base, args.vanilla)
        stale = lib.remove_stale(args.out, old, manifest)
        lib.write_manifest(args.out / MANIFEST_REL, manifest)
    except lib.CarryError as e:
        print(f"carry FAILED: {e}", file=sys.stderr)
        return 1
    for line in log:
        print(line)
    for name, n in counts(manifest):
        print(f"{name:22} {n}")
    if stale:
        print(f"removed {len(stale)} stale file(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
