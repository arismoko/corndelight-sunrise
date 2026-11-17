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

## CD-05 First playable slice — PASS — CDM1 closed — 2026-11-16
- base: farmersdelight-horizon 30ba2a6 | addon commit: d88cc46 (no code change in this task) | build pin afe471cf
- in game (fd-port, FDM6, survival, pad 60003..60022,200,59992..60003; `../run/shots/cd-05/`). The test player's
  36 stacks were moved into chests at 60019,200,59995 (27) and 60021,200,59995 (9) first.
  - `corn_delight:corn_seeds` crafted in the 2×2 grid from 1 corn → 1 seeds.
  - corn on the FD cutting board (FD 26.3's board takes the whole stack: 5 corn) + flint knife →
    `corn_delight:cutting/corn`: +2 corn seeds, +1 corncob, knife 131 → 130, board 5 → 4.
  - furnace with coal: corn seeds → popcorn within 205 ticks (recipe 200; XP 521 → 522 for 0.5); corn → grilled
    corn within 205 ticks.
  - eating (Easy for the test, Peaceful restored): popcorn food 1 → 4, saturation 0 → 3.0 (3 × 0.5 × 2); grilled
    corn 4 → 10, 3.0 → 5.4 (+2.4 = 6 × 0.2 × 2).
  - corncob as fuel under a corn: `lit_total_time: 100`, cook progress reached ~100/200 before the fuel ran out
    (half an item), then decayed as vanilla.
  - composter: 62 corncobs: 3 tries on an empty composter all added a layer (1.21.1's level-0 rule, kept in the
    inline provider); 59 tries at levels 1–6 → 14 layers (23.7 %, expected 25 %, σ ≈ 3.3 tries).
  - corn fed to a chicken: `InLove` 0 → 587, corn −1 (`minecraft:chicken_food` tag carried from CD).
  - save & quit (full game restart) with 4 corn on the board and the knife at 130: after the restart the board
    still holds 4 corn (rendered, `board-after-restart.png`), knife 130; a cut after the restart → 3 left, +2
    seeds, +1 corncob.
  - second player: LAN stays environment-blocked as in MD-08/MD-12 (offline developer session refuses `lan open`), so
    the dedicated server: rig re-exported from `../run/native-mods` (base + CD built together for the server SDK,
    `run/server-export-new` → `run/server-engine`; client copy from `native-afe471c-a0692d0bd98a`). Server and Bob:
    "content from 3 mod(s)", `corn_delight: base api 1`. Bob (survival) put 2 corn on a board and cut once with a
    flint knife: board 2 → 1, Bob +2 seeds +1 corncob, knife 131 → 130 (`bob-cut.png`, `server.log`).
- deltas: none new.
- next: CD-06 (two-tall corn crop).

## CD-06 Two-tall corn crop — PASS — 2026-11-16
- base: farmersdelight-horizon 0b58ed0 (`api::crop` added) | addon commit: (this commit) | build pin afe471cf
- code: `src/crop.rs` — the corn Part on `corn_crop` (wheat template) and pure decisions. Behaviour taken from
  MMLib's HighCropBlock/CornCrop by reading only (AD9: re-implemented, nothing copied; restated here in my words):
  random tick at raw light ≥ 9: below age 7 a roll 1/(⌊25/speed⌋+1) grows one age (flag 2); then a lower half
  whose age was ≥ 4 **before** the tick rolls again and places an upper half (age 0) when the space is empty and an
  upper half could stand there (flags 3); the template's own growth is cancelled. An upper half survives only on a
  lower corn half of age ≥ 4 at raw light ≥ 8 (sky view implies it at darkening 0); a lower half keeps the
  template's crop rule. Bone meal: always succeeds (+2..5 from the level random), refused only when the relevant
  upper half is mature (an upper target, or the upper above a lower one); past 7 the half stops at 7 and a lower
  half bone-meals the upper above it, or places one at the leftover age (total − 8). Growth speed and draws come from
  the base's `api::crop` (vanilla `getGrowthSpeed`, as FD's crops).
- unit: 11 tests / 40+ decision cases (`dark_draws_nothing`, `young_lower_grows_with_one_roll`,
  `upper_roll_uses_the_age_before_the_tick`, `mature_lower_still_rolls_for_the_upper`, `upper_half_grows_alone`,
  `roll_bounds`, `upper_survival`, `bonemeal_targets`, `bonemeal_within_the_half`, `bonemeal_overflow`,
  `state_values`); 15 crate tests pass, clippy -D warnings clean.
- in game (fd-port, FDM6, field 60004..60011,199,59999/60001 on moist farmland; `../run/shots/cd-06/`):
  - 14 seeds planted by player use on farmland; time-lapse at `random_tick_speed 300` (`lapse-1..6.png`): lowers
    grew to 7, upper halves appeared and grew on their own (U0..U7 over 60 s); check of every upper: 14 uppers, 0 not
    standing on a lower of age ≥ 4.
  - bone meal: three lowers at age 6 with nothing above → lower 7 + upper at age 0, 1, 0 (overflow 2..5 − 2);
    lower 7 with an upper at 2 → upper 7 (passed up).
  - survival break of a mature lower (upper 7 above): both halves gone, drops 2 corn + 7 seeds (each half rolled its
    own table: CQ1).
  - light: a sealed stone cell (sky 0, block 0) on farmland with water inside kept its corn at age 2 for 20 s at
    speed 300, while an open plant went 2 → 7 and grew an upper half. (A first box leaked sky light 12 through the
    water channel and the farmland's partial shape; that run was discarded.)
  - farmer probe (CA8): a level-2 farmer with 16 corn seeds and a composter next to the field harvested a mature plant
    within ~60 s (lower broken, its upper gone with it), picked up the seeds (17 → 22) and replanted an age-0 corn:
    **PASS**, CA8 not needed.
  - restart: 22 corn states identical after save & quit and a new start (`before-restart.json`).
  - FD rich soil farmland (CA7): corn planted on `rich_soil_farmland` grew to lower 7 + upper 7 in 12 s at speed 300.
- observed (kept, reference data): dry farmland under corn turns to dirt and the corn pops — CD's data does not add
  corn to `#minecraft:maintains_farmland` (vanilla's list; FD adds its own crops). Recorded as quirk CQ7.
- not checked: bees (the template's bee growth would set the age directly), trampling.
- deltas: CA12 — the corn's growth does not fire the `crop_grow_pre/post` hooks for other mods (NeoForge
  `canCropGrow`/`fireCropGrowPost`): mods cannot dispatch engine hooks; the base's own crops have the same gap.
- next: CD-07 (wild corn block).

## CD-07 Wild corn block — PASS — 2026-11-16
- base: farmersdelight-horizon 0b58ed0 | addon commit: (this commit)
- code: `lib.rs` registers `corn_delight:wild_corn` through the base's `api::wild_crop::register(…,
  "minecraft:saturation", 8)` (BlockRegistry: `WildCropBlock(SATURATION, 8)`; 1.21.1 `FlowerBlock` takes
  **seconds**, so 160 ticks — the inventory's "8 ticks" was wrong; vanilla's dandelion is 0.35 s = 7 ticks).
- carry: new generated recipe `corn_delight:suspicious_stew_from_wild_corn` (bowl + 2 #mushrooms + wild corn →
  suspicious stew with saturation 160), the 26.3 per-flower form of 1.21.1's special suspicious-stew recipe, which
  took any `#minecraft:small_flowers` item with a FlowerBlock effect (CA13). FD 26.3 ships no such recipe for its own
  wild crops (not changed: FD behaviour). Carry re-pinned to base 0b58ed0; 267 files.
- in game (fd-port, FDM6, grass pad 60003..60014,199,59985..59991; `../run/shots/cd-07/`):
  - placement: refused on stone, placed on grass; `execute if block … #minecraft:small_flowers` → "Test passed".
  - bone meal ×15 on one wild corn → 7 wild corn around it (≤ 10 cap).
  - brown mooshroom fed wild corn → `stew_effects: [{id: "minecraft:saturation"}]` (duration 160 is the codec
    default and is omitted); crafted in the 2×2 grid: bowl + red + brown mushroom + wild corn → suspicious stew with
    `suspicious_stew_effects: [{id: "minecraft:saturation"}]` (`stew-craft.png`).
  - loot (survival): bare hand → 1 corn seeds (×3); shears → 1 wild corn, shears 238 → 237 (the carried
    `neoforge:can_item_perform_ability` → base `farmersdelight:can_item_perform_ability` rename works).
  - cutting board + flint knife → 1 corn seeds + 1 FD straw (`corn_delight:cutting/wild_corn`).
  - rich soil: 3 wild corn on FD rich soil, `random_tick_speed 300` for 50 s → no spread; positive control: two
    azaleas on the same rich-soil row became oak trees in 30 s (boost works) — wild corn is in
    `#farmersdelight:unaffected_by_rich_soil` through `#wild_crops` (base overlay entry `corn_delight:wild_corn`,
    optional). (Fern and short grass were tried first as controls; they are in that tag themselves, so they do not
    count.) The command parser does not know mod tags ("Unknown block tag"), so membership was checked by behaviour.
- deltas: CA13 (generated stew recipe, as above).
- next: CD-08 (wild corn world generation).

## CD-08 Wild corn world generation — PASS — 2026-11-17
- base: farmersdelight-horizon 0b58ed0 (no base change) | addon commit: (this commit) | build pin afe471cf
- found: the carried patch (CD-03, R8) asked for `#minecraft:dirt` below the corn, the floor and the grass. 26.3 split
  that tag: `#dirt` now holds only dirt, coarse dirt and rooted dirt; grass blocks, podzol, mycelium, moss and mud
  moved to `#grass_blocks`/`#moss_blocks`/`#mud`, and vanilla's (and FD 26.3's) features use
  `#minecraft:substrate_overworld` (= the old union, plus pale moss block, which 1.21.1 lacks). Result before the fix:
  wild corn almost never generated (world `CDGen1`, seed 1: 0 patches in 121 plains chunks; `/place feature` 0/20 on
  a flat grass pad, FD's `wild_carrots` 5/10 on the same pad). Not a delta: a 1.21.1 → 26.3 data uplift.
- code: carry rule **R10** (`[[block_tag_rename]]` in `tools/carry_rules_cd.toml.in`, `rename_block_tags` in
  `tools/carry_cd.py`): `matching_block_tag` predicates in carried worldgen get `minecraft:substrate_overworld`;
  `patch_wild_corn.json` regenerated (3 predicates), manifest/uplift report updated, unit test
  `test_r10_block_tag_rename_only_in_block_predicates` (14 carry tests OK), `carry.sh --check` ok (267 files).
- data (unchanged from CD-03): `worldgen/feature/patch_wild_corn.json` = `minecraft:overlay` of coarse-dirt floor,
  wild corn (±4/±3) and short grass (±6/±3) (FD 26.3 shape, BX-09); placed feature `rarity_filter 70`, `in_square`,
  `count 64`, heightmap, `biome` (biome_tag dropped); NeoForge `add_features` on `#is_overworld` minus lush caves and
  mushroom fields, base temperature 0.4–0.9 (`horizon:climate`).
- in game (fd-port, new creative worlds `CD8s1`/`CD8s2`/`CD8s3`, seeds 1/2/3; `../run/shots/cd-08/`): survey
  script `survey.py` (in the evidence folder) locates a biome, scans 11×11 chunks (y 50/58…130/185) with
  `horizon-ctl blocks`, classifies every chunk by `execute if biome` at its centre's surface, and clusters wild corn
  into patches (FD wild carrots + onions counted the same way as a control: same biomes and shape, rarity 1/120
  each ≈ 1/60 together).

  | seed | chunks | eligible (land) | excluded biomes | corn patches | corn in excluded | FD control patches |
  |---|---|---|---|---|---|---|
  | 1 (two passes) | 2621 | 2157 (1558) | 462 | 14 | 0 | 6 (second pass only) |
  | 2 | 1958 | 1214 (1040) | 641 | 11 | 0 | 13 |
  | 3 | 1892 | 1320 (915) | 572 | 9 | 0 | 9 |
  | total | 6471 | 4691 (3513) | 1675 | 34 | 0 | 28 |

  - patches found in forest (19), plains (5), flower forest (3), birch / old-growth birch forest (2), sunflower
    plains, swamp, meadow, beach, river (1 each); 2–13 wild corn each, with coarse dirt and short grass around
    (`seed1-plains-patch.png`). Excluded biomes scanned: desert, snowy plains/taiga/beach/slopes, ice spikes, taiga
    and old-growth taigas, savanna (+plateau, windswept), jungle/sparse jungle, badlands, windswept hills, grove,
    stony shore/peaks, frozen ocean/river, **mushroom fields (60 chunks)**: 0 patches. Lush caves: underground only,
    and the heightmap placement puts every try at the surface, so they cannot get any.
  - density: in the chunks where the control ran (3363 eligible), corn 30 patches vs FD 28 (expected ratio
    (1/70)/(1/60) = 0.86, seen 1.07). Both fall short of the nominal rate per eligible chunk (corn 34 in 4691 =
    1/138; on land 1/103) for the same reasons in both: ocean/river chunks place nothing, forest canopies put the
    heightmap origin on the leaves, slopes miss the ±3 y spread. No FD reference run exists (FD is never run here),
    so the comparison is against FD's port in the same chunks.
  - `/place feature corn_delight:patch_wild_corn`: one call is **one try** (in FD 26.3's shape the 64 tries live in
    the placed feature's `count`; FD's own `wild_carrots` behaves the same), 4/10 calls placed something on a flat
    grass pad; 64 calls at one origin → 10 wild corn, 24 short grass, 6 coarse dirt (`place-feature-64.png`).
    Recorded under CA1 (the 1.21.1 command placed the whole patch in one call).
- not covered: chunk-for-chunk equality with CD 1.21.1 (different generator/version; AD1); the unknown-biome chunks
  of seed 2 (103, biomes outside the script's list: pale garden/dappled forest centres) had no corn.
- worlds: `CDGen` (made 2026-11-16 21:25 by an earlier session, not logged) and `CDGen1` (generated with the old tag)
  are leftovers and can be deleted; `CD8s1..3` hold the survey.
- deltas: none new (CA1 noted: `/place feature` = one try).
- next: CD-09 (CDM2 demo).
