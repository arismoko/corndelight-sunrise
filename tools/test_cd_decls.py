#!/usr/bin/env python3
"""CD-04 fixture: tools/decl/cd.toml.in against values read from Corn Delight's sources (ItemRegistry.java, the
generated data maps), and the generator's output forms. Reads the CD checkout at ../sources/Corn-Delight (read only)."""
import json
import re
import sys
import tomllib
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen_cd_decls as g  # noqa: E402

CD = HERE.parent.parent / "sources" / "Corn-Delight"
REG = CD / "src/main/java/cn/mcmod/corn_delight/item/ItemRegistry.java"
MAPS = CD / "src/generated/resources/data/neoforge/data_maps/item"
DURATIONS = {"BRIEF": 600, "SHORT": 1200, "MEDIUM": 3600, "LONG": 6000}
EFFECTS = {"ModEffects.COMFORT": "farmersdelight:comfort", "ModEffects.NOURISHMENT": "farmersdelight:nourishment",
           "MobEffects.REGENERATION": "minecraft:regeneration", "MobEffects.DAMAGE_BOOST": "minecraft:strength"}


def registry() -> dict:
    """name -> {food, effects, remainder, drink} from ItemRegistry.java's register(...) blocks."""
    text = REG.read_text("utf-8")
    out = {}
    for m in re.finditer(r'register\("([a-z_]+)"(.*?)\);\n', text, re.S):
        name, body = m.group(1), m.group(2)
        row = {}
        if f := re.search(r"amountAndCalories\((\d+),\s*([\d.]+)F\)", body):
            row["food"] = [int(f.group(1)), float(f.group(2))]
        effects = re.findall(r"MobEffectInstance\(([\w.]+),\s*FoodValues\.(\w+)_DURATION", body)
        if effects:
            row["effects"] = [[EFFECTS[e], DURATIONS[d]] for e, d in effects]
        if c := re.search(r"build\(\),\s*Items\.(\w+)\)", body):
            row["remainder"] = "minecraft:" + c.group(1).lower()
        if "drink(" in body:
            row["drink"] = True
        out[name] = row
    return out


class Table(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with g.TABLE.open("rb") as f:
            cls.t = tomllib.load(f)
        cls.reg = registry()

    def test_items_in_registry_order(self):
        self.assertEqual(list(self.t["items"]), list(self.reg))
        self.assertEqual(len(self.reg), 26)

    def test_food_values_effects_containers(self):
        for name, src in self.reg.items():
            row = self.t["items"][name]
            for key in ("food", "effects", "remainder"):
                self.assertEqual(row.get(key), src.get(key), f"{name}.{key}")
            self.assertEqual(bool(row.get("drink")), bool(src.get("drink")), name)

    def test_data_maps(self):
        comp = json.loads((MAPS / "compostables.json").read_text())["values"]
        fuel = json.loads((MAPS / "furnace_fuels.json").read_text())["values"]
        ours = {f"corn_delight:{n}": r["compost"] for sec in ("items", "blocks")
                for n, r in self.t[sec].items() if "compost" in r}
        self.assertEqual(ours, {k: v["chance"] for k, v in comp.items()})
        self.assertEqual({f"corn_delight:{n}": r["fuel"] for n, r in self.t["items"].items() if "fuel" in r},
                         {k: v["burn_time"] for k, v in fuel.items()})


class Forms(unittest.TestCase):
    def test_saturation_is_java_float(self):
        self.assertEqual(g.saturation(2, 0.2), 0.8)
        self.assertEqual(g.saturation(12, 0.8), 19.2)
        self.assertEqual(g.saturation(8, 0.9), 14.4)

    def test_compost_providers(self):
        self.assertEqual(g.compostable(0.65), {"layers": "minecraft:compostable/medium"})
        inline = g.compostable(0.25)["layers"]
        self.assertEqual(inline["default"]["distribution"], [{"data": 1, "weight": 25}, {"data": 0, "weight": 75}])
        self.assertEqual(inline["cases"][0]["value"], 1)

    def test_outputs(self):
        files = g.render()
        self.assertEqual(sum(1 for k in files if k.startswith("block/")), 6)
        self.assertEqual(sum(1 for k in files if k.startswith("item/")), 21)
        crop = json.loads(files["block/corn_crop.json"])
        self.assertEqual(crop["block_item"], "corn_delight:corn_seeds")
        self.assertEqual(crop["shapes"]["values"]["4,true"], [[0.0, 0.0, 0.0, 1.0, 0.875, 1.0]])
        self.assertEqual(crop["shapes"]["values"]["2,false"], [[0.0, 0.0, 0.0, 1.0, 0.75, 1.0]])
        tab = json.loads(files["creative_tab/corn_delight.json"])
        self.assertEqual(len(tab["items"]), 26)


if __name__ == "__main__":
    unittest.main()
