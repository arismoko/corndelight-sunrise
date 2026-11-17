#!/usr/bin/env python3
"""Generate Corn Delight's engine block, item and creative-tab declarations from tools/decl/cd.toml.in (CD-04).

Rows are Corn Delight's values (cited); this script writes them in the base port's declaration forms:
- foods: `minecraft:food` {nutrition, saturation = nutrition × modifier × 2 in float}, `minecraft:consumable`
  (eat 1.6 s default; drinks: drink animation and sound, no particles, as FD's drinks), one `apply_effects` per
  effect (MobEffectInstance defaults), `remainder` = crafting remainder + `use_remainder` + stack 16;
- compost chances as `minecraft:compostable` layers: vanilla's providers where the chance is one of theirs
  (0.3 low, 0.5 low_medium, 0.65 medium, 0.85 medium_high, 1.0 always_add_one), otherwise the same provider shape
  inline (an empty composter always takes a layer, else a 1/0 draw weighted chance : 1 − chance), which is
  1.21.1's ComposterBlock rule;
- fuel as `minecraft:cooking_fuel` (burn time, speed 1); villager food as `minecraft:villager_food`;
- the cob pipe as `minecraft:equippable` (head, equip sound);
- blocks: the row's declaration keys, with shapes given in pixels (corn crop by age × upper half; feasts by
  servings) and block items' components (wild corn's compost chance) on the block.

Keys are checked against the base generator's allowed sets. Usage: gen_cd_decls.py [--check]
"""
from __future__ import annotations

import argparse
import json
import struct
import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import target  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
TABLE = REPO / "tools" / "decl" / "cd.toml.in"
OUT = REPO / "data" / "corn_delight" / target.DECL_DIR
NS = "corn_delight"

BLOCK_KEYS = {"template", "properties", "state_properties", "default_state"}
VANILLA_COMPOST = {
    0.3: "minecraft:compostable/low",
    0.5: "minecraft:compostable/low_medium",
    0.65: "minecraft:compostable/medium",
    0.85: "minecraft:compostable/medium_high",
    1.0: "minecraft:compostable/always_add_one",
}


class DeclError(Exception):
    pass


def f32(x: float) -> float:
    """The shortest decimal that is the same Java float."""
    v = struct.unpack("f", struct.pack("f", x))[0]
    for digits in range(1, 10):
        r = round(v, digits)
        if struct.unpack("f", struct.pack("f", r))[0] == v:
            return r
    return v


def saturation(nutrition: int, modifier: float) -> float:
    """FoodConstants.saturationByModifier: nutrition * modifier * 2.0F, each step in float."""
    m = struct.unpack("f", struct.pack("f", modifier))[0]
    step = struct.unpack("f", struct.pack("f", nutrition * m))[0]
    return f32(step * 2.0)


def compostable(chance: float) -> dict:
    if chance in VANILLA_COMPOST:
        return {"layers": VANILLA_COMPOST[chance]}
    pct = round(chance * 100)
    if abs(pct - chance * 100) > 1e-9:
        raise DeclError(f"compost chance {chance} is not a whole percent")
    return {"layers": {
        "type": "minecraft:number_dispatcher",
        "cases": [{"condition": {"type": "minecraft:match_block", "blocks": "minecraft:composter",
                                 "state": {"level": "0"}}, "value": 1}],
        "default": {"type": "minecraft:weighted_list",
                    "distribution": [{"data": 1, "weight": pct}, {"data": 0, "weight": 100 - pct}]},
    }}


def px(box) -> list[float]:
    return [round(v / 16, 6) for v in box]


def block_decl(name: str, row: dict, items: dict) -> dict:
    out = {k: row[k] for k in ("template", "properties", "state_properties", "default_state") if k in row}
    if "lower_px" in row:
        values = {}
        for age in range(8):
            values[f"{age},false"] = [[0.0, 0.0, 0.0, 1.0, row["lower_px"][age] / 16, 1.0]]
            values[f"{age},true"] = [[0.0, 0.0, 0.0, 1.0, row["upper_px"][age] / 16, 1.0]]
        out["shapes"] = {"properties": ["age", "upper"], "values": values}
        out["collision_shapes"] = {"default": []}
    if "shape" in row:
        out["shapes"] = {"default": [px(b) for b in row["shape"]]}
    if row.get("no_collision"):
        out["collision_shapes"] = {"default": []}
    if "servings_shapes_px" in row:
        s = row["servings_shapes_px"]
        values = {str(n): [px(b) for b in s.get(str(n), s.get("default"))] for n in range(5)}
        out["shapes"] = {"properties": ["servings"], "values": values}
    if row.get("block_item") == "seeds":
        out["item"] = False
        seeds = [i for i, r in items.items() if r.get("block") == name]
        if len(seeds) != 1:
            raise DeclError(f"{name}: expected one item placing it, found {seeds}")
        out["block_item"] = f"{NS}:{seeds[0]}"
    components = {}
    if "compost" in row:
        components["minecraft:compostable"] = compostable(row["compost"])
    if components:
        out["components"] = components
    unknown = set(row) - BLOCK_KEYS - {"source", "lower_px", "upper_px", "block_item", "shape", "no_collision",
                                       "servings_shapes_px", "compost"}
    if unknown:
        raise DeclError(f"blocks.{name}: unknown key(s) {sorted(unknown)}")
    return out


def item_decl(name: str, row: dict) -> dict | None:
    if row.get("kind") == "block":
        return None  # the block's own item
    components: dict = {}
    out: dict = {"template": "minecraft:stick"}
    if "block" in row:
        out["block"] = f"{NS}:{row['block']}"
    if "remainder" in row:
        out["max_stack_size"] = 16
        out["crafting_remainder"] = row["remainder"]
    if "compost" in row:
        components["minecraft:compostable"] = compostable(row["compost"])
    if "fuel" in row:
        components["minecraft:cooking_fuel"] = {"burn_time": row["fuel"], "speed_multiplier": 1.0}
    if "food" in row:
        nutrition, modifier = row["food"]
        components["minecraft:food"] = {"nutrition": nutrition, "saturation": saturation(nutrition, modifier)}
        consumable: dict = {}
        if row.get("drink"):
            consumable.update({"animation": "drink", "sound": "minecraft:entity.generic.drink",
                               "has_consume_particles": False})
        if row.get("effects"):
            consumable["on_consume_effects"] = [{"type": "minecraft:apply_effects", "effects": [
                {"id": e, "duration": d, "amplifier": 0} for e, d in row["effects"]]}]
        components["minecraft:consumable"] = consumable
        if "remainder" in row:
            components["minecraft:use_remainder"] = {"id": row["remainder"]}
    if "villager_food" in row:
        components["minecraft:villager_food"] = {"value": row["villager_food"]}
    if "equip" in row:
        components["minecraft:equippable"] = {"slot": row["equip"]["slot"], "equip_sound": row["equip"]["sound"]}
    unknown = set(row) - {"source", "kind", "block", "remainder", "compost", "fuel", "food", "drink", "effects",
                          "villager_food", "equip"}
    if unknown:
        raise DeclError(f"items.{name}: unknown key(s) {sorted(unknown)}")
    if components:
        out["components"] = components
    return out


def dump(body) -> bytes:
    return (json.dumps(body, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def render() -> dict[str, bytes]:
    with TABLE.open("rb") as f:
        t = tomllib.load(f)
    for section in ("blocks", "items"):
        for name, row in t[section].items():
            if "source" not in row:
                raise DeclError(f"{section}.{name}: missing source citation")
    out = {}
    for name, row in t["blocks"].items():
        out[f"block/{name}.json"] = dump(block_decl(name, row, t["items"]))
    for name, row in t["items"].items():
        if row.get("kind") == "block" and name not in t["blocks"]:
            raise DeclError(f"items.{name}: block item without a block")
        body = item_decl(name, row)
        if body is not None:
            out[f"item/{name}.json"] = dump(body)
    tab = t["tab"]
    out["creative_tab/corn_delight.json"] = dump(
        {"title": tab["title"], "icon": f"{NS}:{tab['icon']}", "items": [f"{NS}:{i}" for i in t["items"]]}
    )
    return out


PICKS_UP = REPO / "data" / "minecraft" / "tags" / "item" / "villager_picks_up.json"


def extra() -> dict[Path, bytes]:
    """Items with villager food: CD gives them to MMLib's villager food map (VillagerUtils.addFoodToVillage), whose
    `wantsToPickUp` makes villagers pick them up. 26.3 says which items villagers pick up with this tag (CA15)."""
    with TABLE.open("rb") as f:
        t = tomllib.load(f)
    foods = [f"{NS}:{n}" for n, row in t["items"].items() if "villager_food" in row]
    out = {PICKS_UP: dump({"values": foods})} if foods else {}
    # The engine's macro names (RETARGET_PLAN D13), from tools/target.toml.in.
    out[REPO / "src" / "engine.rs"] = target.engine_rs()
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    try:
        files = render()
    except (DeclError, tomllib.TOMLDecodeError) as e:
        print(f"gen_cd_decls FAILED: {e}", file=sys.stderr)
        return 1
    present = {p.relative_to(OUT).as_posix() for p in OUT.rglob("*.json")} if OUT.exists() else set()
    stale = sorted(present - set(files))
    if args.check:
        bad = [r for r, b in files.items() if not (OUT / r).exists() or (OUT / r).read_bytes() != b]
        for r in bad + stale:
            print(f"out of date: data/{NS}/{target.DECL_DIR}/{r}", file=sys.stderr)
        bad_extra = [p for p, b in extra().items() if not p.exists() or p.read_bytes() != b]
        for p in bad_extra:
            print(f"out of date: {p.relative_to(REPO)}", file=sys.stderr)
        if bad or stale or bad_extra:
            return 1
        print(f"decl check ok: {len(files)} files")
        return 0
    for rel, body in files.items():
        p = OUT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_bytes() != body:
            p.write_bytes(body)
    for rel in stale:
        (OUT / rel).unlink()
    for p, body in extra().items():
        p.parent.mkdir(parents=True, exist_ok=True)
        if not p.exists() or p.read_bytes() != body:
            p.write_bytes(body)
    print(f"wrote {len(files)} declaration(s), removed {len(stale)} stale")
    return 0


if __name__ == "__main__":
    sys.exit(main())
