"""Validate exported clips against the manifest."""
import json
import os

import soundfile as sf

PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
manifest = json.load(open(os.path.join(PROJECT, "sounds", "manifest.json"), encoding="utf-8"))

bad = []
total = 0
for gun in manifest:
    for clip in gun["clips"]:
        total += 1
        path = os.path.join(PROJECT, clip["file"].replace("/", os.sep))
        try:
            info = sf.info(path)
            if info.frames == 0:
                bad.append((path, "empty"))
        except Exception as exc:  # noqa: BLE001
            bad.append((path, str(exc)))

print(f"checked={total} bad={len(bad)}")
for row in bad[:5]:
    print(" ", row)
print("example:", manifest[0]["name"], manifest[0]["clips"][0]["file"])
print("durations:", [c["duration"] for c in manifest[0]["clips"]])
print("sizes_kb:", [round(os.path.getsize(os.path.join(PROJECT, c["file"])) / 1024) for c in manifest[0]["clips"]])
