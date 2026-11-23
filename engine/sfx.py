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


FX = {"whoosh": (whoosh, .55), "pop": (pop, .8), "tick": (tick, .5), "riser": (riser, .5)}


def _add(buf, sig, at, gain):
    i = int(at * SR)
    if i >= len(buf): return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[:j - i] * gain


def build_track(events, total, path, bpm=104):
    n = int((total + .5) * SR)
    bed = np.zeros(n); fx = np.zeros(n)
    beat = 60 / bpm
    notes = [55.0, 55.0, 65.4, 49.0]  # A1 A1 C2 G1 pulse
    t, k = 0.0, 0
    while t < total:
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
    mix /= max(1e-9, np.abs(mix).max()) / .89
    wavfile.write(path, SR, (mix * 32767).astype(np.int16))
