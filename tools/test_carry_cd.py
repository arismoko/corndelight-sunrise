#!/usr/bin/env python3
"""Golden tests for tools/carry_cd.py's rules (CD-03), on small inputs. Needs the base checkout beside this repo
(../farmersdelight-horizon) for carry_lib / worldgen_rewrite; the pin is not checked here."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "farmersdelight-horizon" / "tools"))
import carry_cd as c  # noqa: E402
import carry_lib  # noqa: E402
import worldgen_rewrite  # noqa: E402

c.lib, c.wg = carry_lib, worldgen_rewrite


def up():
    return c.Uplift({"c:foods/milk"})


class Recipes(unittest.TestCase):
    def test_r1_objects_to_strings(self):
        r = c.upgrade_recipe({"type": "minecraft:crafting_shaped", "pattern": ["w"], "key": {
            "w": {"tag": "c:crops/corn"}, "b": {"item": "minecraft:water_bucket"}},
            "result": {"id": "x:y", "count": 3}}, up())
        self.assertEqual(r["key"], {"w": "#c:crops/corn", "b": "minecraft:water_bucket"})
        self.assertEqual(r["result"], {"id": "x:y", "count": 3})
        r = c.upgrade_recipe({"type": "minecraft:smelting", "ingredient": {"item": "a:b"}, "result": {"id": "a:c"}}, up())
        self.assertEqual(r["ingredient"], "a:b")

    def test_r2_vanilla_compound_kept_and_r5_prune(self):
        u = up()
        r = c.upgrade_recipe({"type": "minecraft:crafting_shapeless", "ingredients": [
            {"type": "neoforge:compound", "children": [{"tag": "c:foods/milk"}, {"tag": "c:drinks/milk"}]}],
            "result": {"id": "a:b"}}, u)
        self.assertEqual(r["ingredients"], [{"type": "neoforge:compound", "children": ["#c:drinks/milk"]}])
        self.assertEqual(u.pruned, ["#c:foods/milk"])

    def test_r3_fd_compound_to_fabric_any(self):
        r = c.upgrade_recipe({"type": "farmersdelight:cooking", "ingredients": [
            {"type": "neoforge:compound", "children": [{"tag": "c:foods/raw_beef"}, {"item": "minecraft:brown_mushroom"}]}],
            "result": {"id": "a:b"}}, up())
        self.assertEqual(r["ingredients"], [{"fabric:type": "fabric:any",
                                             "ingredients": ["#c:foods/raw_beef", "minecraft:brown_mushroom"]}])

    def test_r4_cutting_tool(self):
        r = c.upgrade_recipe({"type": "farmersdelight:cutting", "ingredients": [{"tag": "c:crops/corn"}],
                              "tool": {"tag": "c:tools/knife"},
                              "result": [{"item": {"id": "a:b", "count": 2}}]}, up())
        self.assertEqual((r["ingredients"], r["tool"]), (["#c:crops/corn"], "#c:tools/knife"))
        self.assertEqual(r["result"], [{"item": {"id": "a:b", "count": 2}}])

    def test_unknown_ingredient_fails(self):
        with self.assertRaises(carry_lib.CarryError):
            c.upgrade_recipe({"type": "minecraft:crafting_shapeless",
                              "ingredients": [{"type": "neoforge:difference"}], "result": {"id": "a:b"}}, up())


class Advancements(unittest.TestCase):
    def test_recipe_unlocked_and_background(self):
        a = c.upgrade_advancement({"display": {"background": "minecraft:textures/block/bricks.png"}, "criteria": {
            "r": {"trigger": "minecraft:recipe_unlocked", "conditions": {"recipe": "a:b"}},
            "i": {"trigger": "minecraft:inventory_changed", "conditions": {"items": [{"items": ["a:b"]}]}}}}, up())
        self.assertEqual(a["criteria"]["r"]["conditions"], {"recipes": "a:b"})
        self.assertEqual(a["display"]["background"], "minecraft:block/bricks")

    def test_unchecked_trigger_fails(self):
        with self.assertRaises(carry_lib.CarryError):
            c.upgrade_advancement({"criteria": {"x": {"trigger": "minecraft:consume_item"}}}, up())


class Loot(unittest.TestCase):
    def test_crop_table_matches_vanilla_shape(self):
        src = {"type": "minecraft:block", "pools": [{"rolls": 1.0, "bonus_rolls": 0.0, "entries": [
            {"type": "minecraft:item", "conditions": [{"condition": "minecraft:block_state_property",
                                                       "block": "a:crop", "properties": {"age": "7"}}],
             "name": "a:corn"}]}], "functions": [{"function": "minecraft:explosion_decay"}]}
        out = c.upgrade_loot(src, up(), {})
        self.assertEqual(out["modifier"], {"type": "minecraft:explosion_decay"})
        self.assertEqual(out["pools"][0]["entries"][0]["condition"],
                         {"type": "minecraft:match_block", "blocks": "a:crop", "state": {"age": "7"}})

    def test_inverted_any_of_rename_and_silk(self):
        src = {"pools": [{"entries": [], "conditions": [
            {"condition": "minecraft:inverted", "term": {"condition": "minecraft:block_state_property",
                                                         "block": "a:b", "properties": {"servings": "4"}}},
            {"condition": "minecraft:any_of", "terms": [
                {"condition": "neoforge:can_item_perform_ability", "ability": "shears_dig"},
                {"condition": "minecraft:match_tool", "predicate": {"predicates": {"minecraft:enchantments": [
                    {"enchantments": "minecraft:silk_touch", "levels": {"min": 1}}]}}}]}]}]}
        out = c.upgrade_loot(src, up(), {"neoforge:can_item_perform_ability": "farmersdelight:can_item_perform_ability"})
        cond = out["pools"][0]["condition"]
        self.assertEqual(cond["type"], "minecraft:all_of")
        inv, anyof = cond["terms"]
        self.assertEqual(inv["term"], {"type": "minecraft:match_block", "blocks": "a:b", "state": {"servings": "4"}})
        self.assertEqual(anyof["terms"], [{"ability": "shears_dig", "type": "farmersdelight:can_item_perform_ability"},
                                          "minecraft:tool/can_silk_touch"])

    def test_set_count_numbers_typed(self):
        src = {"pools": [{"rolls": {"min": 2.0, "max": 5.0}, "entries": [
            {"type": "minecraft:item", "functions": [{"function": "minecraft:set_count", "count": {"min": 1, "max": 3}}]}]}]}
        out = c.upgrade_loot(src, up(), {})
        self.assertEqual(out["pools"][0]["rolls"]["type"], "minecraft:uniform")
        self.assertEqual(out["pools"][0]["entries"][0]["modifier"]["count"]["type"], "minecraft:uniform")


class Items(unittest.TestCase):
    RULES = {"item_definitions": {"flat_contexts": ["gui", "fixed", "ground"], "special": {"cob_pipe": "cob_pipe_model"}}}

    def test_registry_order_and_definitions(self):
        java = 'X = ITEMS.register("wild_corn",\n// Y = register("old", ...)\nZ = register("corn", ()->food(\n'
        self.assertEqual(c.item_ids(java), ["wild_corn", "corn"])
        self.assertEqual(c.item_definition("corn", self.RULES),
                         {"model": {"type": "minecraft:model", "model": "corn_delight:item/corn"}})
        pipe = c.item_definition("cob_pipe", self.RULES)["model"]
        self.assertEqual(pipe["property"], "minecraft:display_context")
        self.assertEqual(pipe["fallback"]["model"], "corn_delight:item/cob_pipe_model")

    def test_fd_asset_renames_and_refs(self):
        u = up()
        model = {"parent": "block/block", "textures": {"tray_top": "farmersdelight:block/tray_top", "x": "#tray_top"}}
        out = c.upgrade_asset(model, u, {"farmersdelight:block/tray_top": "farmersdelight:block/tray"})
        self.assertEqual(out["textures"]["tray_top"], "farmersdelight:block/tray")
        self.assertEqual(c.asset_refs("m.json", out),
                         {("models", "block/block"), ("textures", "farmersdelight:block/tray")})

    def test_typed_variant_fields(self):
        out = c.upgrade_asset({"variants": {"": {"model": "a:b", "y": "90", "uvlock": "true"}}}, up())
        self.assertEqual(out["variants"][""], {"model": "a:b", "y": 90, "uvlock": True})


if __name__ == "__main__":
    unittest.main()
