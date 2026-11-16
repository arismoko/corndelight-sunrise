# PROGRESS — Corn Delight → Horizon port

Plan: `../addons/ADDONS_PLAN.md` §10.2 (CD-01…CD-18), rules `../addons/ADDONS_HANDOFF.md` §4. Each entry names the
base (`ported_farmersdelight`) commit and version it was validated with.

## CD-01 Native skeleton with base code dependency — PASS — 2026-11-16
- base: farmersdelight-horizon af04ea8 (`3.6.30-horizon.2` + BX-04/05/06/09, unreleased) | build pin afe471cf |
  addon commit: (this commit)
- pins re-verified: `git ls-remote` Corn-Delight `refs/heads/1.21` = `ab03743e…` (unchanged); local MMLib at
  `8deb5c2f…`. Release lookup (Modrinth/CurseForge) not retried: UNVERIFIED (AU-1), as in the source lock.
- native crate: `horizon-mod.toml` id `ported_corn_delight`, version `1.1.8-horizon.1`, `namespaces =
  ["corn_delight"]`, `side = "both"`, `[native]` = the base's pins (game 26.3, horizon afe471cf, mixins e59da909),
  `[dependencies] ported_farmersdelight = "=3.6.30-horizon.2"`. `Cargo.toml` names only `horizon-mod-api` at the
  pin. `src/lib.rs` logs `corn_delight: base api <ported_farmersdelight::api::API_VERSION>` in `register`.
  LICENSE (port, MIT), LICENSE-corn_delight + `third_party/corn_delight/LICENSE` (verbatim CD MIT), NOTICE (MMLib:
  behaviour only, no code), README, CI (JSON, tool tests).
- found: the launcher **refuses** a mod whose `Cargo.toml` already names a `[dependencies]` mod
  (`horizon-mod-package/src/dependencies.rs:254-259`, `CargoConflict`), so the base cannot be a normal Cargo
  dependency for local work. `tools/cargo_dev.py` mirrors the crate into `target/dev-crate/` (symlinked `src/`) with
  `ported_farmersdelight = { path = ../farmersdelight-horizon, package = "farmersdelight-horizon" }` added, as the
  launcher does, and runs cargo there (`cargo_dev.py test`).
- build rig: `../run/rebuild.sh` now rsyncs the base and Corn Delight into `../run/native-mods/` and runs
  `native-build` on that folder (both compiled together; `BASE_ONLY=1` for the base alone).
- unit: `built_against_base_api_1` (1 passed).
- in game (AU-3, first cross-mod native build): `native-build` of the folder → "Built (optimized, prebuilt)"
  (`native-afe471c-926bd7af2f98`); FDM6 starts with "content from 3 mod(s)"; stderr (`../run/play.log`) shows
  `corn_delight: base api 1`; title screen Mods list shows "Corn Delight (Horizon port) 1.1.8-horizon.1" above the
  base and More Delight (`../run/shots/cd-01/mods-screen.png`). Corn Delight alone in the build folder →
  "Error: ported_corn_delight requires missing mod ported_farmersdelight", build refused, instance unchanged
  (`missing-base.txt`).
- deltas: none.
- next: CD-02 (config and load conditions).

## CD-02 Config and load conditions — PASS — 2026-11-16
- base: farmersdelight-horizon af04ea8 | addon commit: (this commit)
- code: `src/config.rs`: CD's COMMON spec (`general`: `genCornFarm` true, `villagersTradeCorn` true, the reference's
  comments) as NeoForge/NightConfig TOML text (`#comment` line above section and keys, keys tab-indented). Reading
  follows `ModConfigSpec#correct`: a missing or non-boolean key takes its default and the file is rewritten
  (valid values kept); a clean file is left alone; keys outside `[general]` do not count. Engine config hooks
  (`register_configs`, `config_loading`, `config_reloading`) wired in `lib.rs`. Load conditions
  `ported_corn_delight:gen_corn_farm` and `ported_corn_delight:villagers_trade_corn` (argument-free, read the live
  values). Ids: the plan's `corn_delight:*` condition ids are in the mod-id namespace instead (the engine registers
  a condition under the dispatching mod's namespace; base plan correction from M0).
- unit: `default_file_reads_clean`, `edited_values_load_without_rewrite`,
  `invalid_or_missing_values_take_defaults_and_correct` (4 passed with CD-01's). clippy -D warnings clean.
- in game (fd-port, FDM6; two probe recipes `corn_delight:cd02_probe_{gen_corn_farm,villagers_trade_corn}`, each
  gated by one condition, added only to the build copy in `../run/native-mods/`, never committed):
  first start writes `config/ported_corn_delight-common.toml` with the default text; both probes load
  (`/recipe give` → "Unlocked 1 recipe(s)", a missing id → "Unknown recipe"); `genCornFarm = false` + `/reload` →
  gen probe "Unknown recipe", trade probe present; restart with `villagersTradeCorn = false` → trade probe
  unknown, gen probe present; file replaced by `[general]\ngenCornFarm = "yes"` + `/reload` → rewritten to the
  full default text, both probes back. The probes leave the instance at the next rebuild.
- deltas: CA10 — the config file is `ported_corn_delight-common.toml` (reference `corn_delight-common.toml`; the
  engine names a mod's files after its id, as the base's A45).
- next: CD-03 (data uplift carry 1.21.1 → 26.3).

## CD-03 Data uplift carry (1.21.1 → 26.3) — PASS (script; in-game zero-skip check runs in CD-04) — 2026-11-16
- base: farmersdelight-horizon 30ba2a6 (overlay re-pinned) | addon commit: (this commit)
- `tools/carry_cd.py` + `tools/carry_rules_cd.toml.in`: imports the base's `carry_lib.py` and `worldgen_rewrite.py`
  from `--base` at the pinned commit; Corn Delight checked at `ab03743e…`; every source file matches exactly one
  rule. Target formats were read from the vanilla 26.3 jar and FD 26.3 data (not assumed):
  - recipes: R1 `{"item"}`/`{"tag"}` → `"id"`/`"#tag"`, lists flattened; R2 `neoforge:compound` kept in vanilla
    recipes (`taco`, `cornbread_batter`; the engine reads it); R3 in FD recipes → `{"fabric:type": "fabric:any"}`
    (6 cooking files: classic_corn_dog, corn_dog, corn_soup, creamed_corn, creamy_corn_drink, nachos_block — the
    plan's "4" was a miscount, cdinv§3.4 lists 6); R4 cutting `tool {"tag"}` → `"#tag"`; R5 `c:foods/milk` pruned
    from 5 files (corn_soup, creamed_corn, creamy_corn_drink, nachos_block, cornbread_batter; `#c:drinks/milk`
    stays in each), CA5.
  - advancements: `recipe_unlocked` `recipe` → `recipes` (23), root background `minecraft:textures/block/bricks.png`
    → `minecraft:block/bricks` (26.3 asset id, as FD 26.3's root); any other trigger than inventory_changed /
    recipe_unlocked would fail the carry (none).
  - loot (7): port-pack semantics (`conditions` → one `condition` / `all_of`, `functions` → `modifier`,
    `condition`/`function` → `type`, typed number providers, silk-touch match_tool →
    `minecraft:tool/can_silk_touch`) plus `block_state_property {block, properties}` → 26.3 `match_block {blocks,
    state}` (26.3 has no block_state_property; vanilla wheat uses match_block). wild_corn's
    `neoforge:can_item_perform_ability` (shears_dig) → the base's `farmersdelight:can_item_perform_ability` (the
    engine has no NeoForge one; the base maps shears_dig to `#c:tools/shear`, NeoForge's ShearsItem ability).
  - worldgen (R8, base BX-09): `configured_feature/patch_wild_corn.json` → `worldgen/feature/` (26.3 folder) as
    `minecraft:overlay` [floor coarse dirt, primary wild corn ±4, secondary short grass ±6]; placed feature:
    `biome_tag` dropped, `count 64` after `in_square`; biome modifier → `neoforge:add_features` (`#is_overworld` and
    not [lush_caves, mushroom_fields] and `horizon:climate` 0.4–0.9).
  - R7: 26 client item definitions from ItemRegistry.java's registration order; `cob_pipe` = `minecraft:select` on
    display context (gui/fixed/ground → `item/cob_pipe`, else `item/cob_pipe_model`). Block states/models: no
    change needed (port-pack asset rules checked; NeoForge `render_type` is read by the engine).
  - R9 overlay `tools/overlay/corn_delight.json` (`farmersdelight:wild_crops` block + item); dropped with their
    task: GLM files (CD-13, CA2), data maps (CD-04/CD-16); excluded: IE recipes (8), Serene Seasons tags (4),
    META-INF, pack.mcmeta, datagen cache. `logo.png` also as `icon.png`.
- counts (plan §CD-03): 40 recipes (0 IE), 36 advancements, 7 loot tables, 4 structures (byte copies), 49 textures,
  55 models, 6 blockstates, 12 lang, 26 item definitions, 14 `c` + 12 `minecraft` tag files; 266 files; fence: 0
  files outside `corn_delight` / `c` / `minecraft` tags; tag universe (vanilla 26.3 jar + base + output): 0
  undefined after the milk prune. `tools/uplift_report.md` lists every rewritten file with its rules.
  `--check` byte-identical ("carry check ok: 266 files").
- tests: `tools/test_carry_cd.py` (12 golden cases, one or more per rule). CI keeps JSON parsing only (the carry
  needs the private base checkout).
- deltas: CA5 (milk prune) recorded.
- next: CD-04 (block and item declarations), then the in-game zero-skip check for CD-03.

## CD-04 Block and item declarations — PASS — 2026-11-16 (also closes CD-03's in-game check)
- base: farmersdelight-horizon 30ba2a6 | addon commit: (this commit)
- `tools/decl/cd.toml.in` (every row cited to ItemRegistry/BlockRegistry/the block classes/the data maps) →
  `tools/gen_cd_decls.py` → `data/corn_delight/horizon/{block (6), item (21), creative_tab (1)}` (block items of
  the 5 placeable blocks come from their block declarations). Forms: foods `minecraft:food` (saturation =
  nutrition × modifier × 2 in Java float) + `consumable` (default 1.6 s; `creamy_corn_drink` drink animation and
  sound, no particles) + one `apply_effects` (Comfort 3600/1200, Regeneration 1200, Strength 600, Nourishment 6000;
  MobEffectInstance defaults); bowl/stick/bottle foods stack 16 with crafting remainder and `use_remainder`;
  `corn` villager food 1; `corncob` fuel 100 (`cooking_fuel`); 12 compost chances as `compostable` layers —
  vanilla providers for 0.5/0.65/0.85/1.0, inline providers in vanilla's own shape (empty composter always,
  else a weighted 1/0 draw) for CD's 0.25/0.35/0.55/0.75; `corn_seeds` places `corn_crop` and is edible (the
  base's onion pattern); `cob_pipe` `equippable` head, equip sound `block.grass.place`. Blocks: `corn_crop`
  wheat template + declared `upper`, shapes by age × half (lower 4/8/12/16 px…, upper 4/6/8/12/14 px…), block item
  `corn_seeds`; `wild_corn` as the base's wild crops (short_dry_grass template, FD's 2..14×13 shape, compost
  0.55); crate (oak planks 2/3), kernel bag (white wool); `nachos_block` (stonecutter template for `facing`,
  servings 0–4 placed full, cake's 0.5/wool sound/POPPED, plate at 0 else plate + nachos); `popcorn_box` (yellow
  wool 0.8, servings 0–4). Creative tab `itemGroup.corn_delight`, icon corn, 26 items in registry order.
- plan corrections: the popcorn box's outline is FD 26.3 `FeastBlock.SHAPES` by servings (CD declares a
  4..12×10 `BOX_SHAPE` but never uses it); CD's block items stack to 64 (not 1 like FD's feasts).
- carry additions found in game: CD's nachos assets name upstream FD 1.21.1 assets FD Refabricated 26.3 renamed
  (`shepherds_pie_block_leftover` model → `…_leftovers`, texture `tray_top` → `tray`, `tray_pie_leftover` →
  `shepherds_pie_leftovers`): magenta nachos block in the first run. New rule `[asset_rename]` and a carry check that
  every model/texture reference resolves in vanilla 26.3, the base or the output (verified to fail without a
  rename). Package icon: CD's logo is a 135×37 banner (`icon.png must be square`, build refused) → the corn item
  texture. `tools/carry.sh` wraps the carry with the local paths.
- tests: `tools/test_cd_decls.py` (6: item order and food/effect/container values against a table extracted from
  ItemRegistry.java, compost/fuel against the data maps, Java-float saturation, providers, output shapes);
  `tools/test_carry_cd.py` 13. decl `--check` 28 files, carry `--check` 266 files.
- in game (fd-port base + MD + CD, FDM6, `../run/shots/cd-04/`): latest.log has **no** `corn_delight` line (0
  skipped recipes, advancements, loot tables — CD-03's acceptance) and the base logs no rejected cooking recipe;
  `/give` of all 26 ids → 26 "Gave"; every block state placed: corn lower ages 0–7 and upper ages 0–7, wild corn,
  crate, kernel bag, nachos 0–4, popcorn box 0–4 render with the carried models (`feasts.png`, `blocks.png`);
  creative tab page 2 "Corn Delight", 26 items in order, cob pipe 2D in the GUI (`creative2.png`). Not yet
  (later tasks): upper halves only survive on farmland now (corn survival is CD-06); feast use (CD-11).
- incident: a teleport onto the pad edge (no floor at 60015,199,59996) dropped the test player to y 113 in creative,
  unhurt; floor filled, player moved back. A rebuild ran while the old game was still open, so the next start
  crashed ("FDM6 is already open in another instance"); the stale game was stopped. Neither touched FDTest.
- deltas: CA11 — the nachos' leftover tray uses FD 26.3's shepherd's pie leftover texture (upstream FD 1.21.1's
  generic `tray_pie_leftover` does not exist in FD 26.3).
- next: CD-05 (first playable slice, closes CDM1).
