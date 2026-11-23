"""Synthesised (royalty-free) audio for Amplifier Reels: a light beat bed + whoosh / pop / tick effects.
build_track(events, total, path): events = list of (seconds, "whoosh"|"pop"|"tick"|"riser").
"""
import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt

SR = 44100
rng = np.random.default_rng(7)


def _env(n, attack=0.005, decay=None):
    t = np.arange(n) / SR
    a = np.clip(t / attack, 0, 1)
    d = np.exp(-t / decay) if decay else 1
    return a * d


def kick():
    n = int(.35 * SR); t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 25)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .002, .12)


def hat():
    n = int(.05 * SR)
    x = sosfilt(butter(4, 7000, "hp", fs=SR, output="sos"), rng.standard_normal(n))
    return x * _env(n, .001, .012) * .5


def snap():
    n = int(.18 * SR)
    x = sosfilt(butter(2, [1200, 5000], "bp", fs=SR, output="sos"), rng.standard_normal(n))
    return x * _env(n, .001, .04) * .9


def bass(freq, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * freq * t) + .3 * np.sin(2 * np.pi * freq * 2 * t)
    return x * _env(n, .01, dur / 2.5) * .5


def whoosh():
    n = int(.55 * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); seg = 1024
    for i in range(0, n, seg):  # sweep a band-pass upward
        fc = 400 + 5000 * (i / n) ** 1.5
        sos = butter(2, [fc * .7, min(fc * 1.4, 20000)], "bp", fs=SR, output="sos")
        out[i:i + seg] = sosfilt(sos, noise[i:i + seg])
    env = np.sin(np.pi * np.clip(t / .55, 0, 1)) ** 2
    return out * env * 1.6


def pop():
    n = int(.12 * SR); t = np.arange(n) / SR
    f = 1100 * np.exp(-t * 18) + 300
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * _env(n, .001, .03) * .9


def tick():
    n = int(.04 * SR)
    x = sosfilt(butter(2, [2500, 6000], "bp", fs=SR, output="sos"), rng.standard_normal(n))
    return x * _env(n, .0005, .006) * .6


def riser():
    n = int(1.0 * SR); t = np.arange(n) / SR
    f = 200 + 900 * (t / 1.0) ** 2
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * .25
    noise = sosfilt(butter(2, 3000, "hp", fs=SR, output="sos"), rng.standard_normal(n)) * .25
    return (tone + noise) * (t / 1.0) ** 2


def soft_whoosh():
    n = int(.7 * SR); t = np.arange(n) / SR
    noise = rng.standard_normal(n)
    out = np.zeros(n); seg = 1024
    for i in range(0, n, seg):  # gentle low sweep, airy not harsh
        fc = 250 + 1800 * np.sin(np.pi / 2 * i / n)
        sos = butter(2, [fc * .6, fc * 1.3], "bp", fs=SR, output="sos")
        out[i:i + seg] = sosfilt(sos, noise[i:i + seg])
    out = sosfilt(butter(2, 3000, "lp", fs=SR, output="sos"), out)
    env = np.sin(np.pi * np.clip(t / .7, 0, 1)) ** 3
    return out * env


def pluck():
    n = int(.45 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 784 * t) + .35 * np.sin(2 * np.pi * 1568 * t) + .15 * np.sin(2 * np.pi * 2352 * t)
    return x * _env(n, .004, .09)


def soft_tick():
    n = int(.03 * SR)
    x = sosfilt(butter(2, [1500, 3500], "bp", fs=SR, output="sos"), rng.standard_normal(n))
    return x * _env(n, .001, .005)


def chime():
    n = int(1.6 * SR); t = np.arange(n) / SR
    x = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t / d)
            for f, a, d in [(1046.5, 1, .55), (1568, .5, .4), (2093, .25, .3), (523.25, .4, .7)])
    return x * np.clip(t / .006, 0, 1)


# Amplifier house style: decent and soft — no beat, gentle effects only.
FX = {"whoosh": (soft_whoosh, .22), "pop": (pluck, .16), "tick": (soft_tick, .06), "riser": (chime, .14)}


def _add(buf, sig, at, gain):
    i = int(at * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain


def build_track(events, total, path, bpm=104, beat_bed=False):
    n = int((total + .5) * SR)
    bed = np.zeros(n); fx = np.zeros(n)
    beat = 60 / bpm
    notes = [55.0, 55.0, 65.4, 49.0]  # A1 A1 C2 G1 pulse
    t, k = 0.0, 0
    while beat_bed and t < total:
        _add(bed, kick(), t, .9)
        _add(bed, hat(), t + beat / 2, .35)
        if k % 2 == 1: _add(bed, snap(), t, .35)
        if k % 2 == 0: _add(bed, bass(notes[(k // 2) % 4], beat * 1.8), t, .6)
        t += beat; k += 1
    for at, kind in events:
        fn, g = FX[kind]
        _add(fx, fn(), max(0, at), g)
    mix = bed * .45 + fx
    fade = int(.8 * SR); mix[-fade:] *= np.linspace(1, 0, fade)
    peak = np.abs(mix).max()
    if peak > .7: mix *= .7 / peak
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))
