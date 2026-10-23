"""Profile picture in the same lab-notebook style as the README panels.

An image made of pixels (a retina-like disc, a nod to the thesis), a convolution kernel on it,
and a filtered signal running across: images and signals in one mark. Writes assets/avatar.svg;
tools/render_avatar.js turns it into a 1024px PNG. Everything sits inside the central circle,
because GitHub crops avatars round.
"""
import math

from build_profile import FACES, THEMES, ROOT

t = THEMES["dark"]
S = 1024
C = S / 2
ink, acc, mu, tr = t["ink"], t["accent"], t["muted"], t["trace"]

grid = []
for i in range(0, S + 1, 32):
    major = i % 128 == 0
    col = t["grid2"] if major else t["grid"]
    w = 1.6 if major else 0.8
    grid.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{S}" stroke="{col}" stroke-width="{w}"/>')
    grid.append(f'<line x1="0" y1="{i}" x2="{S}" y2="{i}" stroke="{col}" stroke-width="{w}"/>')

# 11x11 pixel image: a bright disc with a darker centre and a few "vessels", inside a dark field.
N, cell, gap = 9, 66, 6
x0 = C - N * cell / 2
y0 = C - N * cell / 2
pix = []


def warm(v):
    """Fundus-like ramp: deep brown, through the accent orange, to pale amber."""
    stops = [(0.0, (58, 30, 16)), (0.5, (245, 158, 91)), (1.0, (255, 226, 190))]
    for (a, ca), (b, cb) in zip(stops, stops[1:]):
        if v <= b:
            k = (v - a) / (b - a)
            return "#%02x%02x%02x" % tuple(int(ca[i] + (cb[i] - ca[i]) * k) for i in range(3))
    return "#%02x%02x%02x" % stops[-1][1]
for r in range(N):
    for c in range(N):
        u, v = (c - (N - 1) / 2) / (N / 2), (r - (N - 1) / 2) / (N / 2)
        d = math.hypot(u, v)
        if d > 1.02:
            continue
        val = 0.85 * math.exp(-((d - 0.55) / 0.42) ** 2) + 0.15
        val -= 0.35 * math.exp(-((u + 0.25) ** 2 + (v + 0.1) ** 2) / 0.02)  # optic disc shadow
        vessel = math.exp(-((v - 0.35 * math.sin(u * 3)) / 0.08) ** 2) * 0.3
        val = max(0.08, min(1.0, val - vessel))
        pix.append(f'<rect x="{x0 + c*cell + gap/2:.1f}" y="{y0 + r*cell + gap/2:.1f}" width="{cell-gap}" height="{cell-gap}" rx="8" '
                   f'fill="{warm(val)}"/>')

# 3x3 kernel highlight on the upper right of the disc.
kc, kr = 5, 1
kernel = (f'<rect x="{x0 + kc*cell - 4}" y="{y0 + kr*cell - 4}" width="{3*cell + 8}" height="{3*cell + 8}" rx="10" '
          f'fill="none" stroke="{ink}" stroke-width="10"/>')

# Filtered signal crossing the whole circle.
pts = []
for i in range(161):
    u = i / 160
    x = C - 400 + 800 * u
    y = C + 40 - (math.sin(2 * math.pi * 2.2 * u) * 0.8 + math.sin(2 * math.pi * 5 * u + 0.5) * 0.2) * 95
    pts.append(f"{x:.1f} {y:.1f}")
wave = (f'<path d="M{" L".join(pts)}" fill="none" stroke="{t["bg"]}" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>'
        f'<path d="M{" L".join(pts)}" fill="none" stroke="{tr}" stroke-width="15" stroke-linecap="round" stroke-linejoin="round"/>')

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">
<style>{FACES[("m", 500)]}</style>
<defs>
  <radialGradient id="glow" cx="50%" cy="48%" r="60%">
    <stop offset="0" stop-color="{t['panel']}"/>
    <stop offset="1" stop-color="{t['bg']}"/>
  </radialGradient>
</defs>
<rect width="{S}" height="{S}" fill="url(#glow)"/>
<g opacity="0.9">{''.join(grid)}</g>
<circle cx="{C}" cy="{C}" r="440" fill="none" stroke="{ink}" stroke-width="2.5" opacity="0.5"/>
<circle cx="{C}" cy="{C}" r="426" fill="none" stroke="{ink}" stroke-width="1" opacity="0.3" stroke-dasharray="4 10"/>
{''.join(pix)}
{kernel}
{wave}
</svg>
'''
(ROOT / "assets" / "avatar.svg").write_text(svg)
print("assets/avatar.svg", round(len(svg) / 1024), "KB")
