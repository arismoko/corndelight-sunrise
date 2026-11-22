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

## CD-09 CDM2 demo — PASS — CDM2 closed — 2026-11-17
- base: farmersdelight-horizon 0b58ed0 | addon commit: f73012d (no code change in this task) | build pin afe471cf
- recorded tour (fd-port, world `CD8s1` = CD-08's new seed-1 world, survival, Peaceful; recordings
  `../run/horizon-home/instances/fd-port/recordings/2026-11-17_14-29-44-cd-09-demo` (before the restart) and
  `…/2026-11-17_14-34-23-cd-09-demo-2` (after); shots `../run/shots/cd-09/`):
  - found: the generated wild corn patch at −2853,79,3085 (plains, 12 wild corn; CD-08).
  - bare hand on wild corn → 1 corn seeds; shears → 1 wild corn; wild corn on a placed FD cutting board + flint knife
    → +1 corn seeds + 1 FD straw; the other 10 wild corn broken by hand → 11 seeds (one dropped 2).
  - field (pad filled flat at −2849..−2841,79,3069..3076, water source at −2845,79,3072): 7 grass tilled with an
    iron hoe → farmland; 7 FD rich soil placed by the player and tilled → `rich_soil_farmland`; 10 seeds planted.
  - mid-growth (random_tick_speed 60 for 20 s, then 0): plain farmland lowers 0/4/0/0/3 (+1 upper), rich soil
    farmland lowers 6/6/7/7/7 (+4 uppers) (`1-mid-growth.png`). Save & quit, full restart: all **15 corn states
    identical**.
  - 40 s more at 60: the rich-soil row mature (5 × lower 7 + upper 7), plain row 2–7. Survival harvest of a mature
    plant: upper half → 1 corn + 3 seeds (the lower stayed, age 7); lower → 1 corn + 4 seeds; reseeded on the same
    rich soil farmland (age 0) (`2-harvest-replant.png`).
- guest: LAN stays environment-blocked (offline developer session, as MD-08/CD-05), so the dedicated server: rig
  re-exported with the current base + CD code (`native-build ../run/native-mods --server-output
  run/server-export-new` → `run/server-engine`, client copy from `native-afe471c-e5f703404e44`); server "content from
  3 mod(s)". Bob (survival) bone-mealed one corn on farmland (pad 60006..60012,155..158,59995..60001 in FDServer):
  age 1 → 4 → lower 7 + upper 0 (overflow) → upper 5 → upper 7; the fifth use on the mature plant was refused
  (bone meal 16 → 12) (`3-bob-bonemeal.png`, `server.log`).
- left as found: random_tick_speed 3 in `CD8s1`; server stopped; Bob's inventory kept (+12 bone meal).
- deltas: none new.
- next: CD-10 (kitchen recipes complete).

## CD-10 Kitchen recipes complete — PASS — 2026-11-17
- base: farmersdelight-horizon 0b58ed0 | addon commit: 22c6766 (no code change in this task) | build pin afe471cf
- AD14 second pass: not needed — CD-04 already generated the five foods' effects with the base's ids
  (`farmersdelight:comfort`/`nourishment` were declared by then); decl `--check` unchanged.
- in game (fd-port, `CD8s1`, pad 19984..20022,66..68,19984..19996; `../run/shots/cd-10/`):
  - **10 pot recipes**, each cooked once on a lit FD stove (ingredients put in with `item replace block … container.N`):
    boiled corn (100 t), caramel popcorn, classic corn dog, corn dog (100 t), corn soup, creamed corn, creamy corn
    drink, cornbread stuffing (200 t), nachos block (bowl container → output), stuffed pumpkin from cornbread
    (400 t, pumpkin container → `farmersdelight:stuffed_pumpkin_block`). The meal-slot containers are the items'
    remainders: stick (corn dogs), bowl (soup, creamed corn, stuffing), glass bottle (drink).
  - `corn_soup` with each compound alternative: raw chicken + milk bucket, raw porkchop + milk bottle, raw beef +
    milk bottle, brown mushroom + milk bucket → corn soup (4/4).
  - **crafting** (crafting table, survival, driver `craft.py`, log `craft.log`): 16/16 PASS — taco (cooked chicken and
    cooked mutton: the `neoforge:compound` alternatives), cornbread batter ×3 from milk bucket and from milk bottle
    (compound around `#c:drinks/milk`; bucket and glass bottle left over), organic compost from corncobs, paper from
    corncobs, raw tortilla ×3 (shaped, bucket left), caramel popcorn, classic corn dog from crafting, cob pipe, corn
    crate ↔ 9 corn, kernel bag ↔ 9 seeds, seeds from corn, popcorn box.
  - **cutting** (board + flint knife): corncob → 1 straw each (FD 26.3's board takes the stack, one cut per item),
    tortilla → 4 tortilla chips (corn and wild corn: CD-05/CD-07).
  - furnace and smoker: cornbread batter → cornbread, raw tortilla → tortilla; campfire (600 t): both.
  - **eating** (Easy, food drained with short Hunger bursts; `eat.py`, `eat.log`): corn soup → Comfort 3:00 + bowl;
    creamed corn → Comfort 3:00 + bowl; creamy corn drink → Comfort 1:00 + Regeneration 1:00 + glass bottle, drink
    pose and the "Sipping" drink sound (`drinking.png`); corn dog / classic corn dog → stick; taco → Strength 0:30;
    cornbread stuffing → Nourishment 5:00 + bowl (nachos bowl: CD-11). Food/saturation as declared (corn soup
    10 → 20, 0 → 18.0).
- ambiguity report (ADDONS_VALIDATION §2.3, MD's `recipe_overlap.py --addon ../corndelight-horizon`): 1709 recipes,
  39 CD, **0 add-on conflicts**; 2 CD recipes skipped by the tool (taco and cornbread batter use
  `neoforge:compound`, which the tool does not read; both crafted in game above).
- incidents (test world only): the test player walked onto a lit campfire placed for the campfire test (`goto`
  stopped on it) and burned to death; the drops were collected back after respawning. Later, on Easy at night, an
  explosion (most likely a creeper) took 10 HP and cratered the pad; 66 hostile mobs killed, pad refilled.
  Difficulty back to Peaceful.
- deltas: none new.
- next: CD-11 (nachos and popcorn feasts).

## CD-11 Nachos and popcorn feasts — PASS — 2026-11-17
- base: farmersdelight-horizon e7215ed (`api::feast::register_custom`, base PROGRESS "CD-11 (base side)") |
  addon commit: (this commit) | build pin afe471cf
- code: `src/feasts.rs`. `nachos_block` = `FeastBlock(cake, nachos_bowl, leftovers)` through
  `api::feast::register` (FD 26.3's take-serving, survival, comparator, particles: CA6). `popcorn_box` through
  `register_custom`: its own use (PopcornBoxBlock#takeServing, restated in the module doc) as a pure `decide`
  (servings, empty hand) → break / serve (last: + paper, block removed without drops) / bare-hand message, and a
  client prediction (serve → Success, bare hand → Pass). Unit test `popcorn_decision_table` (16 crate tests),
  clippy -D warnings clean. Carry re-pinned to base e7215ed (unchanged output, 267 files).
- in game (fd-port, `CD8s1`, pad around 20004..20010,67,19992, survival; `../run/shots/cd-11/`; driver `feast.py`
  in the session):
  - nachos: empty hand → action bar "You need a Bowl to eat this.", servings 4; with bowls 4× → +1 nachos bowl and
    −1 bowl each, 4 → 0 (plate shape); the next use breaks it: wood-break sound, loot → 1 bowl.
  - popcorn box: empty main hand (bowl in the off hand) → +1 caramel popcorn, no message, "Gear equips" subtitle
    (armour equip sound) (`feasts.png`); bowls in both hands → "Use your bare hand to grab popcorn.", nothing
    taken; the last serving → +1 caramel popcorn +1 paper, block gone, nothing on the ground; a box set to
    0 servings → breaks on use with no drops.
  - inherited FeastBlock parts: comparator next to a box with 2 servings → redstone 2; removing the floor under a
    box removes it.
  - save & quit + restart: nachos 4 and 0, popcorn 2 and 2 identical.
  - guest (dedicated server, rig re-exported with base e7215ed + CD; LAN environment-blocked as before): Bob took a
    nachos bowl with a bowl (bowl −1) and a caramel popcorn (`bob-feasts.png`, `server.log`).
- quirks (reference behaviour, kept): **CQ8** — holding an item in the main hand with an empty off hand still takes
  popcorn: the main hand gets the bare-hand message and passes, then vanilla tries the off hand, whose empty stack
  serves (seen in game: message + serving). **CQ9** — CD ships no loot table for the popcorn box, so breaking it
  (mined or used at 0 servings) drops nothing.
- incident (test player Bob on the dedicated server): teleported to z 60002, one block off the CD-09 pad, he fell
  ~96 blocks and died; his items were collected back (12 bone meal from CD-09 given back by command).
- deltas: none new (CA6 as planned).
- next: CD-12 (CDM3 demo).

## CD-12 CDM3 demo — PASS — CDM3 closed — 2026-11-17
- base: farmersdelight-horizon e7215ed | addon commit: d87cd66 (no code change in this task) | build pin afe471cf
- recorded kitchen tour (fd-port, `CD8s1`, survival; recordings `../run/horizon-home/instances/fd-port/recordings/
  2026-11-17_15-01-53-cd-12-demo` and `…/2026-11-17_15-04-07-cd-12-demo-2`; shots `../run/shots/cd-12/`):
  - corn soup through the pot's menu (corn, cabbage, raw chicken, milk bucket into 300–303, bowl into 307) on a lit
    stove → corn soup taken from 308.
  - nachos block cooked in the pot (2 tortilla chips, cooked beef, milk bottle, tomato sauce + bowl) → placed by the
    player (facing south, toward the player) → 2 servings with bowls (`1-kitchen.png`, popcorn box placed beside it
    and one bare-hand serving).
  - **save & quit + restart mid-feast**: nachos 2 servings and popcorn box 3 servings identical.
  - popcorn party after the restart: bare hand 3× → caramel popcorn each, the last + paper, box gone
    (`2-popcorn-last.png`); nachos 2 more servings → plate (`3-nachos-plate.png`) → next use breaks it, bowl dropped.
- guest (dedicated server; LAN environment-blocked): Bob filled a pot on a lit stove through its menu (corn,
  cabbage, raw beef, milk bottle + bowl) → corn soup taken, milk bottle → glass bottle (`4-bob-pot.png`,
  `server.log`); his nachos and popcorn servings are CD-11's.
- observation (base, not CD): after a meal is taken from the pot's output through the menu, `data get block` still
  lists it in the pot's `Inventory` tag — the client-mirror update tag, not the slots (`Items` empty, the menu
  shows 308 empty, no duplicate). Left as is; noted for the base.
- deltas: none new.
- next: CD-13 (chest loot injection).

## CD-13 Chest loot injection — PASS — 2026-11-17
- base: farmersdelight-horizon e7215ed | addon commit: (this commit) | build pin afe471cf
- code: `src/loot.rs` + `loot_table_load` in `lib.rs`. CD's two MMLib `add_loot_table` modifiers (behaviour read in
  MMLib's AddLootTableModifier, nothing copied: after the chest's own pools the extra table is rolled with the same
  context and its items appended) become one appended pool per chest table, holding the extra table as its only
  entry (`{"rolls": 1, "entries": [{"type": "minecraft:loot_table", "value": …}]}`): a one-entry, one-roll pool draws
  nothing itself, so the draws and their order are the reference's; the base (dispatched first) has already
  appended FD's chest pools, as FD's pools precede CD's modifier. Targets: the 5 village house chests →
  `corn_delight:village_house`, `minecraft:chests/shipwreck_supply` → `corn_delight:shipwreck_supply` (CA2).
- unit: `pools_appended_for_exactly_the_six_tables` (6 targets; butcher, shipwreck map/treasure, dungeon and FD's
  nested table untouched), `pool_after_existing_pools_and_on_a_table_without_pools`; 18 crate tests, clippy clean.
- in game (fd-port, `CD8s1`; `/loot insert` into a fresh chest per roll, 30 chests per table; script and log in
  `../run/shots/cd-13/`):

  | table | chests with corn items | mean corn items (sd) | range | expected mean |
  |---|---|---|---|---|
  | village_plains_house | 30/30 | 7.13 (2.16) | 3–13 | 7.0 (2–5 rolls × 1–3) |
  | village_desert_house | 30/30 | 7.53 (2.36) | 2–12 | 7.0 |
  | village_savanna_house | 30/30 | 7.93 (2.98) | 2–12 | 7.0 |
  | village_snowy_house | 30/30 | 7.40 (2.85) | 2–12 | 7.0 |
  | village_taiga_house | 30/30 | 7.17 (2.49) | 3–12 | 7.0 |
  | shipwreck_supply | 30/30 | 6.00 (2.80) | 2–12 | 5.6 (1–4 rolls × seeds 2–4 / corn 1–2) |
  | village_butcher (control) | 0/30 | 0 | — | 0 |

  Seeds and corn come out about evenly in the houses (567 seeds / 548 corn); vanilla and FD items are still in the
  same chests (e.g. plains: gold nugget, potatoes, bread, sapling, emeralds, FD onion + 5 seeds + 5 corn).
- not covered: naturally generated village chests (same table code path as `/loot`).
- deltas: CA2 as planned (no behaviour difference).
- next: CD-14 (village corn farms).

## CD-14 Village corn farms — PASS (config gate: CA14) — 2026-11-17
- base: farmersdelight-horizon e7215ed | addon commit: (this commit) | build pin afe471cf
- data: `tools/gen_villages.py` (`--check`) renders CD's VillageStructures (MMLib StructuresUtils.addBuildingToPool,
  read only: `single_pool_element`, processors `minecraft:empty`, rigid, weight) as `horizon:add_to` files
  `data/corn_delight/worldgen/template_pool/village/{plains,taiga}_houses.json`: small ×3 + large ×1 each (CA3). The four
  carried pieces are 1.21.1 NBT (DataVersion 3955): same 13×6×9 / 7×6×9 size and building-entrance jigsaw as
  vanilla's farms; corn states carry only `age`, so they load as lower halves; the taiga pieces' jigsaw names the
  plains streets pool (CQ5, kept).
- in game (fd-port, new world `CD14`, seed 14; scripts/logs in `../run/shots/cd-14/`):
  - natural villages (located from a 3000-block grid, 9×9 chunks scanned): **plains 20 villages, 11 with corn farms
    (17 farms); taiga 23 villages, 15 with corn farms (22 farms)**.
  - pool sampling (`/place jigsaw minecraft:village/plains/houses … 1` at 81 isolated sky spots): 10 empty (vanilla's
    empty elements are 10/96), 67 other houses, 4 corn farms (3 large, 1 small) = 5.6 % of placed pieces (expected
    4/96 = 4.2 %).
  - `/place structure` villages (18 plains, 12 taiga), corn farms vs vanilla's crop farms in the same villages: plains
    corn 19 small + 1 large, vanilla 28 small + 2 large; taiga corn 8 small, vanilla 16 small. Large pieces rarely fit
    for vanilla's farms too, so the few large corn farms come from the village layout, not CD (in natural villages all
    39 corn farms were small).
  - corn in a placed village farm grows: random_tick_speed 100 for 20 s → 81 lower halves from ages 0–2 to 0–6, one
    upper half (back to 3 afterwards). Screenshot `plains-village-corn-farm.png`.
  - `genCornFarm = false` + `/reload`: 6 new plains villages still had 162 corn (config restored after).
- engine gap (known): template-pool additions take no load conditions (base E-26), so `genCornFarm` cannot switch the
  farms off. Delta **CA14**: `genCornFarm` is inert; villages always get the corn farms (CD's default).
- deltas: CA3 as planned, CA14 new.
- next: CD-15 (trades).

## CD-15 Villager and wandering-trader trades — PASS (give counts: CA4) — 2026-11-17
- base: farmersdelight-horizon e7215ed | addon commit: 35a794b (data and `tools/gen_trades.py`, committed with CD-14 by
  mistake) + (this commit: log) | build pin afe471cf
- data: `tools/gen_trades.py` (`--check`, 9 files) from VillagerTradeHandler and its two listing classes (read only,
  restated in the generator's docstring): `corn_delight:villager_trade/farmer/1/corn_emerald{,_2}` (1 corn → 1 emerald,
  16 uses, xp 2, discount 0.05; the listing's random count is discarded: CQ3), `farmer/2/emerald_{cornbread,tortilla}`
  (wants emerald uniform 6–20, gives 6–16), `wandering_trader/emerald_corn_seeds` (6–20 → 2–8, xp 2) and
  `emerald_popcorn_box` (7–21 → 1–2, xp 15); tag entries in `minecraft:villager_trade/farmer/level_1|level_2` with
  `neoforge:conditions` `ported_corn_delight:villagers_trade_corn` (FD's farmersBuyFDCrops is always true here,
  CA9), and in `wandering_trader/common` ungated (CQ4: both wandering trades in the common pool).
- probe: the random give count is written as vanilla 26.3 reads it (`given_item_modifier` `minecraft:set_count`
  uniform). The engine's trade modifiers (`merchant.rs` `apply_modifier`) have no `set_count` arm and read
  `gives.count` as a fixed number → **E-41** (trade `set_count` ignored); `gives.count` holds the midpoint
  (cornbread/tortilla 11, seeds 5, popcorn box 2) → delta **CA4**. EX-01 (ADDONS_PLAN §11) is the engine change.
- in game (fd-port, `CD14`, NoAI merchants summoned on a pad, each trade screen opened once, `Offers` read; script
  and logs in `../run/shots/cd-15/`):

  | merchants | with a CD offer | expected | CD offers seen |
  |---|---|---|---|
  | farmer L1 × 30 | 15 | 41.7 % (2 of 5 + 2 FD + 2 CD) | 16 × corn 1 → emerald 1, 16 uses, xp 2 (one farmer drew both) |
  | farmer L2 × 30 | 16 | 52.4 % (2 of 3 + 2 + 2) | cornbread 8, tortilla 10: 7–19 emeralds → 11, 16 uses, xp 5 |
  | wandering trader × 60 | 8 | 11.6 % (5 of 78 + 4 FD + 2 CD) | seeds 3 (7–11 emeralds → 5), popcorn box 5 (11–20 → 2), 16 uses |

  Prices fall inside the ranges; FD and vanilla offers appear next to them (carrot, potato, FD onion/tomato,
  cabbage, rice…).
- config: `villagersTradeCorn = false` + `/reload` → new farmers still offered corn (9/15 at each level); after a
  full restart with the key off → **0/15 L1, 0/15 L2**. Tag conditions are evaluated when the world's content is
  built, not on `/reload` (recipes did change on `/reload` in CD-02). Key restored to true.
- deltas: CA4 (fixed give counts, E-41). Engine gap E-41 new.
- next: CD-16 (cob pipe and item behaviours).

## CD-16 Cob pipe and item behaviours — PASS — 2026-11-17
- base: farmersdelight-horizon e7215ed | addon commit: (this commit) | build pin afe471cf
- code/data: `tools/gen_cd_decls.py` also writes `data/minecraft/tags/item/villager_picks_up.json` (items with
  `villager_food`: corn), checked by `--check` (decl check ok: 28 files; test_cd_decls OK; carry check ok).
- reference read (MMLib, read only): CD calls `VillagerUtils.addFoodToVillage(CORN, 1)`; MMLib's map starts as a
  copy of vanilla's villager food points, and its Villager mixin **replaces** `wantsToPickUp` with "item is in that
  map and fits", replaces the food-point count with the map's, eats map foods first, and makes farmers throw map
  foods to hungry villagers. In 26.3, what villagers pick up is `#minecraft:villager_picks_up`; corn's food points
  are the item's `minecraft:villager_food` (CD-04).
- in game (fd-port, `CD14`, pad at 100000,200,100000; `../run/shots/cd-16/`):
  - cob pipe: right-click in survival → head slot (armour slot 500), hand empty; the "General of the Maize"
    challenge (`corn_delight:macarthur`) was granted on equip (`pipe-third-person.png` shows the toast; the F5 key
    did not switch the camera through horizon-ctl). Armour stand with the pipe on its head shows the 3D pipe; the
    dropped item shows the 2D icon (`pipe-armor-stand.png`, `pipe-armor-stand-close.png`).
  - enchanting the held pipe: Curse of Vanishing and Curse of Binding apply (`enchantable/vanishing`,
    `enchantable/equippable`); protection, unbreaking, mending refused ("cannot support that enchantment").
  - animals (`animals.py`, adult NoAI mobs, one right-click each, 16 in hand): corn → InLove ≈ 580 for cow, pig,
    sheep, goat, chicken and horse, one item used each; parrot eats it (item used; a taming roll, no love mode).
    Corncob and corn seeds the same on cow, chicken and parrot.
  - villager: before the tag a farmer picked up dropped corn seeds (vanilla `villager_plantable_seeds`, carried CD
    tag) but left corn; after it, a farmer picked up 3 dropped corn (Inventory: 3 corn).
  - composter (`compost.py`, levels 1–6, stack refilled): corn seeds 70/200 = 35.0 % (0.35; an earlier 60-try run
    gave 29), corn 38/60 = 63.3 % (0.65 ± 6 %), cornbread 50/60 = 83.3 % (0.85 ± 5 %); corncob 0.25 in CD-05.
    (A 200-try seeds run with only 64 seeds in hand read 13 % — the empty clicks; discarded.) Corncob fuel: CD-05.
- delta **CA15**: MMLib's replacement of `wantsToPickUp` is not reproduced. Here villagers pick up corn *and*
  keep vanilla's wanted items (wheat, seeds, bone meal for farmers); in the reference, any mod using MMLib makes
  villagers pick up only the food map's items (bread, potato, carrot, beetroot, corn). Reproducing it needs
  replacing vanilla villager behaviour for every villager (no hook, and it would break vanilla farming). Food
  sharing between villagers uses the engine's vanilla rule; not tested with corn.
- deltas: CA15 new.
- next: CD-17 (advancements, lang, creative tab audit).

## CD-17 Advancements, lang, creative tab audit — PASS — 2026-11-17
- base: farmersdelight-horizon e7215ed | addon commit: (this commit) | build pin afe471cf
- advancements (fd-port, `CD14`; `../run/shots/cd-17/adv.py`): the 36 carried advancements (13 CD + 23 recipe
  unlocks; every criterion is `inventory_changed` or `recipe_unlocked`) revoked for the test player → saved file
  shows **0/36**; then the 22 items they name obtained with `/give` into an emptied inventory → **36/36 done**,
  including `corn_knowleage` (11 foods) and `stuffing_chef` (cornbread stuffing + FD stuffed pumpkin block). (A first
  pass read 17/36: the inventory was full, so gives fell on the ground, and `save-all` is not a command here — the
  file was read before it was written; `horizon-ctl save` fixed the readout.) `macarthur` was also earned by
  equipping the pipe in CD-16.
- lang: `tools/test_lang_cd.py` (new; MD-11's audit for CD's ids: every item/block declaration, tab title, popcorn
  message, advancement titles/descriptions = 55 core keys). en_us and zh_cn have all 55; ja_jp, ru_ru, uk_ua lack 5
  (pipe, corncob, macarthur, tab); ca_es, it_it, it_ch, zh_hk, zh_tw lack 29 and ko_kr 30 (all advancements, pipe,
  corncob, tab); **de_de lacks all 55: upstream's file names every key under the old namespace `corndelight`**
  (`item.corndelight.corn`, …). Missing keys fall back to en_us, as on NeoForge. Kept as carried: quirk **CQ11**
  (incomplete upstream locales, de_de under the wrong namespace). The plan's "12 locales without missing keys"
  cannot hold without writing translations, which the port does not do.
- in game: language zh_cn → held corn reads "玉米", ja_jp → "トウモロコシ" (`name-zh_cn.png`, `name-ja_jp.png`;
  popcorn box "爆米花桶" / "ポップコーンバケット" in the files); back to en_us.
- creative tab: unchanged since CD-04 (`itemGroup.corn_delight`, 26 items in registry order); no item added since.
- deltas: none new (CQ11 recorded).
- next: CD-18 (CDM4 demo, validation matrix, release).

## CD-18 CDM4 demo, validation matrix, release — IN PROGRESS — 2026-11-17 (paused on user request)
- base: farmersdelight-horizon c2ac486 (`3.6.30-horizon.3`, release commit; **not tagged yet**) | addon commit:
  (this WIP commit) | build pin afe471cf
- written: `horizon-mod.toml` pins `ported_farmersdelight = "=3.6.30-horizon.3"` (version `1.1.8-horizon.1`); README
  rewritten for the release (install, reference statement AD1, CA1–CA15 as player-visible differences, kept quirks
  CQ1–CQ9 and CQ11, credits incl. MMLib as behaviour reference only).
- packages (in `../dist/` with `.sha256`): `ported_farmersdelight-3.6.30-horizon.3.hmod` (2947831 bytes, SHA-256
  40a687b8…cab97), `ported_corn_delight-1.1.8-horizon.1.hmod` (158519 bytes, d67d20da…d5bd1),
  `ported_moredelight-26.9.16-horizon.2.hmod` (139903 bytes, 5ae75940…786e); all three pass `cargo horizon-mod check`.
  Rebuild them if any source changes before tagging.
- checks done: base fmt/clippy/test (98 + 1 ignored), carry 2872, decl/tooltip/worldgen --check, tools/test_*.py;
  CD fmt/clippy/test (18), carry 267, decl 28, villages 2, trades 9, test_carry/decls/lang; MD carry re-pinned to
  base c2ac486 with identical carried files (225), MD tests, decl 34, lang --strict 0 gaps.
- recipe ambiguity over all three (MD `tools/recipe_overlap.py`, now with repeatable `--addon` and
  `neoforge:compound`): 1749 recipes, 79 from the add-ons, 0 skipped, **0 add-on conflicts**.
- release install in fd-port: the two native packages in `horizon-home/instances/fd-port/horizon-native-mods/`
  (`ported_farmersdelight.hmod`, `ported_corn_delight.hmod`), `horizon-mods.txt` turns on all three, MD `.2` in
  `horizon-mods/`; launcher `native-build --instance fd-port` → `native-afe471c-34d86ab9d16b` (release build).
  NOTE: `run/rebuild.sh` builds from the source trees instead and would replace it.
- matrix rows done (world `CDV8`, seed 8; `../run/shots/cd-18/`):
  - V8 PASS: `CDV8` created base-only ("content from 1 mod(s)", `corn_delight:corn` unknown), reopened with MD+CD:
    "content from 3 mod(s)", `corn_delight: base api 1`, no ERROR lines, CD/MD items obtainable; no wild corn near
    spawn (old chunks).
  - V4 (part): creative page 2 shows Corn Delight (26 items), Farmer's Delight and More Delight tabs
    (`creative-p2.png`); MD stone knife cut CD corn on an FD board (+2 seeds, +1 corncob, 131 → 130); recipe report
    above.
  - V9 PASS: corn (lower 3, 3, 7 + upper 2), nachos 2, popcorn 3 identical after a full restart; a pot cooking corn
    soup (CookTime 82 at quit, 98 after) finished → corn soup.
  - V10 (part, dedicated server): server re-exported from the two release packages (unpacked to
    `run/native-release-src/`) → `run/server-engine`, client copy from `native-afe471c-34d86ab9d16b`, MD `.2` on server
    and both clients (sha checked); "content from 3 mod(s)". Bob equipped the cob pipe → Alice sees it on Bob's head
    (`v10-alice-sees-bob-pipe.png`; Bob got "General of the Maize"); Alice took a nachos bowl with a bowl, Bob a
    caramel popcorn bare-handed; both clients show nachos 2 / popcorn 2; Bob cut corn with the MD stone knife on a
    board (+2 seeds +1 corncob). NOT DONE: a completed corn trade on the server (stopped while summoning farmers).
- still to do: V10 trade; V3 summary (base + CD: CD-06…CD-17 entries); V5 (CD without base: instance with only the CD
  package → refusal), V6 (CD built with `=3.6.30-horizon.2` against base `.3` → refusal; also the old MD `.1` package
  against base `.3`), V7 (CD removed from a world: record), V11 (genCornFarm CA14, villagersTradeCorn CD-15,
  farmersBuyFDCrops CA9, FD foodEffectTooltip), V12 (1000 corn vs 1000 wheat tick time, FD VALIDATION_PLAN §3.5);
  MD re-validation rows against base `.3` (V2/V5/V6/V10 at least) and MD PROGRESS entry; then tag base
  `v3.6.30-horizon.3`, CD `v1.1.8-horizon.1`, MD `v26.9.16-horizon.2`, push tags; CHECKPOINT.
- left running/changed at pause: dedicated server (`run/fd-server`) with Alice and Bob online on the CD-09 pad
  (nachos 2, popcorn 2, board with 1 corn at 60009,159,60000, a NoAI farmer may exist near 60011,159,59997); the
  fd-port game was quit earlier? — no: the single-player game on `CDV8` is still open. random_tick_speed in CDV8 is 3.
- next: CD-18 (continue from "still to do").

## CD-18 CDM4 demo, validation matrix, release — PASS (LAN: ENVIRONMENT-BLOCKED) — CDM4 closed — 2026-11-17
- base: farmersdelight-horizon c2ac486 (`3.6.30-horizon.3`, tag `v3.6.30-horizon.3`) | addon commit: (this commit),
  tag `v1.1.8-horizon.1` | build pin afe471cf
- release: `../dist/ported_corn_delight-1.1.8-horizon.1.hmod` (158772 bytes, SHA-256 daf778b0…b796; rebuilt today:
  only README.md differs from the WIP package, which gained the removal paragraph below; `cargo horizon-mod check`
  clean; every packaged file byte-identical to this commit's tree). Base `.3` package 40a687b8…cab97 and MD `.2`
  5ae75940…786e unchanged and identical to their trees. Carry re-pinned to the base release commit c2ac486
  (`tools/carry_rules_cd.toml.in`): 267 carried files byte-identical, only the manifest's pin/hashes changed.
- checks: base cargo test 98 + 1 ignored, carry 2872, decl 237, tooltips/worldgen/fixtures --check, 9 tools/test_*.py;
  CD cargo test 18, carry 267, decl 28, villages 2, trades 9, 3 tools/test_*.py; MD carry 225, decl 34, lang --strict
  0 gaps, 4 tests; `recipe_overlap.py --addon moredelight --addon corndelight`: 1749 recipes (79 add-on), 0 skipped,
  0 add-on conflicts (`../run/shots/cd-18/recipe-overlap.txt`).
- ADDONS_VALIDATION §4, Corn Delight rows (evidence `../run/shots/cd-18/`; world `CDV8`, seed 8, release build
  `native-afe471c-34d86ab9d16b` of the three packages):

  | Row | Result | Evidence |
  |---|---|---|
  | V3 base + CD | PASS | §3.2 = CD-05; §3.3 = CD-08 (wild corn, 3 seeds), CD-13 (chest loot), CD-14 (village farms), CD-15 (trades); §3.4 = CD-11/CD-12; CD-06…CD-17 acceptance all PASS (entries above) |
  | V4 base + MD + CD | PASS (dedicated server) / LAN ENVIRONMENT-BLOCKED | creative page 2 shows the CD (26 items), FD and MD tabs (`creative-p2.png`); recipe report above; MD stone knife cut CD corn on an FD board in single player (+2 seeds +1 corncob, 131 → 130, twice) and on the dedicated server (Bob); server + Alice + Bob all with base `.3`, MD `.2`, CD `.1`. LAN: the offline developer session refuses `lan open` (as MD-08/MD-12) |
  | V5 base absent | PASS | instance `cd-nobase` with only the CD package: `native-build` refuses "ported_corn_delight requires missing mod ported_farmersdelight" (`v5-nobase-build.log`); starting the instance anyway runs the plain game without CD (1658 items). MD `.2` alone: startup refused, same message (`v5-md2-nobase.log`) |
  | V6 wrong base version | PASS | CD package repacked in the scratchpad with `=3.6.30-horizon.2` + base `.3`: `native-build` refuses "ported_corn_delight requires ported_farmersdelight =3.6.30-horizon.2, but installed version is 3.6.30-horizon.3" (`v6-cd-wrongpin-build.log`); old MD `.1` with base `.3`: startup refused with the same wording (`v6-md1-base3.log`); instance deleted (launcher Trash) |
  | V7 CD removed from a world | PASS (recorded) | see below; WARN "mod ported_corn_delight was 1.1.8-horizon.1 when the world was saved, now missing" (`v7-cd-off.log`) |
  | V8 CD added to a base-only world | PASS | WIP part above (`CDV8` base-only, then MD+CD: "content from 3 mod(s)") |
  | V9 save/reload/restart | PASS | WIP part above (corn states, nachos/popcorn servings, mid-cook corn soup) |
  | V10 multiplayer | PASS (dedicated server) / LAN ENVIRONMENT-BLOCKED | WIP part above (cob pipe seen on Bob's head, nachos/popcorn servings on both clients, cutting) + today: a summoned farmer (first try) offered `corn_delight:corn` 1 → emerald 1 (16 uses, xp 2) next to wheat; Alice put 1 corn in the merchant slot, took the emerald (`v10-server-corn-trade.png`); server `Offers.Recipes[0].uses` = 1 |
  | V11 config | PASS (recorded) | `genCornFarm`: inert (CA14, CD-14); `villagersTradeCorn = false`: 0/15 L1 and 0/15 L2 farmers after a restart (CD-15); FD `farmersBuyFDCrops`: no such key in FD 26.3, always true (CA9, BX-06); FD `enableFoodEffectTooltip = false` removes MD's tooltip lines (BX-03/MD-10; base tooltip code unchanged in `.3`: `git diff v3.6.30-horizon.2 c2ac486` touches only an added `Values::bool_named`); Corn Delight has no effect tooltips upstream (no `addFoodEffectTooltip` in CD) |
  | V12 performance | PASS | below |

- V7 detail: snapshot with random ticks off (`v7-before.txt`): corn lowers at -1/1/2,117,-10 (age 3 alone; 7+2; 7+5),
  nachos 2, popcorn box 3, inventory with corn/seeds/corncob/popcorn. CD turned off (`horizon-mods.txt`, native
  rebuild): all CD blocks read as air, CD stacks read as `minecraft:air` keeping their counts (`v7-off.txt`). CD back
  on: everything returned **except the corn at -1,117,-10** (`v7-on.txt`). Control: the same corn survives a plain
  restart with CD on. Second run with one popcorn box in each chunk: the box in chunk 0 (3,117,-6) returned, the box
  in chunk −1 (-2,117,-7) did not (`v7b-*.txt`). Chunk −1 holds the lit stove and cooking pot; blocks there are lost,
  consistent with that chunk being saved again while CD is off (unknown blocks written as air). Recorded as engine
  observation **E-42** (unknown mod blocks are kept only in chunks not saved while the mod is missing); README says
  so and advises a backup. No promise in the plan; no delta.
- V12 detail (`v12-ticktime*.log`): 1000 crops (40×25 on farmland with 5 water rows), player 30–70 blocks away,
  `random_tick_speed 3`, day frozen, `/tick query` 100-tick samples. Alternating phases: empty 4.00 / 4.58 ms, wheat
  4.30 / 4.85, corn 4.68 / 4.90 (background drifted 3.6 → 4.9 ms). Starting at age 3 so corn grows upper halves:
  corn 4.12 / 4.43 ms, wheat 4.35 / 4.45 (6 samples each). Growth over ~4 min: corn 365 / 1000 advanced, wheat 332.
  **No measurable cost for corn over wheat** (differences −0.2…+0.4 ms, inside the drift). First attempt on dry
  farmland: corn's farmland turned to dirt (254/1000 in 3 min, corn popped off) while wheat's did not — the known
  kept quirk CQ7 (corn not in `#minecraft:maintains_farmland`, as upstream); that run was discarded.
- MD re-validation on base `.3` (MD PROGRESS entry "CD-18 (MD side)"): §3.1 in `CDV8` — stone knife crafted in the
  2×2 grid; potato and bread cut with it (diced potatoes, 4 bread slices, durability −1 per cut); a potato left on
  the board kept across a full restart (render upright like every block item, seen face-on from the south,
  `v2-md-board-*.png`); bread slice smelted → toast. Log errors: only the 3 known M0 crate-condition lines.
- CDM4 world tour: village corn farms (CD-14, 26 villages), chest loot (CD-13, 30 chests per table), trades (CD-15 in
  single player, CD-18 on the dedicated server) — all recorded in game.
- cleanup: test fields removed, forceload none, `random_tick_speed` 3, `advance_time` true in CDV8; the furnace and
  marker blocks removed; fd-port's mod list has all three on (release packages, CD package re-copied); clients and
  dedicated server stopped; the user's FDTest world was not opened.
- deltas: none new. Engine observation E-42 new. Quirks: CQ7 seen again (no new id).
- **Corn Delight complete (CD-01…CD-18).** next: none in the current scope (report to the user).

## RT-03 Retarget to Sunrise 2d81263 — PASS (smoke; full re-validation NOT RUN) — 2026-11-17
- build pin: sunrise@2d8126336e579777eabf9b2fd8b3d476236a04f2 | base commit: f267df5 (3.6.30-sunrise.1) | mod commits:
  5842e6d + this | version 1.1.8-sunrise.1 (not tagged/released yet). `main` converted in place (user's choice).
- did: `sunrise-mod.toml` (dependency `=3.6.30-sunrise.1`), API from the SDK path; `tools/target.toml.in` +
  `tools/target.py` (copy of the base's; `gen_cd_decls.py` writes `data/corn_delight/sunrise/` and `src/engine.rs`,
  `gen_villages.py` writes `sunrise:add_to`); `play_sound` gets `except = None`; `tools/cargo_dev.py` points the
  SDK path at the base's `.sunrise/` (one copy of the API crates in the lockfile); carry re-pinned to the base
  commit (wild corn biome modifier now `sunrise:climate`). README for Sunrise.
- in game (with the base, `SRTest`; base PROGRESS RT-03): 3 mods loaded, 0 errors; corn grew to lower age 7 at
  random tick speed 200; bone meal on a lone lower 7 placed an upper half (age 3); a hand-placed upper half
  survives neighbour updates; `recipe give corn_delight:corn_crate` works.
- observation (no delta): Sunrise gives a mod block random ticks as its template does (`random_tick` doc), so a
  lower corn at max age no longer ticks: an upper half is placed only by the rolls at ages 4–6, else by bone meal.
  This is upstream's behaviour (CornCrop/HighCropBlock keep CropBlock's `isRandomlyTicking = !isMaxAge`); at
  Horizon the max-age lower still ticked. Seen as a lone lower 7 after a fast time-lapse.
- not run: CDM4 tour, villages/loot/trades, popcorn box/nachos, restart, dedicated server, V3/V4/V12 matrix rows.
- checks: cargo_dev test 18 passed, clippy -D warnings, fmt; carry 267, decl 28, villages --check; 3 tools tests.
- deltas: none new.
- next: re-validation on Sunrise, then release 1.1.8-sunrise.1 with the base.

## RT-04 Sunrise re-validation and release 1.1.8-sunrise.1 — PASS (LAN: ENVIRONMENT-BLOCKED) — 2026-11-18
- build pin: sunrise@2d8126336e579777eabf9b2fd8b3d476236a04f2 | base commit: 8911db2 (`3.6.30-sunrise.1`, tag
  `v3.6.30-sunrise.1`) | mod commit: (this commit), tag `v1.1.8-sunrise.1`. Carry re-pinned to 8911db2: 267
  carried files byte-identical, only the manifest's pin changed.
- release packages (`../dist/`, `cargo sunrise-mod build`; every packaged file byte-identical to its tree, plus the
  generated `uses.json`): base `ported_farmersdelight-3.6.30-sunrise.1.smod` 2998820 B, SHA-256 b4a8e2b6…;
  CD `ported_corn_delight-1.1.8-sunrise.1.smod` 166430 B, 02ed700e…; MD `ported_moredelight-26.9.16-sunrise.1.smod`
  139901 B, 8b208f89… (full hashes in the `.sha256` files). Fresh instance `fd-release`: the two native packages
  unpacked and `native-build` → built; MD enabled in `sunrise-mods.txt`; new world `RelTest`: "content from
  3 mod(s)", 0 ERROR lines, MD stone knife cut CD corn on an FD board in survival (131 → 130, corncob + seeds).
- ADDONS_VALIDATION §4 on Sunrise (`../run/shots/RT-04/`; base entry for the FD rows):
  | Row | Result | Evidence |
  |---|---|---|
  | V3 base + CD | PASS | nachos: empty hand → "You need a Bowl to eat this.", 4 bowls → 4 nachos bowls, 0 → next use breaks it, 1 bowl dropped; popcorn box: bare hand ×3 → caramel popcorn, the last + paper, box gone; bowl in the main hand → message + serving (CD-11's off-hand pass); corn soup eaten → Comfort 3:00, bowl back; corn ages kept through restarts |
  | V4 base + MD + CD | PASS (single player, dedicated server) / LAN ENVIRONMENT-BLOCKED | MD stone knife cuts CD corn (+2 seeds +1 corncob) in single player, on the server (Bob) and from the release packages |
  | V5 base absent | PASS | CD alone: `native-build` refuses "ported_corn_delight requires missing mod ported_farmersdelight"; MD alone on a plain server: "mod load refused: ported_moredelight requires missing mod ported_farmersdelight" |
  | V6 wrong base version | PASS | CD pinned `=3.6.30-sunrise.0` with base `.1`: "requires ported_farmersdelight =3.6.30-sunrise.0, but installed version is 3.6.30-sunrise.1" |
  | V7 / V8 / V11 | carried from CD-18 (no code change since; engine observation E-42 not re-run) | — |
  | V9 save/reload/restart | PASS | two full restarts: nachos 3, popcorn 2, corn age 2 and 6, board item, mid-cook MD pot (`restart-*.txt`) |
  | V10 multiplayer | PASS (dedicated server + Alice + Bob) / LAN ENVIRONMENT-BLOCKED (`lan open` refused in the offline developer session) | server engine exported with `native-build --server-output`; handshake ok; cutting (Bob); pot through Bob's menu (corn soup; boiled corn first because the corn sat alone for 100 ticks); nachos and popcorn servings by both players, counts in sync on both clients; cob pipe on Alice's face seen by Bob (`mp-cob-pipe-bob-sees-alice.png`); "General of the Maize" on equip; farmer offering corn 1 → emerald 1 (1 of 3 summoned), Alice traded, `uses` = 1 |
  | V12 performance | carried from CD-18 (no code change) | — |
- checks: cargo_dev test 18, clippy -D warnings; carry 267, decl 28, villages 2, trades 9; 3 tools/test_*.py.
  `cargo sunrise-mod check` cannot compile CD alone: "cannot find module or crate `ported_farmersdelight`" — the
  check has no way to resolve a dependency mod's crate (Horizon's `check` passed). **E-44 (new)**, workaround: the
  crate is checked through `tools/cargo_dev.py` and built by the launcher's `native-build` (instance and server
  export). The base's own `check` passes (rustup `wasm32-unknown-unknown` target added for it).
- deltas: none new. Engine gap E-44 new.
- next: none in the retarget scope.

## REG-02 Registry PR #5 updated after the base listing — PASS (repack: ENVIRONMENT-BLOCKED) — 2026-11-22
- base: `ported_farmersdelight 3.6.30-sunrise.1` listed on sunrise-mods `main` (PR #4 merged 2026-11-22, repacked
  file `1c5c0d01…`) | CD commit 3ecabda (unchanged; package `02ed700e…` unchanged).
- registry: branch `add-ported-corn-delight` updated from upstream `main` (aea7e12, pushed); local
  `registry check` with the Nightly tool reports nothing for this entry (the 77 errors are other mods' files not
  downloaded locally). MD's #6 updated the same way (77229bb). Comments on #5/#6.
- repack (the maintainers' 2026-11-20 request): **ENVIRONMENT-BLOCKED, E-45 (new)**. `cargo sunrise-mod build` of
  Nightly 9425651 refuses an add-on: "code link requirements refused: ported_corn_delight requires missing mod
  ported_farmersdelight". Its build plan's mod folder is the project alone (`cargo-sunrise-mod/src/dev.rs`, `mods:
  project`; `sunrise-native-build` `scan_bundles`), so a dependency mod cannot be supplied. The `2d81263` tool built
  CD in RT-04. Not fixed on Sunrise main (last `dev.rs` change 2026-11-21), no upstream issue. Workaround: none for the
  package. The `.1` file keeps its schema-1 uses list. **This also blocks CD's Nightly release (RT-11)** until fixed;
  filing it upstream needs the user's OK.
- next: back to RT-09 on branch `nightly` (stash "RT-09 wip").
