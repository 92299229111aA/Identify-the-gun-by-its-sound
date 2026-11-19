"""Pairwise waveform correlation across all guns (FFT), to find shared recordings."""
import itertools
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")

SR = 16000
DUR = 1.4
MAX_LAG = int(0.05 * SR)


def load_segments(path):
    data, rate = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    if rate != SR:
        idx = np.linspace(0, len(mono) - 1, int(len(mono) * SR / rate))
        mono = np.interp(idx, np.arange(len(mono)), mono)
    mono = mono[: int(DUR * SR)]
    mono = mono - mono.mean()
    n = np.linalg.norm(mono) or 1e-9
    return (mono / n).astype(np.float32)


def max_norm_xcorr(a, b):
    n = len(a) + len(b)
    size = 1 << (n - 1).bit_length()
    fa = np.fft.rfft(a, size)
    fb = np.fft.rfft(b, size)
    corr = np.fft.irfft(fa * np.conj(fb), size)
    corr = np.concatenate((corr[-MAX_LAG:], corr[: MAX_LAG + 1]))
    return float(np.abs(corr).max())


def main():
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    names, segs = {}, {}
    for gun in manifest:
        standard = next((g for g in gun["groups"] if g["key"] == "standard"), None)
        if not standard:
            continue
        names[gun["id"]] = gun["name"]
        segs[gun["id"]] = [
            load_segments(os.path.join(PROJECT, c["file"].replace("/", os.sep)))
            for c in standard["clips"][:3]
        ]

    ids = list(segs)
    rows = []
    for a, b in itertools.combinations(ids, 2):
        best = max(max_norm_xcorr(x, y) for x in segs[a] for y in segs[b])
        rows.append((best, a, b))

    rows.sort(reverse=True)
    print(f"{'score':>6}  pair")
    for score, a, b in rows[:30]:
        print(f"{score:6.3f}  {names[a]:16s} ~ {names[b]}")

    json.dump(
        [{"a": a, "b": b, "score": round(float(s), 4)} for s, a, b in rows],
        open(os.path.join(HERE, "identical.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=1,
    )


if __name__ == "__main__":
    main()
