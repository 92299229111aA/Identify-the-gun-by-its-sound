"""Detect guns that literally share the same recording (envelope correlation)."""
import json
import os

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(HERE)
MANIFEST = os.path.join(PROJECT, "sounds", "manifest.json")


def envelope(path, points=200):
    data, rate = sf.read(path, dtype="float32", always_2d=True)
    mono = data.mean(axis=1)
    win = max(1, int(0.002 * rate))
    frames = len(mono) // win
    env = np.abs(mono[: frames * win]).reshape(frames, win).max(axis=1)
    if len(env) < points:
        env = np.interp(np.linspace(0, len(env) - 1, points), np.arange(len(env)), env)
    else:
        idx = np.linspace(0, len(env) - 1, points).astype(int)
        env = env[idx]
    env = env - env.mean()
    n = np.linalg.norm(env) or 1e-9
    return env / n


def best_corr(a, b, shifts=(0, 1, 2, 3, 5, 8)):
    best = -1.0
    for s in shifts:
        if s == 0:
            best = max(best, float(np.dot(a, b)))
        else:
            best = max(best, float(np.dot(a[s:], b[:-s])), float(np.dot(a[:-s], b[s:])))
    return best


def main():
    manifest = json.load(open(MANIFEST, encoding="utf-8"))
    envs = {}
    for gun in manifest:
        standard = next((g for g in gun["groups"] if g["key"] == "standard"), None)
        if not standard:
            continue
        vecs = []
        for clip in standard["clips"][:3]:
            path = os.path.join(PROJECT, clip["file"].replace("/", os.sep))
            vecs.append(envelope(path))
        envs[gun["id"]] = vecs

    ids = list(envs)
    pairs = []
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            best = max(best_corr(a, b) for a in envs[ids[i]] for b in envs[ids[j]])
            pairs.append((best, ids[i], ids[j]))
    pairs.sort(reverse=True)

    print("highest envelope correlations:")
    for score, a, b in pairs[:15]:
        print(f"  {score:.4f}  {a:10s} ~ {b}")

    dupes = [(a, b) for score, a, b in pairs if score > 0.97]
    json.dump(dupes, open(os.path.join(HERE, "duplicates.json"), "w", encoding="utf-8"), indent=1)
    print(f"\npairs > 0.97: {len(dupes)}")
    for a, b in dupes:
        print("  ", a, "~", b)


if __name__ == "__main__":
    main()
