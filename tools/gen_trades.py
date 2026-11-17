#!/usr/bin/env python3
"""Villager and wandering-trader trades (CD-15) from CD's VillagerTradeHandler, as 26.3 `villager_trade`
data plus tag entries (the base's format: plain ids, E-27).

Reference listings (restated): RandomPriceSellItemListing(item, cost, min, max, uses, xp) wants 1 item and
gives `cost` emeralds — the random count it draws is set on a copy after the cost was built, so it is
never used (CQ3). RandomPriceOrderItemListing(item, cost, min, max, uses, xp) wants
min(cost + 5 + nextInt(15), 64) emeralds and gives nextInt(min, max + 1) items. Price multiplier 0.05.
Farmer trades need FD's farmersBuyFDCrops (always true in FD 26.3, CA9) and CD's villagersTradeCorn
(`ported_corn_delight:villagers_trade_corn` on the tag files); the wandering trades are ungated and both
go to the generic pool (CQ4).

The random give count is written as vanilla would read it (a `minecraft:set_count` given-item modifier);
this engine ignores that modifier (E-41), so `gives.count` holds the range's midpoint (CA4).

Usage: gen_trades.py [--check]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONDITION = "ported_corn_delight:villagers_trade_corn"


def sell(item, cost, uses, xp):
    return {"wants": {"id": item}, "gives": {"id": "minecraft:emerald", "count": cost},
            "max_uses": uses, "xp": xp, "reputation_discount": 0.05}


def order(item, cost, lo, hi, uses, xp):
    mid = (lo + hi + 1) // 2
    return {"wants": {"id": "minecraft:emerald",
                      "count": {"type": "minecraft:uniform", "min": min(cost + 5, 64), "max": min(cost + 19, 64)}},
            "gives": {"id": item, "count": mid},
            "given_item_modifier": [{"type": "minecraft:set_count",
                                     "count": {"type": "minecraft:uniform", "min": lo, "max": hi}}],
            "max_uses": uses, "xp": xp, "reputation_discount": 0.05}


# (trade id, data, tag file) in VillagerTradeHandler's order.
TRADES = [
    ("farmer/1/corn_emerald", sell("corn_delight:corn", 1, 16, 2), "farmer/level_1"),
    ("farmer/1/corn_emerald_2", sell("corn_delight:corn", 1, 16, 2), "farmer/level_1"),
    ("farmer/2/emerald_cornbread", order("corn_delight:cornbread", 1, 6, 16, 16, 5), "farmer/level_2"),
    ("farmer/2/emerald_tortilla", order("corn_delight:tortilla", 1, 6, 16, 16, 5), "farmer/level_2"),
    ("wandering_trader/emerald_corn_seeds", order("corn_delight:corn_seeds", 1, 2, 8, 16, 2), "wandering_trader/common"),
    ("wandering_trader/emerald_popcorn_box", order("corn_delight:popcorn_box", 2, 1, 2, 16, 15), "wandering_trader/common"),
]


def dump(v) -> str:
    return json.dumps(v, indent=2, ensure_ascii=False) + "\n"


def files() -> dict[Path, str]:
    out: dict[Path, str] = {}
    tags: dict[str, list[str]] = {}
    for tid, data, tag in TRADES:
        out[DATA / "corn_delight/villager_trade" / f"{tid}.json"] = dump(data)
        tags.setdefault(tag, []).append(f"corn_delight:{tid}")
    for tag, values in tags.items():
        doc = {"values": values}
        if tag.startswith("farmer/"):
            doc = {"neoforge:conditions": [{"type": CONDITION}], **doc}
        out[DATA / "minecraft/tags/villager_trade" / f"{tag}.json"] = dump(doc)
    return out


def main(argv) -> int:
    check = "--check" in argv
    bad = []
    for path, text in files().items():
        if check:
            if not path.exists() or path.read_text("utf-8") != text:
                bad.append(f"{path.relative_to(ROOT)} differs")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, "utf-8")
    if bad:
        print("\n".join(bad))
        return 1
    print(f"trades {'check ok' if check else 'written'}: {len(files())} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
