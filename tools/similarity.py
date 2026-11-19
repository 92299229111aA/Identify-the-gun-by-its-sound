"""Measure acoustic similarity between guns to find shared recordings."""
import itertools
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")

POINTS = 96


def load(path):
    data, rate = sf.read(path, dtype="float32", always_2d=True)
    return data.mean(axis=1), rate


def envelope(mono, points=POINTS):
    win = max(1, len(mono) // points)
    frames = len(mono) // win
    env = np.abs(mono[: frames * win]).reshape(frames, win).max(axis=1)
    if len(env) != points:
        env = np.interp(np.linspace(0, len(env) - 1, points), np.arange(len(env)), env)
    env = env - env.mean()
    n = np.linalg.norm(env) or 1e-9
    return env / n


def spectrum(mono):
    spec = np.abs(np.fft.rfft(mono))
    bands = np.array_split(spec, 64)
    vec = np.log1p(np.array([b.mean() for b in bands]))
    vec = vec - vec.mean()
    n = np.linalg.norm(vec) or 1e-9
    return vec / n


def best_corr(a, b, shifts=(0, 1, 2, 4)):
    best = -1.0
    for s in shifts:
        if s == 0:
            best = max(best, float(np.dot(a, b)))
        else:
            best = max(best, float(np.dot(a[s:], b[:-s])), float(np.dot(a[:-s], b[s:])))
    return best


def main():
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    guns = {}
    for gun in manifest:
        standard = next((g for g in gun["groups"] if g["key"] == "standard"), None)
        if not standard:
            continue
        envs, specs = [], []
        for clip in standard["clips"][:3]:
            mono, rate = load(os.path.join(PROJECT, clip["file"].replace("/", os.sep)))
            envs.append(envelope(mono))
            specs.append(spectrum(mono))
        guns[gun["id"]] = {"name": gun["name"], "env": envs, "spec": specs}

    ids = list(guns)
    pairs = []
    for a, b in itertools.combinations(ids, 2):
        env_sim = max(best_corr(x, y) for x in guns[a]["env"] for y in guns[b]["env"])
        spec_sim = max(float(np.dot(x, y)) for x in guns[a]["spec"] for y in guns[b]["spec"])
        pairs.append((env_sim, spec_sim, a, b))
    pairs.sort(reverse=True)

    print(f"{'env':>6} {'spec':>6}  pair")
    for env_sim, spec_sim, a, b in pairs[:20]:
        print(f"{env_sim:6.3f} {spec_sim:6.3f}  {guns[a]['name']:16s} ~ {guns[b]['name']}")

    json.dump(
        [{"a": a, "b": b, "env": round(e, 4), "spec": round(s, 4)} for e, s, a, b in pairs[:200]],
        open(os.path.join(HERE, "similarity.json"), "w", encoding="utf-8"),
        ensure_ascii=False,
        indent=1,
    )


if __name__ == "__main__":
    main()
