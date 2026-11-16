# Corn Delight — Horizon port

A native [Horizon](https://github.com/arismoko/horizon) mod porting Corn Delight 1.1.8 (an add-on for Farmer's
Delight) to Minecraft 26.3. Work in progress: see `PROGRESS.md`.

Requires the Farmer's Delight Horizon port (`ported_farmersdelight`) at exactly the version in `horizon-mod.toml`;
the launcher refuses to build Corn Delight without it. Corn Delight's code calls the base's public `api` module
(feasts, wild crops), so both are native mods built together by the launcher.

**Multiplayer:** every player needs the Horizon client with the same Farmer's Delight port and this mod.

## Reference

There is no Corn Delight for Fabric or for Minecraft 26.x. The port follows Corn Delight 1.21 (NeoForge 1.21.1,
commit `ab03743e`) for Corn Delight's own behaviour, and Farmer's Delight Refabricated 26.3 (the base port) for
everything Corn Delight inherits from Farmer's Delight (feasts, wild crops, effects, cooking and cutting). Data is
converted to 26.3 formats by a script.

## Building from source

The base mod is not in `Cargo.toml` (the launcher adds it). Local checks use a checkout of the base beside this
repository:

```sh
python3 tools/cargo_dev.py test
python3 tools/cargo_dev.py clippy --all-targets -- -D warnings
```

## Credits

Corn Delight © 2022 Zheng Syameimaru and the MCMOD Modding Group (MIT). Farmer's Delight © 2020 vectorwing (MIT);
Farmer's Delight Refabricated by MehVahdJukaar, cassiancc et al. See `NOTICE`.
