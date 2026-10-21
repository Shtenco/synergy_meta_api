#!/usr/bin/env python3
"""Explicit developer-side clones. Never invoked by the HTTP service."""
import argparse
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = json.loads((ROOT / "upstreams.json").read_text(encoding="utf-8"))["sources"]

def main():
    ap = argparse.ArgumentParser()
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true")
    group.add_argument("--all", action="store_true")
    group.add_argument("--name")
    ap.add_argument("--depth", type=int, default=0)
    args = ap.parse_args()
    if args.list:
        for item in SOURCES:
            print(f'{item["name"]:35} {item["category"]:15} {item["url"]}')
        return
    selection = SOURCES if args.all else [i for i in SOURCES if i["name"] == args.name]
    if not selection:
        ap.error("Unknown upstream name")
    target_dir = ROOT / "upstream_sources"
    target_dir.mkdir(exist_ok=True)
    for item in selection:
        target = target_dir / item["name"]
        if target.exists():
            print("SKIP existing:", target)
            continue
        command = ["git", "clone", "--", item["url"], str(target)]
        if args.depth:
            command = ["git", "clone", "--depth", str(args.depth), "--", item["url"], str(target)]
        print("CLONE", item["url"])
        subprocess.run(command, check=True)

if __name__ == "__main__":
    main()
