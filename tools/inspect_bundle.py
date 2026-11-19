"""Inspect one EFT asset bundle for AudioClips (read-only)."""
import sys

import UnityPy

path = sys.argv[1]
env = UnityPy.load(path)

clips = []
others = {}
for obj in env.objects:
    name = obj.type.name
    others[name] = others.get(name, 0) + 1
    if name == "AudioClip":
        try:
            data = obj.read()
            clips.append(
                (
                    getattr(data, "m_Name", "") or "",
                    getattr(data, "m_Channels", None),
                    getattr(data, "m_Frequency", None),
                    round(getattr(data, "m_Length", 0) or 0, 3),
                )
            )
        except Exception as exc:  # noqa: BLE001
            clips.append((f"<read error {exc}>", None, None, None))

print("objects by type:", dict(sorted(others.items(), key=lambda kv: -kv[1])[:10]))
print(f"AudioClips: {len(clips)}")
for row in clips[:60]:
    print("  ", row)

# Try decoding the first clip to prove the samples are usable.
for obj in env.objects:
    if obj.type.name != "AudioClip":
        continue
    data = obj.read()
    try:
        samples = data.samples
    except Exception as exc:  # noqa: BLE001
        print("decode error:", exc)
        break
    if samples:
        for sample_name, payload in list(samples.items())[:3]:
            head = payload[:4]
            print(
                f"decoded {getattr(data, 'm_Name', '?')!r} -> {sample_name!r} "
                f"{len(payload)} bytes, magic={head!r}"
            )
    else:
        print("no samples returned for", getattr(data, "m_Name", "?"))
    break
