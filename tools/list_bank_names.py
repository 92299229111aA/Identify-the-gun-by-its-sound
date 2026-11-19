"""Print AudioClip naming samples for every weapon bank (read-only)."""
import json
import os

import UnityPy

BANKS = (
    r"D:\tkfben\EscapeFromTarkov_Data\StreamingAssets\Windows"
    r"\assets\content\audio\banks"
)
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "bank_names.json")

result = {}
for entry in sorted(os.listdir(BANKS)):
    if not entry.endswith(".bundle") or entry == "weaponsounds.bundle":
        continue
    bank_id = entry[: -len(".bundle")]
    path = os.path.join(BANKS, entry)
    names = []
    try:
        env = UnityPy.load(path)
        for obj in env.objects:
            if obj.type.name != "AudioClip":
                continue
            try:
                names.append(getattr(obj.read(), "m_Name", "") or "")
            except Exception:  # noqa: BLE001
                continue
    except Exception as exc:  # noqa: BLE001
        result[bank_id] = {"error": str(exc)}
        print(f"{bank_id:12s} ERROR {exc}", flush=True)
        continue
    result[bank_id] = names
    sample = ", ".join(sorted(names)[:6])
    print(f"{bank_id:12s} n={len(names):4d}  {sample}", flush=True)

with open(OUT, "w", encoding="utf-8") as handle:
    json.dump(result, handle, ensure_ascii=False, indent=1)
print("saved", OUT)
