"""Derive a short, discriminating tone hint per gun from the exported clips.

Brightness = spectral centroid, tail = share of energy after 300 ms (a reverb
tail measure that survives the initial transient), weight = energy below 300 Hz.
Labels come from terciles inside the pool, so every hint actually distinguishes.
"""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")
OUT = os.path.join(HERE, "hints.json")


def features(path):
    data, rate = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if mono.size < 2048:
        return None

    frame, hop = 2048, 1024
    centroids, weights = [], []
    for start in range(0, len(mono) - frame, hop):
        chunk = mono[start:start + frame] * np.hanning(frame)
        spec = np.abs(np.fft.rfft(chunk))
        freqs = np.fft.rfftfreq(frame, 1.0 / rate)
        total = spec.sum()
        if total <= 1e-9:
            continue
        centroids.append(float((spec * freqs).sum() / total))
        weights.append(total)
    centroid = float(np.average(centroids, weights=weights)) if centroids else 0.0

    energy = mono ** 2
    total_e = float(energy.sum()) or 1e-9
    after = int(0.3 * rate)
    tail_ratio = float(energy[after:].sum()) / total_e if len(energy) > after else 0.0

    spec_full = np.abs(np.fft.rfft(mono))
    freqs_full = np.fft.rfftfreq(len(mono), 1.0 / rate)
    low_ratio = float((spec_full[freqs_full < 300] ** 2).sum()) / ((spec_full ** 2).sum() or 1e-9)

    return {"centroid": centroid, "tail": tail_ratio, "low": low_ratio}


def tertile_labels(values, low_label, mid_label, high_label):
    order = sorted(values.items(), key=lambda kv: kv[1])
    n = len(order)
    labels = {}
    for i, (key, _v) in enumerate(order):
        labels[key] = low_label if i < n / 3 else (high_label if i >= 2 * n / 3 else mid_label)
    return labels


def main():
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    feats = {}
    for gun in manifest:
        standard = next((g for g in gun["groups"] if g["key"] == "standard"), None)
        if not standard:
            continue
        rows = []
        for clip in standard["clips"][:3]:
            f = features(os.path.join(PROJECT, clip["file"].replace("/", os.sep)))
            if f:
                rows.append(f)
        if not rows:
            continue
        feats[gun["id"]] = {
            "name": gun["name"],
            "centroid": float(np.mean([r["centroid"] for r in rows])),
            "tail": float(np.mean([r["tail"] for r in rows])),
            "low": float(np.mean([r["low"] for r in rows])),
        }

    bright = tertile_labels({k: v["centroid"] for k, v in feats.items()}, "偏闷", "中频", "偏亮")
    tail = tertile_labels({k: v["tail"] for k, v in feats.items()}, "尾音短", "尾音中等", "尾音长")
    body = tertile_labels({k: v["low"] for k, v in feats.items()}, "低频薄", "低频适中", "低频厚")

    hints = {}
    for gid, f in feats.items():
        hints[gid] = {
            "hint": f"{bright[gid]} · {tail[gid]} · {body[gid]}",
            "centroid": round(f["centroid"]),
            "tail": round(f["tail"], 3),
            "low": round(f["low"], 2),
            "name": f["name"],
        }

    json.dump(hints, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("guns:", len(hints))
    for gid in list(hints)[:8]:
        print(gid, hints[gid]["centroid"], hints[gid]["tail"], hints[gid]["low"])
    from collections import Counter
    print("tail labels:", Counter(v["hint"].split(" · ")[1] for v in hints.values()))
    print("bright labels:", Counter(v["hint"].split(" · ")[0] for v in hints.values()))
    print("body labels:", Counter(v["hint"].split(" · ")[2] for v in hints.values()))


if __name__ == "__main__":
    main()
