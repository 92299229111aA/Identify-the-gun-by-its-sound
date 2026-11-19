"""Summarise the AudioClip names found by scan_audio.py."""
import json
import os
import re
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, "audio_scan.json"), encoding="utf-8"))

total = sum(len(v) for v in data.values())
names = [c["name"] for v in data.values() for c in v]
print(f"files={len(data)} clips={total} unique={len(set(names))}")

print("\n=== per-file (top 12 by clip count) ===")
for f, clips in sorted(data.items(), key=lambda kv: -len(kv[1]))[:12]:
    print(f"{f:28s} {len(clips):5d}")

print("\n=== first 40 names from the biggest audio file ===")
biggest = max(data.items(), key=lambda kv: len(kv[1]))[0]
for clip in data[biggest][:40]:
    print(f"  {clip['name']!r}  ch={clip['channels']} freq={clip['frequency']} len={clip['length']}")

pattern = re.compile(r"(fire|shot|weap|gun|rifle|pistol|shotgun|shot_|_fire)", re.I)
hits = [n for n in names if pattern.search(n)]
print(f"\n=== names matching weapon/fire keywords: {len(hits)} ===")
for n in hits[:60]:
    print("  ", n)

print("\n=== token frequency in names (top 40) ===")
tokens = Counter()
for n in names:
    for token in re.split(r"[^A-Za-z0-9]+", n.lower()):
        if token and not token.isdigit():
            tokens[token] += 1
for token, count in tokens.most_common(40):
    print(f"  {token:22s} {count}")
