"""Export three fire-sound variants per gun from the local EFT install.

standard   - outdoor close one-shots, unsuppressed
suppressed - close one-shots with the "silenced" set
auto       - a burst stitched from the one-shot takes at the weapon's real
             cyclic rate, followed by the game's own loop_tail clip

Read-only for the game directory; writes only under sounds/.
"""
import io
import json
import os
import subprocess
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

TARGET_RMS = 0.080
PEAK_CEILING = 0.700
VORBIS_QUALITY = "8"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# prefix, display, caliber, rpm (None = no automatic mode)
WEAPONS = [
    ("ak74m", "AK-74M", "5.45x39", 650),
    ("akm", "AKM", "7.62x39", 600),
    ("ak101", "AK-101", "5.56x45", 650),
    ("m4a1", "M4A1", "5.56x45", 800),
    ("hk416", "HK 416A5", "5.56x45", 850),
    ("fal", "SA-58", "7.62x51", 700),
    ("aug", "AUG A3", "5.56x45", 680),
    ("scar", "SCAR-H", "7.62x51", 600),
    ("avt", "AVT-40", "7.62x54R", 750),
    ("mutant", "Mk47 Mutant", "7.62x39", 650),
    ("mp5", "MP5", "9x19", 800),
    ("mp7", "MP7", "4.6x30", 950),
    ("mpx", "MPX", "9x19", 850),
    ("p90", "P90", "5.7x28", 900),
    ("vityaz", "PP-19-01", "9x19", 700),
    ("vector", "Vector .45", ".45 ACP", 1100),
    ("ash12", "ASh-12", "12.7x55", 650),
    ("vss", "VSS Vintorez", "9x39", 700),
    ("m9a3", "M9A3", "9x19", None),
    ("rem870", "M870", "12ga", None),
]

BURST_SHOTS = 8
TAIL_SECONDS = 1.0


def select_standard(index, prefix):
    cands, seen = [], set()
    for bank, names in index.items():
        if not isinstance(names, list):
            continue
        for name in names:
            low = name.lower()
            if not low.startswith(prefix) or name in seen or "close" not in low:
                continue
            if any(t in low for t in ("silenced", "distant", "far", "loop", "tail", "double")):
                continue
            seen.add(name)
            cands.append((bank, name))
    outdoor = sorted([c for c in cands if "outdoor" in c[1].lower()], key=lambda c: c[1])
    indoor = sorted([c for c in cands if "indoor" in c[1].lower()], key=lambda c: c[1])
    neutral = sorted(
        [c for c in cands if "indoor" not in c[1].lower() and "outdoor" not in c[1].lower()],
        key=lambda c: c[1],
    )
    chosen = outdoor[:6]
    if len(chosen) < 3:
        chosen = (outdoor + neutral + indoor)[:6]
    return chosen


def select_suppressed(index, prefix):
    cands, seen = [], set()
    for bank, names in index.items():
        if not isinstance(names, list):
            continue
        for name in names:
            low = name.lower()
            if not low.startswith(prefix) or name in seen or "close" not in low:
                continue
            if "silenced" not in low:
                continue
            if any(t in low for t in ("distant", "far", "loop", "tail")):
                continue
            seen.add(name)
            cands.append((bank, name))
    outdoor = sorted([c for c in cands if "outdoor" in c[1].lower()], key=lambda c: c[1])
    indoor = sorted([c for c in cands if "indoor" in c[1].lower()], key=lambda c: c[1])
    neutral = sorted(
        [c for c in cands if "indoor" not in c[1].lower() and "outdoor" not in c[1].lower()],
        key=lambda c: c[1],
    )
    return (outdoor + neutral + indoor)[:4]


def select_tail(index, prefix, silenced: bool):
    """Find the game's own loop_tail clip for the burst ending."""
    for want_sil in ([True] if silenced else [False, True]):
        for bank, names in index.items():
            if not isinstance(names, list):
                continue
            for name in names:
                low = name.lower()
                if not low.startswith(prefix) or "close" not in low:
                    continue
                if not low.endswith(("loop_tail", "loop_silenced_tail")):
                    continue
                if "outdoor" not in low:
                    continue
                has_sil = "silenced" in low
                if has_sil == want_sil:
                    return (bank, name)
    return None


def to_stereo(data: np.ndarray) -> np.ndarray:
    if data.shape[1] == 1:
        return np.repeat(data, 2, axis=1)
    return data[:, :2]


def build_burst(shots, tail, rpm: int):
    rate = shots[0][1]
    channels = 2
    interval = 60.0 / float(rpm)
    tail_data = to_stereo(tail[0]) if tail is not None else None
    if tail_data is not None:
        tail_rate = tail[1] if tail is not None else rate
        cap = int(TAIL_SECONDS * tail_rate)
        tail_data = tail_data[:cap].copy()
        fade = min(int(0.15 * tail_rate), len(tail_data))
        if fade > 0:
            tail_data[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]
    tail_rate = tail[1] if tail is not None else rate

    starts = [int(i * interval * rate) for i in range(len(shots))]
    body_end = starts[-1] + max(len(to_stereo(d)) for d, _ in shots)
    tail_len = len(tail_data) if tail_data is not None else 0
    total = body_end + tail_len + 1

    buf = np.zeros((total, channels), dtype=np.float32)
    for shot_index, start in enumerate(starts):
        data, _ = shots[shot_index % len(shots)]
        stereo = to_stereo(data)
        end = start + len(stereo)
        buf[start:end] += stereo

    if tail_data is not None:
        offset = int(len(shots) * interval * rate)
        end = offset + len(tail_data)
        if end > len(buf):
            buf = np.pad(buf, ((0, end - len(buf)), (0, 0)))
        buf[offset:end] += tail_data

    peak = float(np.abs(buf).max())
    if peak > 0:
        buf *= min(1.0, PEAK_CEILING / peak)
    return buf, rate


def encode_ogg(data: np.ndarray, rate: int, out_path: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "in.wav")
        sf.write(wav, data, rate, format="WAV", subtype="PCM_24")
        subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-i", wav,
             "-c:a", "libvorbis", "-q:a", VORBIS_QUALITY, out_path],
            check=True,
        )


def main() -> None:
    index = json.load(open(INDEX_JSON, encoding="utf-8"))
    os.makedirs(OUT_DIR, exist_ok=True)

    plan = {}
    for prefix, display, caliber, rpm in WEAPONS:
        standard = select_standard(index, prefix)
        suppressed = select_suppressed(index, prefix)
        plan[prefix] = {
            "display": display,
            "caliber": caliber,
            "rpm": rpm,
            "standard": standard,
            "suppressed": suppressed,
            "tail": select_tail(index, prefix, False) if rpm else None,
            "tail_sil": select_tail(index, prefix, True) if rpm else None,
        }

    needed = set()
    for entry in plan.values():
        for key in ("standard", "suppressed"):
            for bank, name in entry[key]:
                needed.add((bank, name))
        for key in ("tail", "tail_sil"):
            if entry[key]:
                needed.add(entry[key])

    by_bank = {}
    for bank, name in needed:
        by_bank.setdefault(bank, set()).add(name)

    clips = {}
    for bank, names in by_bank.items():
        env = UnityPy.load(os.path.join(BANKS_DIR, f"{bank}.bundle"))
        for obj in env.objects:
            if obj.type.name != "AudioClip":
                continue
            try:
                clip = obj.read()
            except Exception:  # noqa: BLE001
                continue
            name = getattr(clip, "m_Name", "") or ""
            if name in names and name not in clips:
                clips[name] = clip

    def decode(name):
        clip = clips.get(name)
        if clip is None:
            return None
        try:
            payload = next(iter(clip.samples.values()))
        except Exception:  # noqa: BLE001
            return None
        return sf.read(io.BytesIO(payload), dtype="float32", always_2d=True)

    manifest = []
    for prefix, display, caliber, rpm in WEAPONS:
        entry = plan[prefix]
        gun_dir = os.path.join(OUT_DIR, prefix)
        groups = []

        rendered = []
        for _, name in entry["standard"]:
            got = decode(name)
            if got:
                rendered.append(("standard", name, got[0], got[1]))
        for _, name in entry["suppressed"]:
            got = decode(name)
            if got:
                rendered.append(("suppressed", name, got[0], got[1]))

        rms_values = [float(np.sqrt((d**2).mean())) for _, _, d, _ in rendered if d.size]
        gain = 1.0
        if rms_values:
            gain = TARGET_RMS / max(float(np.median(rms_values)), 1e-6)
            peak = max(float(np.abs(d).max()) for _, _, d, _ in rendered)
            if peak * gain > PEAK_CEILING:
                gain = PEAK_CEILING / max(peak, 1e-6)

        for group_key, label in (("standard", "标准"), ("suppressed", "消音")):
            items = [r for r in rendered if r[0] == group_key]
            if not items:
                continue
            folder = os.path.join(gun_dir, group_key)
            os.makedirs(folder, exist_ok=True)
            files = []
            for index_in_group, (_, name, data, rate) in enumerate(items):
                scaled = np.clip(data * gain, -1.0, 1.0).astype(np.float32)
                out_name = f"{name}.ogg"
                encode_ogg(scaled, rate, os.path.join(folder, out_name))
                files.append(
                    {
                        "file": f"sounds/{prefix}/{group_key}/{out_name}",
                        "clip": name,
                        "duration": round(len(scaled) / rate, 3),
                    }
                )
            groups.append({"key": group_key, "label": label, "clips": files})

        # Automatic burst
        if rpm and entry["standard"]:
            shots = []
            for _, name in entry["standard"]:
                got = decode(name)
                if got:
                    shots.append((np.clip(got[0] * gain, -1.0, 1.0).astype(np.float32), got[1]))
            if shots:
                tail = decode(entry["tail"][1]) if entry["tail"] else None
                tail = (np.clip(tail[0] * gain, -1.0, 1.0).astype(np.float32), tail[1]) if tail else None
                burst, rate = build_burst(shots, tail, rpm)
                folder = os.path.join(gun_dir, "auto")
                os.makedirs(folder, exist_ok=True)
                out_name = f"{prefix}_auto_burst.ogg"
                encode_ogg(burst, rate, os.path.join(folder, out_name))
                groups.append(
                    {
                        "key": "auto",
                        "label": f"连发（{rpm} RPM）",
                        "clips": [
                            {
                                "file": f"sounds/{prefix}/auto/{out_name}",
                                "clip": f"{prefix}_auto_burst",
                                "duration": round(len(burst) / rate, 3),
                            }
                        ],
                    }
                )

        if groups:
            manifest.append(
                {"id": prefix, "name": display, "caliber": caliber, "groups": groups}
            )
            counts = {g["key"]: len(g["clips"]) for g in groups}
            print(f"{prefix:8s} {display:14s} {counts}", flush=True)

    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(f"done: guns={len(manifest)}", flush=True)


if __name__ == "__main__":
    main()
