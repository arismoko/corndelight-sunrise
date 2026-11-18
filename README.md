# Corn Delight — Sunrise port

A native [Sunrise](https://github.com/sunrise-org/sunrise) mod porting Corn Delight 1.1.8 (an add-on for Farmer's
Delight) to Minecraft 26.3: two-tall corn, wild corn in temperate biomes, corn kitchen (pot recipes, nachos and the
popcorn box feasts), the cob pipe, village corn farms, chest loot and villager/wandering-trader trades.

Version `1.1.8-sunrise.1`, for the Farmer's Delight Sunrise port `3.6.30-sunrise.1` exactly, built for Sunrise
`2d8126336e579777eabf9b2fd8b3d476236a04f2`. (`1.1.8-horizon.1`, tag `v1.1.8-horizon.1`, was the Horizon `afe471cf`
build.)

**Download:** [Releases](https://github.com/play-go/corndelight-horizon/releases) (`ported_corn_delight-<version>.smod` with its SHA-256). Needs the
[Farmer's Delight Sunrise port](https://github.com/play-go/farmersdelight-horizon); works alongside [More Delight](https://github.com/play-go/moredelight-horizon).

## Install

Unpack `ported_corn_delight-<version>.smod` (or put this repository's source) next to the
[Farmer's Delight port](https://github.com/play-go/farmersdelight-horizon) (`3.6.30-sunrise.1`) in the same mods folder and build both with
`sunrise-launcher native-build <mods folder> --instance <instance> --trust-native-code`; the launcher builds both together (Corn Delight's code calls the base's
public `api` module: crops, feasts, wild crops, config). It refuses to build Corn Delight without the base, or with
another base version. A dedicated server needs both in its native build too.

**Multiplayer:** every player needs the Sunrise client with the same Farmer's Delight port and this mod.

**Removing the mod from a world** (observed on Horizon; not yet re-checked on Sunrise): the game logs a warning ("mod ported_corn_delight was … now missing") and opens
the world. Corn Delight items read as empty stacks while the mod is off and come back when it is turned on again.
Placed Corn Delight blocks (corn, nachos, popcorn boxes) show as air; they come back only in chunks the game did not
save again in the meantime. A chunk that is saved while the mod is off (for example one with a lit stove or anything
else that changes) loses them for good (engine observation E-42). Back up the world first.

## Reference

There is no Corn Delight for Fabric or for Minecraft 26.x. The port follows Corn Delight 1.21 (NeoForge 1.21.1,
commit `ab03743e`) for Corn Delight's own behaviour, and Farmer's Delight Refabricated 26.3 (the base port) for
everything Corn Delight inherits from Farmer's Delight (feasts, wild crops, effects, cooking and cutting). The data
is converted to 26.3 formats by a script (`tools/carry_cd.py`); the corn crop, feasts, chest loot and the rest are
re-implemented from the reference's behaviour. MMLib (the library Corn Delight uses) was read for behaviour only; no
code of it is used or copied.

## Differences from the reference

- CA1: wild corn patches are vanilla feature compositions in Farmer's Delight 26.3's shape; `/place feature` places
  one try per call (the 64 tries live in the placed feature).
- CA2: the chest loot (village houses, shipwreck supply) is added in code as an extra pool, with the same draws.
- CA3: village corn farms are added to the house pools as data.
- CA4: farmers' cornbread/tortilla and the wandering trader's corn seeds/popcorn box give a fixed count (11, 11, 5,
  2: the middle of the reference's random range), because the engine ignores the trade `set_count` modifier (E-41).
- CA5: `c:foods/milk` alternatives that no mod defines are removed from 5 recipes.
- CA6: the feasts and wild corn follow Farmer's Delight Refabricated 26.3 (the base), not upstream FD 1.21.1.
- CA9: the farmer trades ignore Farmer's Delight's `farmersBuyFDCrops` (the base has no such key; always on).
- CA10: the config file is `config/ported_corn_delight-common.toml`.
- CA11: the nachos' empty tray uses FD 26.3's shepherd's pie leftover texture.
- CA12: corn growth does not fire other mods' crop-growth hooks.
- CA13: suspicious stew from wild corn is a generated recipe (26.3 lists stew flowers per recipe).
- CA14: `genCornFarm = false` does not remove the village corn farms (engine: pool additions take no conditions).
- CA15: villagers pick up corn and keep picking up vanilla's items; MMLib's replacement of the villager's wanted
  items (only foods) is not reproduced.
- `villagersTradeCorn` takes effect when a world is opened, not on `/reload`.

Kept quirks of the reference: CQ1 each mature half of a corn drops its own loot; CQ2 the popcorn box's message passes
an unused argument; CQ3 farmers buy 1 corn for 1 emerald; CQ4 both wandering trades are in the common pool; CQ5 the
taiga corn farms' jigsaw names the plains street pool; CQ6 the upper half grows on its own and bone meal overflows
into it; CQ7 dry farmland under corn turns to dirt (corn is not in `#maintains_farmland`); CQ8 holding an item with
an empty off hand still takes popcorn (through the off hand); CQ9 the popcorn box drops nothing when broken; CQ11
several locales are incomplete, and de_de names every key under an old namespace (English is shown).

## Building from source

The base mod is not in `Cargo.toml` (the launcher adds it). Local checks use a checkout of the
[base](https://github.com/play-go/farmersdelight-horizon) beside this repository:

```sh
python3 tools/cargo_dev.py test
python3 tools/cargo_dev.py clippy --all-targets -- -D warnings
tools/carry.sh --check
python3 tools/gen_cd_decls.py --check
python3 tools/gen_villages.py --check
python3 tools/gen_trades.py --check
python3 tools/test_carry_cd.py && python3 tools/test_cd_decls.py && python3 tools/test_lang_cd.py
```

## Credits

Corn Delight © 2022 Zheng Syameimaru and the MCMOD Modding Group (MIT). Farmer's Delight © 2020 vectorwing and
contributors (MIT); Farmer's Delight Refabricated by MehVahdJukaar, cassiancc and contributors. MMLib by the MCMOD
Modding Group (behaviour reference only). See `NOTICE`.
