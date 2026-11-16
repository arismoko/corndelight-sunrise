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
