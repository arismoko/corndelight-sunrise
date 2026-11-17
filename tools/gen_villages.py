#!/usr/bin/env python3
"""Village corn farms (CD-14, CA3): CD's VillageStructures adds four pieces to vanilla's house pools at
server start (MMLib StructuresUtils.addBuildingToPool: a single pool element with processor list
`minecraft:empty`, rigid projection, at the given weight). Here they are `horizon:add_to` pool files.

Usage: gen_villages.py [--check]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data/corn_delight/worldgen/template_pool/village"

# (vanilla pool, [(piece, weight)]) in VillageStructures' call order.
POOLS = [
    ("plains", [("corn_delight:village/houses/plains_small_corn_farm", 3),
                ("corn_delight:village/houses/plains_large_corn_farm", 1)]),
    ("taiga", [("corn_delight:village/houses/taiga_small_corn_farm", 3),
               ("corn_delight:village/houses/taiga_large_corn_farm", 1)]),
]


def render(biome: str, pieces) -> str:
    doc = {
        "horizon:add_to": f"minecraft:village/{biome}/houses",
        "elements": [
            {"weight": w, "element": {"element_type": "minecraft:single_pool_element", "location": loc,
                                      "processors": "minecraft:empty", "projection": "rigid"}}
            for loc, w in pieces
        ],
    }
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main(argv) -> int:
    check = "--check" in argv
    bad = []
    for biome, pieces in POOLS:
        path = OUT / f"{biome}_houses.json"
        text = render(biome, pieces)
        piece_files = [ROOT / "data" / loc.split(":")[0] / "structure" / (loc.split(":")[1] + ".nbt") for loc, _ in pieces]
        bad += [str(p) for p in piece_files if not p.exists()]
        if check:
            if not path.exists() or path.read_text("utf-8") != text:
                bad.append(f"{path} differs")
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, "utf-8")
    if bad:
        print("\n".join(bad))
        return 1
    print(f"villages {'check ok' if check else 'written'}: {len(POOLS)} files")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
