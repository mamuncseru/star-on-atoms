"""Fetch QuEra's public STAR circuits, pinned and verified.

The circuits this book measures were published by QuEra Computing for the
ETH QHack 2026 challenge. That repository carries no license file, so this
book does not redistribute them: it downloads them at one pinned commit and
checks every file against the SHA-256 recorded below. A file that changes
upstream fails here, loudly, instead of quietly changing every number in the
book.

Files land in data/external/eth_qhack_2026/ (git-ignored).

Run:  python tools/fetch_star_circuits.py
      python tools/fetch_star_circuits.py --check   (verify, download nothing)
"""

from __future__ import annotations

import hashlib
import pathlib
import sys
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEST = ROOT / "data" / "external" / "eth_qhack_2026"

REPO = "QuEraComputing/ETH_QHACK_2026"
COMMIT = "393312b5de1e7890c67d01775c948b4dcdde760d"   # main, 2026-09-04

SHA256 = {
    "assets/star_circuits/star_d=3.stim":
        "466bde2419d16edf960ab5c24dfe3cdb38e2be204d7db872ef7de9bc089555f9",
    "assets/star_circuits/star_d=5.stim":
        "34208f384a22ac31cec4b036e47d6087ee80729aea23e3c3d342b695a8518f94",
    "assets/star_circuits/star_d=7.stim":
        "83a1aa328a65beb6065d3913609c717726ebe70438936697b1068f38a09ae1f4",
    "assets/star_circuits/star_d=9.stim":
        "c8af0c95294d92cfbbb42c45456d7b1bb1526e347e7edf158320237b971d1479",
    "assets/star_circuits/star_d=11.stim":
        "e4f9dbb342f3fba3d0c0ab7fb834a689d2cb2294b3366adbcac74c9c34fc0ec1",
    "assets/star_circuits/star_d=13.stim":
        "30480f073b04c5691cbdf192db20d87087dd886077c88744b027a3beab7bcb39",
    "assets/star_circuits/star_d=15.stim":
        "3f150d148361f02ecd98792b9ca5b7c6a85188f38a998792acc6d00c523a8613",
    "assets/star_sim.svg":
        "76f1e49eba4673bebc504e21e26444cdd551bbc505d3e4825f87235908d96eb4",
}


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def local(name: str) -> pathlib.Path:
    return DEST / pathlib.Path(name).name


def main() -> int:
    check_only = "--check" in sys.argv
    DEST.mkdir(parents=True, exist_ok=True)
    bad = []
    for name, want in SHA256.items():
        path = local(name)
        if not path.exists() and not check_only:
            url = f"https://raw.githubusercontent.com/{REPO}/{COMMIT}/{name}"
            with urllib.request.urlopen(url, timeout=60) as response:
                path.write_bytes(response.read())
        if not path.exists():
            bad.append(f"{path.name}: missing (run without --check)")
        elif digest(path) != want:
            bad.append(f"{path.name}: SHA-256 mismatch — upstream changed, "
                       "or the download was corrupted")
    for line in bad:
        print(f"  ✗ {line}")
    if bad:
        return 1
    print(f"{len(SHA256)} files at {REPO}@{COMMIT[:10]} verified in "
          f"{DEST.relative_to(ROOT)}/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
