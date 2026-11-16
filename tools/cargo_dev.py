#!/usr/bin/env python3
"""Run cargo on this mod with the base mod as a dependency, as the launcher builds it.

The launcher adds `ported_farmersdelight = { path = …, package = "farmersdelight-horizon" }` to the mod's
Cargo.toml from horizon-mod.toml [dependencies], and refuses a Cargo.toml that already names it. For local
builds this script mirrors the mod into target/dev-crate/ (Cargo.toml + src/, symlinked sources), adds that
dependency pointing at a base checkout (default ../farmersdelight-horizon) and runs cargo there:

    python3 tools/cargo_dev.py test
    python3 tools/cargo_dev.py clippy --all-targets -- -D warnings
    python3 tools/cargo_dev.py --base /path/to/farmersdelight-horizon build
"""
import os
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main() -> int:
    args = sys.argv[1:]
    base = REPO.parent / "farmersdelight-horizon"
    if args[:1] == ["--base"]:
        base, args = Path(args[1]).resolve(), args[2:]
    with (base / "Cargo.toml").open("rb") as f:
        package = tomllib.load(f)["package"]["name"]
    dev = REPO / "target" / "dev-crate"
    dev.mkdir(parents=True, exist_ok=True)
    src = dev / "src"
    if not src.is_symlink():
        if src.exists():
            raise SystemExit(f"{src} exists and is not a symlink")
        src.symlink_to(REPO / "src")
    manifest = (REPO / "Cargo.toml").read_text()
    manifest = manifest.replace(
        "[dependencies]\n",
        f'[dependencies]\nported_farmersdelight = {{ path = "{base}", package = "{package}" }}\n',
        1,
    )
    manifest += "\n[workspace]\n"
    target = dev / "Cargo.toml"
    if not target.exists() or target.read_text() != manifest:
        target.write_text(manifest)
    env = dict(os.environ, CARGO_TARGET_DIR=str(REPO / "target"))
    return subprocess.call(["cargo", *args], cwd=dev, env=env)


if __name__ == "__main__":
    sys.exit(main())
