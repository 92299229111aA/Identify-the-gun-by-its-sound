"""Compare guns by log-mel spectrogram cross-correlation (shared recordings score ~1)."""
import itertools
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")

SR = 22050
N_FFT = 1024
HOP = 256
N_MELS = 40
MAX_SHIFT = 12


def mel_filterbank(sr, n_fft, n_mels):
    def hz_to_mel(f):
        return 2595.0 * np.log10(1.0 + f / 700.0)

    def mel_to_hz(m):
        return 700.0 * (10 ** (m / 2595.0) - 1.0)

    low, high = hz_to_mel(50), hz_to_mel(sr / 2 - 100)
    mels = np.linspace(low, high, n_mels + 2)
    hz = mel_to_hz(mels)
    bins = np.floor((n_fft + 1) * hz / sr).astype(int)
    fb = np.zeros((n_mels, n_fft // 2 + 1))
    for i in range(n_mels):
        start, center, stop = bins[i], bins[i + 1], bins[i + 2]
        if center > start:
            fb[i, start:center] = (np.arange(start, center) - start) / (center - start)
        if stop > center:
            fb[i, center:stop] = (stop - np.arange(center, stop)) / (stop - center)
    return fb


FB = mel_filterbank(SR, N_FFT, N_MELS)


def spectrogram(mono):
    if len(mono) < N_FFT:
        mono = np.pad(mono, (0, N_FFT - len(mono)))
    frames = 1 + (len(mono) - N_FFT) // HOP
    window = np.hanning(N_FFT)
    out = np.empty((frames, N_MELS), dtype=np.float32)
    for i in range(frames):
        chunk = mono[i * HOP: i * HOP + N_FFT] * window
        spec = np.abs(np.fft.rfft(chunk))
        out[i] = np.log1p(FB @ spec)
    out = out - out.mean()
    n = np.linalg.norm(out) or 1e-9
    return out / n


def load_clips(gun_id, manifest):
    gun = next(g for g in manifest if g["id"] == gun_id)
    standard = next(g for g in gun["groups"] if g["key"] == "standard")
    specs = []
    for clip in standard["clips"][:4]:
        mono, rate = sf.read(os.path.join(PROJECT, clip["file"].replace("/", os.sep)), dtype="float32", always_2d=True)
        mono = mono.mean(axis=1)
        if rate != SR:
            idx = np.linspace(0, len(mono) - 1, int(len(mono) * SR / rate))
            mono = np.interp(idx, np.arange(len(mono)), mono)
        specs.append(spectrogram(mono))
    return specs


def compare(a, b):
    best = -1.0
    for x, y in itertools.product(a, b):
        if x.shape[0] > y.shape[0]:
            x, y = y, x
        for shift in range(0, MAX_SHIFT + 1):
            if shift == 0:
                xx, yy = x, y[: x.shape[0]]
            else:
                if x.shape[0] + shift > y.shape[0]:
                    continue
                xx, yy = x, y[shift: shift + x.shape[0]]
            score = float((xx * yy).sum())
            best = max(best, score)
    return best


def main():
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    ids = [g["id"] for g in manifest]
    names = {g["id"]: g["name"] for g in manifest}
    feats = {gid: load_clips(gid, manifest) for gid in ids}

    if len(sys.argv) > 1 and sys.argv[1] == "probe":
        probes = [("ak74", "ak102"), ("ak74", "ak74m"), ("ak101", "ak74m"), ("m4a1", "hk416"), ("mp5", "mp7"), ("ak102", "ak101")]
        for a, b in probes:
            print(f"{names[a]:14s} ~ {names[b]:14s}  {compare(feats[a], feats[b]):.4f}")
        return

    rows = []
    for a, b in itertools.combinations(ids, 2):
        rows.append((compare(feats[a], feats[b]), a, b))
    rows.sort(reverse=True)
    print(f"{'score':>6}  pair")
    for score, a, b in rows[:25]:
        print(f"{score:6.3f}  {names[a]:16s} ~ {names[b]}")
    json.dump(
        [{"a": a, "b": b, "score": round(s, 5)} for s, a, b in rows],
        open(os.path.join(HERE, "mel_similarity.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=1,
    )


if __name__ == "__main__":
    main()
