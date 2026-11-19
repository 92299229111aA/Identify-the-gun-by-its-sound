"""Export weapon fire samples from the local EFT install to OGG (read-only).

Clip names are inconsistent across banks ("ak74m_indoor_close_oneshot_01",
"akm_close_indoor_01", "m4a1_indoor_close_onseshot_01"), so selection works by
gun-name prefix over every bank, then decodes only the banks that hold a chosen
clip. Nothing under the game directory is written.

Volume policy: each gun gets one gain derived from the median RMS of its takes
(so guns are comparable in a quiz while takes inside a gun keep their relative
dynamics), capped so the loudest peak lands at PEAK_CEILING. A high-quality
Vorbis encode with that headroom keeps decode overshoot below full scale.
"""
import io
import json
import os
import subprocess
import sys
import tempfile

import imageio_ffmpeg
import numpy as np
import soundfile as sf
import UnityPy

BANKS_DIR = (
    r"D:\tkfben\EscapeFromTarkov_Data\StreamingAssets\Windows"
    r"\assets\content\audio\banks"
)
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
OUT_DIR = os.path.join(PROJECT, "sounds")
INDEX_JSON = os.path.join(HERE, "bank_names.json")

MAX_PER_GUN = 6
TARGET_RMS = 0.080
PEAK_CEILING = 0.700
VORBIS_QUALITY = "8"

# prefix, display name, caliber
WEAPONS = [
    ("ak74m", "AK-74M", "5.45x39"),
    ("akm", "AKM", "7.62x39"),
    ("ak101", "AK-101", "5.56x45"),
    ("m4a1", "M4A1", "5.56x45"),
    ("hk416", "HK 416A5", "5.56x45"),
    ("fal", "SA-58", "7.62x51"),
    ("aug", "AUG A3", "5.56x45"),
    ("scar", "SCAR-H", "7.62x51"),
    ("avt", "AVT-40", "7.62x54R"),
    ("mutant", "Mk47 Mutant", "7.62x39"),
    ("mp5", "MP5", "9x19"),
    ("mp7", "MP7", "4.6x30"),
    ("mpx", "MPX", "9x19"),
    ("p90", "P90", "5.7x28"),
    ("vityaz", "PP-19-01", "9x19"),
    ("vector", "Vector .45", ".45 ACP"),
    ("ash12", "ASh-12", "12.7x55"),
    ("vss", "VSS Vintorez", "9x39"),
    ("m9a3", "M9A3", "9x19"),
    ("rem870", "M870", "12ga"),
]

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def is_close_shot(name: str) -> bool:
    lowered = name.lower()
    if "close" not in lowered:
        return False
    return not any(
        token in lowered
        for token in ("silenced", "distant", "far", "loop", "tail", "double")
    )


def select(index, prefix: str):
    """Pick up to MAX_PER_GUN clips for a prefix, preferring outdoor close shots."""
    candidates = []
    seen = set()
    for bank, names in index.items():
        if not isinstance(names, list):
            continue
        for name in names:
            lowered = name.lower()
            if not lowered.startswith(prefix) or name in seen:
                continue
            if not is_close_shot(name):
                continue
            seen.add(name)
            candidates.append((bank, name))

    outdoor = sorted([c for c in candidates if "outdoor" in c[1].lower()], key=lambda c: c[1])
    indoor = sorted([c for c in candidates if "indoor" in c[1].lower()], key=lambda c: c[1])
    neutral = sorted(
        [
            c
            for c in candidates
            if "indoor" not in c[1].lower() and "outdoor" not in c[1].lower()
        ],
        key=lambda c: c[1],
    )
    chosen = outdoor[:MAX_PER_GUN]
    if len(chosen) < 3:
        chosen = (outdoor + neutral + indoor)[:MAX_PER_GUN]
    return chosen


def encode_ogg(data: np.ndarray, rate: int, out_path: str) -> None:
    """Encode float samples to OGG/Vorbis through the bundled ffmpeg."""
    with tempfile.TemporaryDirectory() as tmp:
        wav_path = os.path.join(tmp, "in.wav")
        sf.write(wav_path, data, rate, format="WAV", subtype="PCM_24")
        subprocess.run(
            [
                FFMPEG,
                "-y",
                "-loglevel",
                "error",
                "-i",
                wav_path,
                "-c:a",
                "libvorbis",
                "-q:a",
                VORBIS_QUALITY,
                out_path,
            ],
            check=True,
        )


def main() -> int:
    index = json.load(open(INDEX_JSON, encoding="utf-8"))
    os.makedirs(OUT_DIR, exist_ok=True)

    plan = {}
    for prefix, display, caliber in WEAPONS:
        chosen = select(index, prefix)
        if not chosen:
            print(f"skip {prefix}: no close-shot clips", flush=True)
            continue
        plan[prefix] = chosen

    by_bank = {}
    for prefix, chosen in plan.items():
        for bank, name in chosen:
            by_bank.setdefault(bank, []).append((prefix, name))

    decoded = {}
    for bank, wanted in by_bank.items():
        env = UnityPy.load(os.path.join(BANKS_DIR, f"{bank}.bundle"))
        lookup = {name for _, name in wanted}
        for obj in env.objects:
            if obj.type.name != "AudioClip":
                continue
            try:
                clip = obj.read()
            except Exception:  # noqa: BLE001
                continue
            name = getattr(clip, "m_Name", "") or ""
            if name in lookup and name not in decoded:
                decoded[name] = clip

    manifest = []
    for prefix, display, caliber in WEAPONS:
        chosen = plan.get(prefix)
        if not chosen:
            continue
        gun_dir = os.path.join(OUT_DIR, prefix)
        os.makedirs(gun_dir, exist_ok=True)

        rendered = []
        for _, name in chosen:
            clip = decoded.get(name)
            if clip is None:
                continue
            try:
                samples = clip.samples
            except Exception as exc:  # noqa: BLE001
                print(f"  decode failed {name}: {exc}", flush=True)
                continue
            if not samples:
                continue
            payload = next(iter(samples.values()))
            data, rate = sf.read(io.BytesIO(payload), dtype="float32", always_2d=True)
            rendered.append((name, data, rate))

        gain = 1.0
        rms_values = [float(np.sqrt((d**2).mean())) for _, d, _ in rendered if d.size]
        if rms_values:
            gain = TARGET_RMS / max(float(np.median(rms_values)), 1e-6)
            peak = max(float(np.abs(d).max()) for _, d, _ in rendered)
            if peak * gain > PEAK_CEILING:
                gain = PEAK_CEILING / max(peak, 1e-6)

        files = []
        for name, data, rate in rendered:
            scaled = np.clip(data * gain, -1.0, 1.0).astype(np.float32)
            out_name = f"{name}.ogg"
            out_path = os.path.join(gun_dir, out_name)
            encode_ogg(scaled, rate, out_path)
            files.append(
                {
                    "file": f"sounds/{prefix}/{out_name}",
                    "clip": name,
                    "duration": round(len(scaled) / rate, 3),
                    "channels": int(scaled.shape[1]),
                }
            )
        print(f"{prefix:8s} {display:14s} clips={len(files)} gain={gain:.2f}", flush=True)
        if files:
            manifest.append(
                {"id": prefix, "name": display, "caliber": caliber, "clips": files}
            )

    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    total = sum(len(g["clips"]) for g in manifest)
    print(f"done: guns={len(manifest)} clips={total}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
