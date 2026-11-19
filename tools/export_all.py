"""Export the full weapon pool: standard / suppressed / auto variants.

Sources are both the per-weapon banks under StreamingAssets and the clips that
live in EscapeFromTarkov_Data/sharedassets*.assets. Read-only for the game dir.
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

GAME_DIR = r"D:\tkfben\EscapeFromTarkov_Data"
BANKS_DIR = os.path.join(
    GAME_DIR, r"StreamingAssets\Windows\assets\content\audio\banks"
)
HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
OUT_DIR = os.path.join(PROJECT, "sounds")
BANK_INDEX = os.path.join(HERE, "bank_names.json")
ASSET_INDEX = os.path.join(HERE, "audio_scan.json")

TARGET_RMS = 0.080
PEAK_CEILING = 0.700
VORBIS_QUALITY = "8"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()

# prefix, name, caliber, rpm, category, type label
WEAPONS = [
    ("ak74", "AK-74", "5.45x39", 650, "rifle", "突击步枪"),
    ("ak74m", "AK-74M", "5.45x39", 650, "rifle", "突击步枪"),
    ("ak101", "AK-101", "5.56x45", 650, "rifle", "突击步枪"),
    ("ak102", "AK-102", "5.56x45", 600, "rifle", "突击步枪"),
    ("akm", "AKM", "7.62x39", 600, "rifle", "突击步枪"),
    ("aksu", "AKS-74U", "5.45x39", 650, "rifle", "突击步枪"),
    ("avt", "AVT-40", "7.62x54R", 750, "rifle", "半自动步枪"),
    ("mutant", "Mk47 Mutant", "7.62x39", 650, "rifle", "突击步枪"),
    ("mdr", "MDR 5.56", "5.56x45", 700, "rifle", "突击步枪"),
    ("mdr308", "MDR 7.62", "7.62x51", 650, "rifle", "突击步枪"),
    ("mcx", "MCX .300", ".300 BLK", 700, "rifle", "突击步枪"),
    ("scar", "SCAR-H", "7.62x51", 600, "rifle", "战斗步枪"),
    ("fal", "SA-58", "7.62x51", 700, "rifle", "战斗步枪"),
    ("hk416", "HK 416A5", "5.56x45", 850, "rifle", "突击步枪"),
    ("m4a1", "M4A1", "5.56x45", 800, "rifle", "突击步枪"),
    ("aug", "AUG A3", "5.56x45", 680, "rifle", "突击步枪"),
    ("adar", "ADAR 2-15", "5.56x45", None, "rifle", "突击步枪"),
    ("tx15", "TX-15 DML", "5.56x45", None, "rifle", "精确射手步枪"),
    ("rfb", "RFB", "7.62x51", None, "rifle", "战斗步枪"),
    ("rsass", "RSASS", "7.62x51", None, "rifle", "精确射手步枪"),
    ("m1a", "M1A", "7.62x51", None, "rifle", "精确射手步枪"),
    ("sks", "SKS", "7.62x39", None, "rifle", "半自动步枪"),
    ("ash12", "ASh-12", "12.7x55", 650, "rifle", "突击步枪"),
    ("svd", "SVD-S", "7.62x54R", None, "sniper", "狙击步枪"),
    ("vss", "VSS Vintorez", "9x39", 700, "special", "特种步枪"),
    ("ppsh", "PPSh-41", "7.62x25", 900, "smg", "冲锋枪"),
    ("mp5", "MP5", "9x19", 800, "smg", "冲锋枪"),
    ("ump", "UMP .45", ".45 ACP", 600, "smg", "冲锋枪"),
    ("vector", "Vector .45", ".45 ACP", 1100, "smg", "冲锋枪"),
    ("vityaz", "PP-19-01", "9x19", 700, "smg", "冲锋枪"),
    ("mp7", "MP7", "4.6x30", 950, "smg", "冲锋枪"),
    ("mpx", "MPX", "9x19", 850, "smg", "冲锋枪"),
    ("mp9", "MP9", "9x19", 900, "smg", "冲锋枪"),
    ("p90", "P90", "5.7x28", 900, "smg", "冲锋枪"),
    ("kedr", "PP-91 Kedr", "9x18", 1000, "smg", "冲锋枪"),
    ("stm9", "STM-9", "9x19", None, "smg", "冲锋枪"),
    ("aps", "APS", "9x18", 900, "pistol", "机关手枪"),
    ("glock18", "Glock 18", "9x19", 1100, "pistol", "手枪"),
    ("pl", "PL-15", "9x19", None, "pistol", "手枪"),
    ("m9a3", "M9A3", "9x19", None, "pistol", "手枪"),
    ("1911", "M1911A1", ".45 ACP", None, "pistol", "手枪"),
    ("deagle", "Desert Eagle", ".50 AE", None, "pistol", "手枪"),
    ("fiveseven", "Five-seveN", "5.7x28", None, "pistol", "手枪"),
    ("rhino", "Chiappa Rhino", ".357", None, "pistol", "左轮手枪"),
    ("rsh", "RSh-12", "12.7x55", None, "pistol", "左轮手枪"),
    ("mosin", "Mosin", "7.62x54R", None, "sniper", "栓动步枪"),
    ("rem700", "M700", "7.62x51", None, "sniper", "栓动步枪"),
    ("t5000", "T-5000M", "7.62x51", None, "sniper", "栓动步枪"),
    ("vpo215", "VPO-215", ".366", None, "sniper", "栓动步枪"),
    ("mts255", "MTs-255", "12ga", None, "shotgun", "霰弹枪"),
    ("moss500", "Mossberg 500", "12ga", None, "shotgun", "霰弹枪"),
    ("m3", "Benelli M3", "12ga", None, "shotgun", "霰弹枪"),
    ("ks23", "KS-23", "23x75", None, "shotgun", "霰弹枪"),
    ("toz", "TOZ-106", "20ga", None, "shotgun", "霰弹枪"),
    ("rem870", "M870", "12ga", None, "shotgun", "霰弹枪"),
    ("utes", "UTS-15", "12ga", None, "shotgun", "霰弹枪"),
    ("rpk16", "RPK-16", "5.45x39", 650, "mg", "轻机枪"),
]

NOISE = ("amb", "water", "vent", "train", "test", "sparks", "shoreline", "shooting",
         "season", "seagulls", "rooftop", "prapor", "powerplant", "labyrinth", "lab",
         "illumination", "ib", "helicopter", "generator", "gas", "flare", "entity",
         "electricity", "electric", "eger", "duck", "coal", "clocks", "circle",
         "chain", "buy", "bunker", "btr", "broken", "blow", "beach", "alarm")


def load_indexes():
    bank = json.load(open(BANK_INDEX, encoding="utf-8"))
    assets = json.load(open(ASSET_INDEX, encoding="utf-8"))
    return bank, assets


def build_source_map(bank, assets):
    """clip name -> ("bank", bank_id) or ("assets", file)."""
    src = {}
    for bank_id, names in bank.items():
        if not isinstance(names, list):
            continue
        for name in names:
            src.setdefault(name, ("bank", bank_id))
    for file_name, clips in assets.items():
        for clip in clips:
            name = clip.get("name", "") if isinstance(clip, dict) else str(clip)
            if name and name not in src:
                src[name] = ("assets", file_name)
    return src


def close_filter(name, silenced=False):
    low = name.lower()
    if "close" not in low:
        return False
    if any(t in low for t in ("distant", "far", "loop", "tail", "double")):
        return False
    has_sil = "silenced" in low
    return has_sil if silenced else not has_sil


def gather(prefix, src, silenced):
    names = [n for n, (kind, _f) in src.items() if n.lower().startswith(prefix + "_") and close_filter(n, silenced)]
    outdoor = sorted([n for n in names if "outdoor" in n.lower()])
    neutral = sorted([n for n in names if "indoor" not in n.lower() and "outdoor" not in n.lower()])
    indoor = sorted([n for n in names if "indoor" in n.lower()])
    return (outdoor + neutral + indoor)


def gather_tail(prefix, src):
    cands = [
        n for n in src
        if n.lower().startswith(prefix + "_") and "outdoor" in n.lower() and n.lower().endswith(("loop_tail", "loop_silenced_tail"))
    ]
    return sorted(cands)


def to_stereo(data):
    return np.repeat(data, 2, axis=1) if data.shape[1] == 1 else data[:, :2]


def decode(entry, container, cache, assets_cache):
    name, (kind, file_name) = entry
    if kind == "bank":
        env = cache.get(file_name)
        if env is None:
            env = UnityPy.load(os.path.join(BANKS_DIR, f"{file_name}.bundle"))
            cache[file_name] = env
        wanted = name
    else:
        env = assets_cache.get(file_name)
        if env is None:
            env = UnityPy.load(os.path.join(GAME_DIR, file_name))
            assets_cache[file_name] = env
        wanted = name

    for obj in env.objects:
        if obj.type.name != "AudioClip":
            continue
        try:
            clip = obj.read()
        except Exception:
            continue
        if getattr(clip, "m_Name", "") != wanted:
            continue
        try:
            payload = next(iter(clip.samples.values()))
        except Exception:
            return None
        data, rate = sf.read(io.BytesIO(payload), dtype="float32", always_2d=True)
        return data, rate
    return None


def encode_ogg(data, rate, out_path):
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "in.wav")
        sf.write(wav, data, rate, format="WAV", subtype="PCM_24")
        subprocess.run(
            [FFMPEG, "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", VORBIS_QUALITY, out_path],
            check=True,
        )


def build_burst(shots, tail, rpm):
    rate = shots[0][1]
    interval = 60.0 / float(rpm)
    tail_data = to_stereo(tail[0]) if tail else None
    if tail_data is not None:
        cap = int(1.0 * tail[1])
        tail_data = tail_data[:cap].copy()
        fade = min(int(0.15 * tail[1]), len(tail_data))
        if fade > 0:
            tail_data[-fade:] *= np.linspace(1.0, 0.0, fade, dtype=np.float32)[:, None]

    starts = [int(i * interval * rate) for i in range(len(shots))]
    body_end = starts[-1] + max(len(to_stereo(d)) for d, _ in shots)
    total = body_end + (len(tail_data) if tail_data is not None else 0) + 1
    buf = np.zeros((total, 2), dtype=np.float32)
    for i, start in enumerate(starts):
        stereo = to_stereo(shots[i % len(shots)][0])
        buf[start:start + len(stereo)] += stereo
    if tail_data is not None:
        offset = int(len(shots) * interval * rate)
        buf[offset:offset + len(tail_data)] += tail_data
    peak = float(np.abs(buf).max())
    if peak > 0:
        buf *= min(1.0, PEAK_CEILING / peak)
    return buf, rate


def main():
    bank, assets = load_indexes()
    src = build_source_map(bank, assets)
    os.makedirs(OUT_DIR, exist_ok=True)

    bank_cache, assets_cache = {}, {}
    manifest = []
    skipped = []

    for prefix, display, caliber, rpm, category, kind in WEAPONS:
        standard = gather(prefix, src, silenced=False)[:6]
        suppressed = gather(prefix, src, silenced=True)[:4]
        if len(standard) < 2:
            skipped.append((prefix, len(standard), len(suppressed)))
            continue

        rendered = []
        for name in standard:
            got = decode((name, src[name]), None, bank_cache, assets_cache)
            if got:
                rendered.append(("standard", name, got[0], got[1]))
        for name in suppressed:
            got = decode((name, src[name]), None, bank_cache, assets_cache)
            if got:
                rendered.append(("suppressed", name, got[0], got[1]))
        if not rendered:
            skipped.append((prefix, 0, 0))
            continue

        rms = [float(np.sqrt((d ** 2).mean())) for _, _, d, _ in rendered if d.size]
        gain = 1.0
        if rms:
            gain = TARGET_RMS / max(float(np.median(rms)), 1e-6)
            peak = max(float(np.abs(d).max()) for _, _, d, _ in rendered)
            if peak * gain > PEAK_CEILING:
                gain = PEAK_CEILING / max(peak, 1e-6)

        gun_dir = os.path.join(OUT_DIR, prefix)
        groups = []
        for key, label in (("standard", "标准"), ("suppressed", "消音")):
            items = [r for r in rendered if r[0] == key]
            if not items:
                continue
            folder = os.path.join(gun_dir, key)
            os.makedirs(folder, exist_ok=True)
            files = []
            for _, name, data, rate in items:
                scaled = np.clip(data * gain, -1.0, 1.0).astype(np.float32)
                out_name = f"{name}.ogg"
                encode_ogg(scaled, rate, os.path.join(folder, out_name))
                files.append({"file": f"sounds/{prefix}/{key}/{out_name}", "clip": name, "duration": round(len(scaled) / rate, 3)})
            groups.append({"key": key, "label": label, "clips": files})

        if rpm:
            shots = [r for r in rendered if r[0] == "standard"][:6]
            if shots:
                tail_name = (gather_tail(prefix, src) or [None])[0]
                tail = decode((tail_name, src[tail_name]), None, bank_cache, assets_cache) if tail_name else None
                burst, rate = build_burst([(np.clip(d * gain, -1, 1).astype(np.float32), r) for _, _, d, r in shots], tail, rpm)
                folder = os.path.join(gun_dir, "auto")
                os.makedirs(folder, exist_ok=True)
                out_name = f"{prefix}_auto_burst.ogg"
                encode_ogg(burst, rate, os.path.join(folder, out_name))
                groups.append({"key": "auto", "label": f"连发（{rpm} RPM）", "clips": [{"file": f"sounds/{prefix}/auto/{out_name}", "clip": out_name[:-4], "duration": round(len(burst) / rate, 3)}]})

        manifest.append({
            "id": prefix, "name": display, "caliber": caliber, "type": kind,
            "category": category, "rpm": rpm, "groups": groups,
        })
        print(f"{prefix:10s} {display:16s} " + " ".join(f"{g['key']}={len(g['clips'])}" for g in groups), flush=True)

    manifest.sort(key=lambda g: (g["category"], g["name"]))
    with open(os.path.join(OUT_DIR, "manifest.json"), "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, ensure_ascii=False, indent=2)
    print(f"\ndone: guns={len(manifest)} clips={sum(len(g['clips']) for gun in manifest for g in gun['groups'])}")
    print("skipped:", skipped)


if __name__ == "__main__":
    main()
