"""Inventory every weapon-fire prefix across banks and shared assets."""
import json
import os
import re
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))

bank_index = json.load(open(os.path.join(HERE, "bank_names.json"), encoding="utf-8"))
asset_index = json.load(open(os.path.join(HERE, "audio_scan.json"), encoding="utf-8"))

by_prefix = defaultdict(lambda: {"bank": [], "asset": [], "close": 0, "sil": 0, "loop": 0})

for bank, names in bank_index.items():
    if not isinstance(names, list):
        continue
    for name in names:
        m = re.match(r"^([a-z0-9]+?)_", name.lower())
        if not m:
            continue
        prefix = m.group(1)
        entry = by_prefix[prefix]
        entry["bank"].append(name)
        low = name.lower()
        if "close" in low and "silenced" not in low and not any(t in low for t in ("distant", "far", "loop", "tail", "double")):
            entry["close"] += 1
        if "silenced" in low and "close" in low and not any(t in low for t in ("distant", "far", "loop", "tail")):
            entry["sil"] += 1
        if "loop" in low and "tail" in low:
            entry["loop"] += 1

for asset, names in asset_index.items():
    for name in names:
        key = name.get("name", "") if isinstance(name, dict) else str(name)
        m = re.match(r"^([a-z0-9]+?)_", key.lower())
        if not m:
            continue
        prefix = m.group(1)
        entry = by_prefix[prefix]
        entry["asset"].append(key)
        low = key.lower()
        if "fire" in low and "close" in low and "silenced" not in low:
            entry["close"] += 1
        if "silenced" in low and "close" in low:
            entry["sil"] += 1
        if "loop" in low:
            entry["loop"] += 1

rows = []
for prefix, entry in by_prefix.items():
    total = len(entry["bank"]) + len(entry["asset"])
    if not (entry["close"] or entry["sil"] or entry["loop"]):
        continue
    sources = []
    if entry["bank"]:
        sources.append("bank")
    if entry["asset"]:
        sources.append("assets")
    rows.append((entry["close"], prefix, entry["sil"], entry["loop"], total, "+".join(sources)))

rows.sort(reverse=True)
print(f"prefixes with usable fire audio: {len(rows)}\n")
print(f"{'prefix':12s} {'close':>5s} {'sil':>4s} {'loop':>4s} {'total':>5s}  source")
for close, prefix, sil, loop, total, src in rows:
    print(f"{prefix:12s} {close:5d} {sil:4d} {loop:4d} {total:5d}  {src}")

json.dump(
    {prefix: {"close": close, "sil": sil, "loop": loop} for close, prefix, sil, loop, _t, _s in rows},
    open(os.path.join(HERE, "prefix_inventory.json"), "w", encoding="utf-8"),
    ensure_ascii=False,
    indent=1,
)
