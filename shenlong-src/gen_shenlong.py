#!/usr/bin/env python3
"""Generates the Shenlong (Dragão Eterno) textures + item models into <out>/assets/poloito.

Pure stdlib (no PIL on the server). Every body part is modelled pointing along +Z (snout/front
toward +Z, back toward +Y) so the plugin can orient each segment with one forward/up basis.
Usage: gen_shenlong.py <pack-root>
"""
import json, os, random, struct, sys, zlib

def png(path, w, h, px):
    raw = b"".join(b"\x00" + bytes(c for p in px[y*w:(y+1)*w] for c in p) for y in range(h))
    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)
    data = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)) \
        + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(data)

def clamp(v): return max(0, min(255, int(v)))

def scales(base, dark, light, seed):
    rnd = random.Random(seed)
    px = []
    for y in range(16):
        for x in range(16):
            # Overlapping half-circle scale rows (offset every other row).
            row = y // 4
            cx = (x + (2 if row % 2 else 0)) % 4
            cy = y % 4
            edge = cy == 3 or (cy == 2 and cx in (0, 3))
            hi = cy == 0 and cx in (1, 2)
            c = dark if edge else (light if hi else base)
            n = rnd.randint(-8, 8)
            px.append((clamp(c[0] + n), clamp(c[1] + n), clamp(c[2] + n), 255))
    return px

def plates(base, line, seed):
    rnd = random.Random(seed)
    px = []
    for y in range(16):
        for x in range(16):
            c = line if y % 4 == 3 else base
            n = rnd.randint(-6, 6)
            px.append((clamp(c[0] + n), clamp(c[1] + n), clamp(c[2] + n), 255))
    return px

def flat(c, seed, noise=6):
    rnd = random.Random(seed)
    return [(clamp(c[0] + (n := rnd.randint(-noise, noise))), clamp(c[1] + n), clamp(c[2] + n), 255) for _ in range(256)]

def eye():
    px = []
    for y in range(16):
        for x in range(16):
            d = ((x - 7.5) ** 2 + (y - 7.5) ** 2) ** 0.5
            px.append((255, 230, 120, 255) if d < 3 else (220, 20, 20, 255))
    return px

def el(frm, to, tex, rot=None):
    e = {"from": frm, "to": to,
         "faces": {f: {"texture": "#" + tex} for f in ("north", "south", "east", "west", "up", "down")}}
    if rot: e["rotation"] = rot
    return e

def body_elements(core, belly_inset):
    lo, hi = core
    return [
        el([lo, lo, 0], [hi, hi, 16], "scales"),
        el([lo + belly_inset, lo - 0.6, 0.5], [hi - belly_inset, lo, 15.5], "belly"),
        el([7.25, hi, 3], [8.75, hi + 2.5, 9], "spine", {"angle": 22.5, "axis": "x", "origin": [8, hi, 6]}),
        el([7.25, hi, 10], [8.75, hi + 2, 15], "spine", {"angle": 22.5, "axis": "x", "origin": [8, hi, 12]}),
    ]

def model(elements, extra_tex=None):
    tex = {"particle": "poloito:item/shenlong_scales", "scales": "poloito:item/shenlong_scales",
           "belly": "poloito:item/shenlong_belly", "spine": "poloito:item/shenlong_mane"}
    tex.update(extra_tex or {})
    return {"textures": tex, "elements": elements}

def main(root):
    a = os.path.join(root, "assets", "poloito")
    for d in ("textures/item", "models/item", "items"):
        os.makedirs(os.path.join(a, d), exist_ok=True)
    t = os.path.join(a, "textures", "item")
    png(os.path.join(t, "shenlong_scales.png"), 16, 16, scales((46, 140, 62), (22, 82, 36), (110, 200, 110), 1))
    png(os.path.join(t, "shenlong_belly.png"), 16, 16, plates((222, 196, 92), (168, 138, 52), 2))
    png(os.path.join(t, "shenlong_mane.png"), 16, 16, flat((24, 92, 44), 3))
    png(os.path.join(t, "shenlong_horn.png"), 16, 16, flat((214, 190, 140), 4))
    png(os.path.join(t, "shenlong_whisker.png"), 16, 16, flat((240, 228, 190), 5, 4))
    png(os.path.join(t, "shenlong_eye.png"), 16, 16, eye())

    head = model([
        el([3, 3, 0], [13, 12, 9], "scales"),                 # skull
        el([4.5, 3, 9], [11.5, 9, 16], "scales"),             # upper snout
        el([5, 1.5, 7], [11, 3, 15], "belly"),                # lower jaw
        el([5.5, 9, 14], [7, 9.6, 15.5], "mane"),             # nostrils
        el([9, 9, 14], [10.5, 9.6, 15.5], "mane"),
        el([2.9, 8.5, 6], [3, 10.5, 8.5], "eye"),             # eyes (flush with the skull sides)
        el([13, 8.5, 6], [13.1, 10.5, 8.5], "eye"),
        el([4, 12, 0], [12, 14, 6], "mane"),                  # brow / mane ridge
        el([3, 6, -3], [13, 13, 0], "mane"),                  # mane flowing back
        el([4, 12, 0], [5.5, 18, 2], "horn", {"angle": -22.5, "axis": "x", "origin": [4.75, 12, 1]}),
        el([10.5, 12, 0], [12, 18, 2], "horn", {"angle": -22.5, "axis": "x", "origin": [11.25, 12, 1]}),
        el([-4, 6, 13], [4.5, 6.5, 13.5], "whisker", {"angle": -22.5, "axis": "z", "origin": [4.5, 6.25, 13.25]}),
        el([11.5, 6, 13], [20, 6.5, 13.5], "whisker", {"angle": 22.5, "axis": "z", "origin": [11.5, 6.25, 13.25]}),
    ], {"mane": "poloito:item/shenlong_mane", "horn": "poloito:item/shenlong_horn",
        "eye": "poloito:item/shenlong_eye", "whisker": "poloito:item/shenlong_whisker"})
    body = model(body_elements((3, 13), 1.5))
    tail = model([
        el([5, 5, 0], [11, 11, 16], "scales"),
        el([6, 4.4, 0.5], [10, 5, 15.5], "belly"),
        el([7.5, 11, 4], [8.5, 15, 16], "spine"),
        el([7.5, 1, 8], [8.5, 5, 16], "spine"),
    ])
    for name, m in (("shenlong_head", head), ("shenlong_body", body), ("shenlong_tail", tail)):
        json.dump(m, open(os.path.join(a, "models", "item", name + ".json"), "w"), indent=1)
        json.dump({"model": {"type": "minecraft:model", "model": "poloito:item/" + name}},
                  open(os.path.join(a, "items", name + ".json"), "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1])
