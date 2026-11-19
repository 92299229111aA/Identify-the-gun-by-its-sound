"""Build acoustic groups: identical recordings vs merely similar guns.

Fast 16 kHz screen over all pairs, then a full-rate verification of candidates.
Output: tools/sound_groups.json
"""
import itertools
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")
OUT = os.path.join(HERE, "sound_groups.json")

IDENTICAL = 0.95
SIMILAR = 0.78
SCREEN = 0.75


def load(path, sr=None, dur=None):
    data, rate = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if sr and rate != sr:
        idx = np.linspace(0, len(mono) - 1, int(len(mono) * sr / rate))
        mono = np.interp(idx, np.arange(len(mono)), mono)
        rate = sr
    if dur:
        mono = mono[: int(dur * rate)]
    mono = mono - mono.mean()
    n = np.linalg.norm(mono) or 1e-9
    return (mono / n).astype(np.float32)


def xcorr(a, b, max_lag):
    size = 1 << (len(a) + len(b) - 1).bit_length()
    fa = np.fft.rfft(a, size)
    fb = np.fft.rfft(b, size)
    corr = np.fft.irfft(fa * np.conj(fb), size)
    corr = np.concatenate((corr[-max_lag:], corr[: max_lag + 1]))
    return float(np.abs(corr).max())


def main():
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    names, coarse, fine = {}, {}, {}
    for gun in manifest:
        standard = next((g for g in gun["groups"] if g["key"] == "standard"), None)
        if not standard:
            continue
        names[gun["id"]] = gun["name"]
        coarse[gun["id"]] = [
            load(os.path.join(PROJECT, c["file"].replace("/", os.sep)), sr=16000, dur=1.4)
            for c in standard["clips"][:3]
        ]

    ids = list(coarse)
    candidates = []
    for a, b in itertools.combinations(ids, 2):
        score = max(xcorr(x, y, int(0.05 * 16000)) for x in coarse[a] for y in coarse[b])
        if score >= SCREEN:
            candidates.append((score, a, b))
    print(f"screen candidates: {len(candidates)}")

    for gun in manifest:
        if gun["id"] in names:
            standard = next(g for g in gun["groups"] if g["key"] == "standard")
            fine[gun["id"]] = [
                load(os.path.join(PROJECT, c["file"].replace("/", os.sep)), dur=1.4)
                for c in standard["clips"][:3]
            ]

    verified = []
    for score, a, b in candidates:
        full = max(xcorr(x, y, int(0.05 * 44100)) for x in fine[a] for y in fine[b])
        verified.append((full, a, b))
    verified.sort(reverse=True)

    parent = {gid: gid for gid in names}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x, y):
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    identical_pairs, similar_pairs = [], []
    for score, a, b in verified:
        if score >= IDENTICAL:
            union(a, b)
            identical_pairs.append((round(score, 3), names[a], names[b]))
        elif score >= SIMILAR:
            similar_pairs.append((round(score, 3), a, b))

    groups = {}
    for gid in names:
        groups.setdefault(find(gid), []).append(gid)
    group_list = [sorted(v) for v in groups.values()]

    print("\nidentical recordings:")
    for score, a, b in identical_pairs:
        print(f"  {score:.3f}  {a:16s} ~ {b}")
    print("\nsimilar (not identical):")
    for score, a, b in similar_pairs[:12]:
        print(f"  {score:.3f}  {names[a]:16s} ~ {names[b]}")

    data = {
        "identicalThreshold": IDENTICAL,
        "similarThreshold": SIMILAR,
        "groups": [{"id": f"g{i+1}", "members": members} for i, members in enumerate(group_list) if len(members) > 1],
        "similarPairs": [{"a": a, "b": b, "score": s} for s, a, b in similar_pairs],
        "verified": [{"a": a, "b": b, "score": round(s, 4)} for s, a, b in verified],
    }
    json.dump(data, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\ngroups with >1 member: {len(data['groups'])}  similar pairs: {len(data['similarPairs'])}")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
