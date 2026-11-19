"""Read-only scan of the local Escape from Tarkov install for AudioClip assets.

Never writes to the game directory: it only opens *.assets files for reading and
records clip names/sizes into this project's tools/ folder.
"""
import json
import os
import sys
import time

import UnityPy

GAME_DIR = r"D:\tkfben\EscapeFromTarkov_Data"
OUT_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_scan.json")

SKIP_SUFFIXES = (".resS", ".resource")


def main() -> int:
    files = sorted(
        f
        for f in os.listdir(GAME_DIR)
        if f.endswith(".assets") and not f.endswith(SKIP_SUFFIXES)
    )
    total = len(files)
    print(f"scanning {total} asset files in {GAME_DIR}", flush=True)

    found: dict[str, list[dict]] = {}
    started = time.time()
    errors = 0

    for index, name in enumerate(files, start=1):
        path = os.path.join(GAME_DIR, name)
        size_mb = os.path.getsize(path) / (1024 * 1024)
        try:
            env = UnityPy.load(path)
            clips = []
            for obj in env.objects:
                if obj.type.name != "AudioClip":
                    continue
                try:
                    data = obj.read()
                    clips.append(
                        {
                            "name": getattr(data, "m_Name", "") or "",
                            "channels": getattr(data, "m_Channels", None),
                            "frequency": getattr(data, "m_Frequency", None),
                            "length": getattr(data, "m_Length", None),
                        }
                    )
                except Exception:
                    continue
            if clips:
                found[name] = clips
                print(
                    f"  [{index}/{total}] {name} ({size_mb:.1f} MB): {len(clips)} AudioClips",
                    flush=True,
                )
        except Exception as exc:  # noqa: BLE001 - report and continue
            errors += 1
            print(f"  [{index}/{total}] {name} ({size_mb:.1f} MB): ERROR {exc}", flush=True)

        if index % 50 == 0:
            elapsed = time.time() - started
            print(
                f"progress {index}/{total}  files-with-audio={len(found)}  "
                f"errors={errors}  elapsed={elapsed:.0f}s",
                flush=True,
            )
            with open(OUT_JSON, "w", encoding="utf-8") as handle:
                json.dump(found, handle, ensure_ascii=False, indent=1)

    with open(OUT_JSON, "w", encoding="utf-8") as handle:
        json.dump(found, handle, ensure_ascii=False, indent=1)

    clip_total = sum(len(v) for v in found.values())
    print(
        f"done: files-with-audio={len(found)} clips={clip_total} errors={errors} "
        f"elapsed={time.time() - started:.0f}s -> {OUT_JSON}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
