"""Builds the SVG panels of the GitHub profile README (light and dark): a lab notebook for AI,
signal and image processing.

Every panel is a self-contained SVG: fonts are subset and embedded, screenshots are embedded,
so GitHub renders them exactly as designed. Run from the repo root:

    python3 tools/build_profile.py
"""
import base64
import io
import math
import random
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "assets"

THEMES = {
    "light": dict(bg="#F6F3EB", panel="#FFFDF8", grid="#E7E1D3", grid2="#DDD5C3", ink="#16181D",
                  muted="#5E6472", faint="#9AA0AC", accent="#C2410C", live="#15803D", shot_frame="#16181D", trace="#0F766E"),
    "dark": dict(bg="#0B0F17", panel="#111722", grid="#161E2B", grid2="#1E2838", ink="#E8EDF5",
                 muted="#8C97A8", faint="#5B6678", accent="#F59E5B", live="#4ADE80", shot_frame="#2A3446", trace="#2DD4BF"),
}

CHARS = "".join(chr(c) for c in range(32, 127)) + "·–—→↗×°ƒ"


def font_face(family, file, weight):
    """Subsets a woff2 font to the characters the panels use and returns an @font-face rule."""
    font = TTFont(TOOLS / "fonts" / file)
    opts = subset.Options()
    opts.flavor = "woff2"
    opts.layout_features = ["kern", "liga"]
    sub = subset.Subsetter(opts)
    sub.populate(text=CHARS)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    data = base64.b64encode(buf.getvalue()).decode()
    return f"@font-face{{font-family:'{family}';font-weight:{weight};src:url(data:font/woff2;base64,{data}) format('woff2');}}"


FACES = {
    ("s", 400): font_face("Plex", "ibm-plex-sans-latin-400-normal.woff2", 400),
    ("s", 500): font_face("Plex", "ibm-plex-sans-latin-500-normal.woff2", 500),
    ("s", 700): font_face("Plex", "ibm-plex-sans-latin-700-normal.woff2", 700),
    ("m", 400): font_face("PlexMono", "ibm-plex-mono-latin-400-normal.woff2", 400),
    ("m", 500): font_face("PlexMono", "ibm-plex-mono-latin-500-normal.woff2", 500),
}
FONTS = "".join(FACES.values())


def fonts_for(body):
    """Only the faces a panel uses: keeps each SVG small. Errs on including a face."""
    import re
    weights = {400} | {int(w) for w in re.findall(r'font-weight="(\d+)"', body)}
    used = {("s", w) for w in weights}
    if 'class="m' in body or "PlexMono" in body:
        used |= {("m", w) for w in weights if w in (400, 500)} | {("m", 400)}
    return "".join(FACES[k] for k in sorted(used) if k in FACES)

SANS = "font-family:Plex,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "font-family:PlexMono,SFMono-Regular,Consolas,monospace"


def embed_image(file, width, crop_ratio=None):
    im = Image.open(TOOLS / "screens" / file).convert("RGB")
    if crop_ratio:  # keep the top of tall screenshots
        h = int(im.width * crop_ratio)
        im = im.crop((0, 0, im.width, min(h, im.height)))
    im = im.resize((width, int(im.height * width / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=84, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode(), im.size


def svg(w, h, body, t, extra_css="", label="", background=True):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">
<style>{fonts_for(body)}
.s{{{SANS}}} .m{{{MONO}}} .ink{{fill:{t['ink']}}} .mu{{fill:{t['muted']}}} .fa{{fill:{t['faint']}}} .ac{{fill:{t['accent']}}}
{extra_css}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}} .rise,.grid,.fm{{opacity:1!important;transform:none!important}} .draw{{stroke-dashoffset:0!important}} .bar{{transform:none!important}} .noisy{{stroke-dashoffset:0!important;opacity:.28}} .kernel{{opacity:0!important}}}}
</style>
{f'<rect width="{w}" height="{h}" fill="{t["bg"]}"/>' if background else ""}
{body}
</svg>
"""


def grid(w, h, t, step=20):
    lines = []
    for x in range(0, w + 1, step):
        lines.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{h}" stroke="{t["grid2"] if x % 100 == 0 else t["grid"]}" stroke-width="{0.8 if x % 100 == 0 else 0.5}"/>')
    for y in range(0, h + 1, step):
        lines.append(f'<line x1="0" y1="{y}" x2="{w}" y2="{y}" stroke="{t["grid2"] if y % 100 == 0 else t["grid"]}" stroke-width="{0.8 if y % 100 == 0 else 0.5}"/>')
    return f'<g class="grid">{"".join(lines)}</g>'


def frame(w, h, t, inset=10):
    return (f'<rect x="{inset}" y="{inset}" width="{w-2*inset}" height="{h-2*inset}" fill="none" stroke="{t["ink"]}" stroke-width="2"/>'
            f'<rect x="{inset+7}" y="{inset+7}" width="{w-2*inset-14}" height="{h-2*inset-14}" fill="none" stroke="{t["ink"]}" stroke-width="0.6"/>')




# ---------------------------------------------------------------------------------------------
# 1. Hero: a noisy signal is drawn, then filtered; its spectrum rises; a kernel convolves an image.
# ---------------------------------------------------------------------------------------------

def _signal_paths(x0, y0, w, amp, n=240, seed=7):
    """A clean two-tone signal and the same signal with noise, as SVG path data."""
    rnd = random.Random(seed)
    clean, noisy = [], []
    for i in range(n + 1):
        u = i / n
        v = math.sin(2 * math.pi * 3 * u) * 0.75 + math.sin(2 * math.pi * 7 * u + 0.6) * 0.25
        x = x0 + u * w
        clean.append((x, y0 - v * amp))
        noisy.append((x, y0 - (v + rnd.gauss(0, 0.28)) * amp))
    to_d = lambda pts: "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
    return to_d(clean), to_d(noisy)


def hero(t):
    W, H = 1200, 470
    ink, acc, mu, tr = t["ink"], t["accent"], t["muted"], t["trace"]
    css = f"""
.grid{{opacity:0;animation:fade .8s ease-out forwards}}
.rise{{opacity:0;transform:translateY(10px);animation:rise .9s cubic-bezier(.2,.7,.2,1) forwards}}
.d1{{animation-delay:.2s}} .d2{{animation-delay:.45s}} .d3{{animation-delay:.7s}} .d4{{animation-delay:.95s}}
.draw{{stroke-dasharray:var(--l);stroke-dashoffset:var(--l);animation:draw var(--t,1.6s) ease-in-out forwards}}
.bar{{transform-box:fill-box;transform-origin:50% 100%;transform:scaleY(0);animation:grow .7s cubic-bezier(.2,.8,.2,1) forwards}}
.noisy{{animation:draw 1.6s .6s ease-in-out forwards, dim .6s 2.6s forwards}}
.kernel{{animation:scan 6s 3.2s steps(1) infinite;opacity:0}}
.fm{{opacity:0;animation:fade .25s forwards}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes dim{{to{{opacity:.28}}}}
@keyframes rise{{to{{opacity:1;transform:none}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes grow{{to{{transform:scaleY(1)}}}}
"""
    # --- Oscilloscope trace (top right) ---
    X, Y, PW = 650, 52, 500
    scope = [f'<rect x="{X}" y="{Y}" width="{PW}" height="150" fill="{t["panel"]}" stroke="{ink}" stroke-width="1.5" class="rise d1"/>']
    for k in range(1, 5):
        scope.append(f'<line x1="{X + k*PW/5}" y1="{Y}" x2="{X + k*PW/5}" y2="{Y+150}" stroke="{t["grid2"]}" stroke-width="0.8" stroke-dasharray="2 4" class="rise d1"/>')
    scope.append(f'<line x1="{X}" y1="{Y+75}" x2="{X+PW}" y2="{Y+75}" stroke="{t["grid2"]}" stroke-width="1" class="rise d1"/>')
    clean, noisy = _signal_paths(X + 10, Y + 75, PW - 20, 48)
    scope.append(f'<path d="{noisy}" fill="none" stroke="{mu}" stroke-width="1.4" class="noisy" style="stroke-dasharray:3200;stroke-dashoffset:3200"/>')
    scope.append(f'<path d="{clean}" fill="none" stroke="{tr}" stroke-width="2.6" stroke-linecap="round" class="draw" style="--l:1700;--t:1.5s;animation-delay:2.2s"/>')
    scope.append(f'''<g class="m rise d2" font-size="10.5" letter-spacing="1.2">
  <text x="{X+12}" y="{Y+18}" fill="{mu}">CH1  x[n] · RAW</text>
  <text x="{X+PW-12}" y="{Y+18}" text-anchor="end" fill="{tr}">y[n] = h * x · LOW-PASS</text>
</g>''')

    # --- Spectrum (bottom middle) ---
    SX, SY, SW, SH = 650, 230, 240, 150
    spec = [f'<rect x="{SX}" y="{SY}" width="{SW}" height="{SH}" fill="{t["panel"]}" stroke="{ink}" stroke-width="1.5" class="rise d2"/>']
    mags = [0.06, 0.1, 0.92, 0.18, 0.08, 0.12, 0.34, 0.1, 0.06, 0.05, 0.07, 0.04, 0.05, 0.03, 0.04, 0.03]
    bw = (SW - 24) / len(mags)
    for i, m in enumerate(mags):
        h = (SH - 40) * m
        col = acc if m > 0.3 else mu
        spec.append(f'<rect x="{SX + 12 + i*bw + 2:.1f}" y="{SY + SH - 14 - h:.1f}" width="{bw-4:.1f}" height="{h:.1f}" fill="{col}" class="bar" style="animation-delay:{1.2 + i*0.05:.2f}s"/>')
    spec.append(f'<line x1="{SX+12}" y1="{SY+SH-14}" x2="{SX+SW-12}" y2="{SY+SH-14}" stroke="{ink}" stroke-width="1"/>')
    spec.append(f'<text x="{SX+12}" y="{SY+18}" class="m rise d2" font-size="10.5" letter-spacing="1.2" fill="{mu}">|X(ƒ)| · FFT</text>')

    # --- Convolution (bottom right): a 3x3 kernel scans a 6x6 image; the feature map fills in. ---
    CX, CY, cell = 910, 230, 20
    conv = [f'<rect x="{CX}" y="{CY}" width="240" height="150" fill="{t["panel"]}" stroke="{ink}" stroke-width="1.5" class="rise d3"/>',
            f'<text x="{CX+12}" y="{CY+18}" class="m rise d3" font-size="10.5" letter-spacing="1.2" fill="{mu}">CONV 3×3</text>']
    ix, iy = CX + 14, CY + 28
    img = [[0.15, 0.2, 0.3, 0.75, 0.85, 0.9], [0.15, 0.25, 0.35, 0.8, 0.9, 0.85], [0.1, 0.2, 0.4, 0.85, 0.9, 0.9],
           [0.12, 0.22, 0.38, 0.78, 0.88, 0.92], [0.1, 0.18, 0.35, 0.8, 0.86, 0.9], [0.12, 0.2, 0.3, 0.75, 0.9, 0.88]]
    for r in range(6):
        for c in range(6):
            v = img[r][c]
            conv.append(f'<rect x="{ix + c*cell}" y="{iy + r*cell}" width="{cell-1.5}" height="{cell-1.5}" fill="{ink}" fill-opacity="{0.12 + 0.75*v:.2f}" class="rise d3"/>')
    # Kernel window: discrete positions, one per second-ish, looping.
    pos = [(0, 0), (1, 0), (2, 0), (3, 0), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (0, 3), (1, 3), (2, 3), (3, 3)]
    frames = len(pos)
    kf = "".join(f"{i*100/frames:.2f}%{{transform:translate({c*cell}px,{r*cell}px)}}" for i, (c, r) in enumerate(pos))
    css += f"@keyframes scan{{0%{{opacity:1}}{kf}100%{{opacity:1;transform:translate({3*cell}px,{3*cell}px)}}}}"
    conv.append(f'<rect x="{ix-2}" y="{iy-2}" width="{3*cell+2.5}" height="{3*cell+2.5}" fill="none" stroke="{acc}" stroke-width="2.4" class="kernel"/>')
    # Feature map: an edge response (strong in the middle columns).
    fx, fy = CX + 150, CY + 48
    conv.append(f'<text x="{fx}" y="{fy-8}" class="m rise d3" font-size="9.5" fill="{mu}">FEATURE MAP</text>')
    fmv = [[0.1, 0.6, 0.95, 0.4], [0.1, 0.65, 0.95, 0.35], [0.15, 0.7, 0.9, 0.4], [0.1, 0.6, 0.95, 0.45]]
    for i, (c, r) in enumerate(pos):
        conv.append(f'<rect x="{fx + c*18}" y="{fy + r*18}" width="16.5" height="16.5" fill="{acc}" fill-opacity="{0.12 + 0.85*fmv[r][c]:.2f}" class="fm" style="animation-delay:{3.2 + i*6/frames:.2f}s"/>')
    conv.append(f'<path d="M{CX+140} {CY+88} h6" stroke="{mu}" stroke-width="1.5" class="rise d3"/>')

    text = f'''
<g class="s">
  <text x="58" y="78" class="m mu rise d1" font-size="12" letter-spacing="2.5">LAB NOTEBOOK · AN-01</text>
  <text x="54" y="160" class="ink rise d1" font-size="72" font-weight="700" letter-spacing="-1">Ahmad Nayfeh</text>
  <rect x="58" y="184" width="72" height="5" fill="{acc}" class="rise d2"/>
  <text x="58" y="232" class="ink rise d2" font-size="28" font-weight="500">AI · Signal &amp; Image Processing</text>
  <text x="58" y="268" class="ac rise d2" font-size="20" font-weight="500">M.Sc. Electrical Engineering, KFUPM</text>
  <text x="58" y="316" class="mu rise d3" font-size="17.5">Deep learning for images and signals:</text>
  <text x="58" y="341" class="mu rise d3" font-size="17.5">medical image synthesis and segmentation,</text>
  <text x="58" y="366" class="mu rise d3" font-size="17.5">self-supervised vision, vibration diagnostics.</text>
</g>'''
    tb_y = H - 60
    cols = [(36, "LOCATION", "RIYADH, SA"), (230, "STUDY", "M.SC. EE · KFUPM"), (450, "THESIS", "COLOR FUNDUS → ANGIOGRAPHY"),
            (760, "FOCUS", "VISION · SIGNALS · SSL"), (980, "WEB", "AHMADNAYFEH.VERCEL.APP")]
    tb = [f'<line x1="17" y1="{tb_y}" x2="{W-17}" y2="{tb_y}" stroke="{ink}" stroke-width="0.8"/>']
    for i, (x, k, v) in enumerate(cols):
        if i:
            tb.append(f'<line x1="{x-18}" y1="{tb_y}" x2="{x-18}" y2="{H-17}" stroke="{ink}" stroke-width="0.6"/>')
        tb.append(f'<text x="{x}" y="{tb_y+17}" class="m" font-size="9.5" fill="{t["faint"]}" letter-spacing="1.5">{k}</text>')
        tb.append(f'<text x="{x}" y="{tb_y+36}" class="m" font-size="12" fill="{acc if k == "WEB" else ink}" letter-spacing="1">{v}</text>')
    body = grid(W, H, t) + frame(W, H, t) + text + "".join(scope + spec + conv) + f'<g class="rise d4">{"".join(tb)}</g>'
    return svg(W, H, body, t, css, "Ahmad Nayfeh: AI, signal and image processing")


# ---------------------------------------------------------------------------------------------
# 2. Section headers.
# ---------------------------------------------------------------------------------------------

def header(t, number, title, note):
    W, H = 1200, 76
    body = f'''
<line x1="0" y1="{H-14}" x2="{W}" y2="{H-14}" stroke="{t['ink']}" stroke-width="1.2"/>
<rect x="0" y="14" width="64" height="{H-28}" fill="{t['ink']}"/>
<text x="32" y="{H/2+7}" text-anchor="middle" class="m" font-size="18" font-weight="500" fill="{t['panel']}">{number}</text>
<text x="86" y="{H/2+10}" class="s ink" font-size="28" font-weight="700" letter-spacing="-0.3">{title}</text>
<text x="{W-4}" y="{H/2+6}" text-anchor="end" class="m fa" font-size="12" letter-spacing="2">{note}</text>'''
    return svg(W, H, body, t, "", title, background=False)


# ---------------------------------------------------------------------------------------------
# 3. Lab: one clickable tile per public experiment, each with a small drawn glyph.
# ---------------------------------------------------------------------------------------------

LAB = [
    dict(key="dip-lib", code="L-01", name="DIP-Lib", tag="IMAGE PROCESSING", glyph="hist",
         lines=["Eight classic image-processing tools", "in one interactive web app."]),
    dict(key="freq", code="L-02", name="Frequency Decomposition Explorer", tag="SIGNALS · FFT", glyph="bands",
         lines=["Split 1D or 2D signals into frequency", "bands with the FFT and rebuild them."]),
    dict(key="edge", code="L-03", name="Edge-Vision", tag="COMPUTER VISION", glyph="edge",
         lines=["Sobel, Laplacian, Canny and Scharr", "side by side, with live parameters."]),
    dict(key="adaptive", code="L-04", name="Adaptive filters for RL", tag="SIGNALS · RL", glyph="lms",
         lines=["LMS, NLMS, sign-error LMS and RLS-LSTD", "compared for grid pathfinding."]),
    dict(key="simclr", code="L-05", name="SimCLR augmentations", tag="SELF-SUPERVISED", glyph="views",
         lines=["How each augmentation shapes SimCLR", "on CIFAR-10 and STL-10."]),
    dict(key="wind", code="L-06", name="Wind power forecasting", tag="TIME SERIES", glyph="series",
         lines=["Direct LSTM against an LSTM to Random", "Forest pipeline; the direct model wins."]),
    dict(key="cnn-depth", code="L-07", name="CNN depth on MNIST", tag="DEEP LEARNING", glyph="layers",
         lines=["How depth trades accuracy against", "parameters in a CNN classifier."]),
    dict(key="rdd", code="L-08", name="Road damage dataset", tag="DATASETS", glyph="boxes",
         lines=["RDD2022 merged with pothole datasets,", "relabelled for detection training."]),
]


def _glyph(kind, x, y, t):
    a, ink, mu, tr = t["accent"], t["ink"], t["muted"], t["trace"]
    g = []
    if kind == "hist":
        for i, h in enumerate([10, 22, 40, 56, 44, 30, 18, 26, 12]):
            g.append(f'<rect x="{x + i*9}" y="{y+64-h}" width="7" height="{h}" fill="{a if i == 3 else mu}"/>')
    elif kind == "bands":
        for i, (h, c) in enumerate([(50, a), (34, a), (20, tr), (12, tr), (8, mu), (6, mu)]):
            g.append(f'<rect x="{x + i*13}" y="{y+64-h}" width="10" height="{h}" fill="{c}"/>')
    elif kind == "edge":
        for r in range(4):
            for c in range(4):
                v = 0.85 if c >= 2 else 0.2
                g.append(f'<rect x="{x + c*15}" y="{y + r*15}" width="13" height="13" fill="{ink}" fill-opacity="{v}"/>')
        g.append(f'<line x1="{x+29}" y1="{y-4}" x2="{x+29}" y2="{y+62}" stroke="{a}" stroke-width="3"/>')
    elif kind == "lms":
        pts = " L".join(f"{x + i*1.0:.1f} {y + 32 - 26*math.exp(-i/22)*math.cos(i/4):.1f}" for i in range(80))
        g.append(f'<path d="M{pts}" fill="none" stroke="{tr}" stroke-width="2"/>')
        g.append(f'<line x1="{x}" y1="{y+32}" x2="{x+80}" y2="{y+32}" stroke="{mu}" stroke-width="1" stroke-dasharray="3 3"/>')
    elif kind == "views":
        g.append(f'<rect x="{x}" y="{y+6}" width="34" height="34" fill="{a}" fill-opacity=".25" stroke="{a}" stroke-width="1.6" transform="rotate(-8 {x+17} {y+23})"/>')
        g.append(f'<rect x="{x+40}" y="{y+22}" width="34" height="34" fill="{tr}" fill-opacity=".25" stroke="{tr}" stroke-width="1.6" transform="rotate(10 {x+57} {y+39})"/>')
        g.append(f'<path d="M{x+30} {y+50} q14 10 22 -6" fill="none" stroke="{mu}" stroke-width="1.4"/>')
    elif kind == "series":
        pts = " L".join(f"{x + i*2:.1f} {y + 36 - 18*math.sin(i/5) - 6*math.sin(i/1.7):.1f}" for i in range(40))
        g.append(f'<path d="M{pts}" fill="none" stroke="{ink}" stroke-width="1.8"/>')
        pts2 = " L".join(f"{x + 60 + i*2:.1f} {y + 36 - 18*math.sin((i+30)/5):.1f}" for i in range(12))
        g.append(f'<path d="M{pts2}" fill="none" stroke="{a}" stroke-width="2" stroke-dasharray="4 3"/>')
    elif kind == "layers":
        for i in range(4):
            g.append(f'<rect x="{x + i*16}" y="{y + 8 + i*6}" width="12" height="{52 - i*12}" fill="{mu if i < 3 else a}"/>')
    elif kind == "boxes":
        g.append(f'<rect x="{x}" y="{y}" width="80" height="62" fill="{ink}" fill-opacity=".12"/>')
        g.append(f'<rect x="{x+8}" y="{y+10}" width="30" height="20" fill="none" stroke="{a}" stroke-width="2"/>')
        g.append(f'<rect x="{x+44}" y="{y+30}" width="28" height="24" fill="none" stroke="{tr}" stroke-width="2"/>')
    return "".join(g)


def lab_tile(t, item):
    W, H = 590, 150
    body = f'''
<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{t['panel']}" stroke="{t['ink']}" stroke-width="2"/>
<text x="28" y="36" class="m fa" font-size="11" letter-spacing="2">{item['code']}</text>
<text x="80" y="36" class="m ac" font-size="11" letter-spacing="1.5">{item['tag']}</text>
<text x="28" y="72" class="s ink" font-size="21" font-weight="700">{item['name']}</text>
<text x="28" y="100" class="s mu" font-size="14.5">{item['lines'][0]}</text>
<text x="28" y="121" class="s mu" font-size="14.5">{item['lines'][1]}</text>
<line x1="470" y1="18" x2="470" y2="{H-18}" stroke="{t['grid2']}" stroke-width="1"/>
{_glyph(item['glyph'], 488, 44, t)}
<text x="{W-22}" y="{H-18}" text-anchor="end" class="m ac" font-size="13">↗</text>'''
    return svg(W, H, body, t, "", item["name"], background=False)


# ---------------------------------------------------------------------------------------------
# 4. Apps: phone screenshots.
# ---------------------------------------------------------------------------------------------

PRODUCTS = [
    dict(key="shadhra", sheet="A-01", name="Shadhra", status="LIVE · WEB + GOOGLE PLAY",
         lines=["Photograph a book page; OCR and", "LLMs turn it into searchable quotes", "in Arabic or English."],
         tags=["OCR", "LLMs", "FastAPI", "React"], cta="shadhra.app", shot="shadhra.jpg", ratio=None),
    dict(key="khatwa", sheet="A-02", name="Khatwa", status="RELEASED · ANDROID",
         lines=["A walking app that plays like a game:", "quests, levels, streaks, and a phone", "lock until you walk."],
         tags=["Kotlin", "Compose", "Firebase", "OSM"], cta="Download", shot="khatwa.webp", ratio=None),
    dict(key="marathon", sheet="A-03", name="Reading Marathon", status="RELEASED · ANDROID",
         lines=["For reading groups: one shared book", "per challenge, a daily log, points,", "badges, analytics and PDF reports."],
         tags=["Kotlin", "Compose", "Firebase"], cta="Download", shot="marathon.png", ratio=2.05),
]


def product_card(t, p):
    W, H = 400, 640
    src, (iw, ih) = embed_image(p["shot"], 300, p["ratio"])
    sw = 196
    sh = min(int(ih * sw / iw), 380)
    px, py = (W - sw) // 2, 170
    tags_x = 32
    tag_svg = []
    for tag in p["tags"]:
        w = 14 + len(tag) * 7.6
        tag_svg.append(f'<rect x="{tags_x}" y="{H-96}" width="{w}" height="24" rx="12" fill="none" stroke="{t["faint"]}" stroke-width="1"/>'
                       f'<text x="{tags_x + w/2}" y="{H-79.5}" text-anchor="middle" class="m mu" font-size="11.5">{tag}</text>')
        tags_x += w + 8
    lines = "".join(f'<text x="32" y="{H-150 + i*20}" class="s mu" font-size="14.5">{l}</text>' for i, l in enumerate(p["lines"]))
    body = f'''
{grid(W, H, t)}
<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{t['panel']}" fill-opacity="0.82" stroke="{t['ink']}" stroke-width="2"/>
<text x="32" y="44" class="m fa" font-size="11" letter-spacing="2">{p['sheet']}</text>
<text x="{W-32}" y="44" text-anchor="end" class="m" font-size="11" letter-spacing="1.5" fill="{t['live']}">{p['status']}</text>
<text x="32" y="92" class="s ink" font-size="34" font-weight="700" letter-spacing="-0.5">{p['name']}</text>
<rect x="32" y="108" width="44" height="4" fill="{t['accent']}"/>
<clipPath id="c-{p['key']}"><rect x="{px}" y="{py}" width="{sw}" height="{sh}" rx="18"/></clipPath>
<rect x="{px-7}" y="{py-7}" width="{sw+14}" height="{sh+14}" rx="24" fill="{t['shot_frame']}"/>
<image href="{src}" x="{px}" y="{py}" width="{sw}" height="{int(ih*sw/iw)}" preserveAspectRatio="xMidYMin slice" clip-path="url(#c-{p['key']})"/>
<rect x="0" y="{H-176}" width="{W}" height="176" fill="{t['panel']}"/>
<line x1="0" y1="{H-176}" x2="{W}" y2="{H-176}" stroke="{t['ink']}" stroke-width="1"/>
<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="none" stroke="{t['ink']}" stroke-width="2"/>
{lines}
{''.join(tag_svg)}
<line x1="0" y1="{H-56}" x2="{W}" y2="{H-56}" stroke="{t['ink']}" stroke-width="0.6"/>
<text x="32" y="{H-24}" class="m ac" font-size="14" font-weight="500" letter-spacing="1">{p['cta']} →</text>'''
    return svg(W, H, body, t, "", p["name"])


# ---------------------------------------------------------------------------------------------
# 5. Stack.
# ---------------------------------------------------------------------------------------------

STACK = [
    ("01", "DEEP LEARNING", "PyTorch · Keras", "CNNs, U-Nets, GANs, self-supervised learning, distillation"),
    ("02", "VISION", "OpenCV · scikit-image", "Segmentation, image synthesis, edge and frequency analysis"),
    ("03", "SIGNALS", "NumPy · SciPy", "FFT, filtering, adaptive filters, vibration analysis"),
    ("04", "DATA", "Pandas · scikit-learn", "Pipelines, classical models, evaluation"),
    ("05", "LLM APPS", "LLM APIs · CrewAI", "OCR to structured text, multi-agent parsing"),
    ("06", "SHIPPING", "Streamlit · FastAPI · Kotlin", "Demos, APIs and native Android apps"),
]


def stack(t):
    W = 1200
    row = 44
    H = 64 + row * len(STACK) + 2
    cols = [32, 110, 300, 600]
    head = "".join(f'<text x="{c}" y="40" class="m fa" font-size="11" letter-spacing="2">{h}</text>'
                   for c, h in zip(cols, ["#", "AREA", "TOOLS", "USED FOR"]))
    rows = []
    for i, (n, area, tools, use) in enumerate(STACK):
        y = 64 + i * row
        if i % 2:
            rows.append(f'<rect x="2" y="{y}" width="{W-4}" height="{row}" fill="{t["grid"]}" fill-opacity="0.55"/>')
        rows.append(f'''<text x="{cols[0]}" y="{y+28}" class="m mu" font-size="13">{n}</text>
<text x="{cols[1]}" y="{y+28}" class="m ac" font-size="11.5" letter-spacing="1.5">{area}</text>
<text x="{cols[2]}" y="{y+28}" class="s ink" font-size="16" font-weight="500">{tools}</text>
<text x="{cols[3]}" y="{y+28}" class="s mu" font-size="15">{use}</text>''')
    lines = "".join(f'<line x1="{c-14}" y1="20" x2="{c-14}" y2="{H}" stroke="{t["ink"]}" stroke-width="0.5"/>' for c in cols[1:])
    body = f'''<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{t['panel']}" stroke="{t['ink']}" stroke-width="2"/>
{''.join(rows)}{head}<line x1="0" y1="64" x2="{W}" y2="64" stroke="{t['ink']}" stroke-width="1"/>{lines}'''
    return svg(W, H, body, t, "", "Stack")


def footer(t):
    W, H = 1200, 96
    cells = [("AUTHOR", "AHMAD NAYFEH"), ("AFFILIATION", "KFUPM"), ("PUBLIC ENTRIES", f"{len(LAB) + len(PRODUCTS)}"), ("UPDATED", "2026"), ("STATUS", "RUNNING")]
    cw = W / len(cells)
    parts = []
    for i, (k, v) in enumerate(cells):
        x = i * cw
        if i:
            parts.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{t["ink"]}" stroke-width="0.8"/>')
        color = t["live"] if k == "STATUS" else t["ink"]
        parts.append(f'<text x="{x+24}" y="36" class="m fa" font-size="10.5" letter-spacing="2">{k}</text>'
                     f'<text x="{x+24}" y="66" class="m" font-size="15" font-weight="500" letter-spacing="1.2" fill="{color}">{v}</text>')
    body = f'''<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{t['panel']}" stroke="{t['ink']}" stroke-width="2"/>{''.join(parts)}'''
    return svg(W, H, body, t, "", "Notebook footer")


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("*.svg"):
        if old.name != "avatar.svg":
            old.unlink()
    for name, t in THEMES.items():
        (OUT / f"hero-{name}.svg").write_text(hero(t))
        (OUT / f"h-lab-{name}.svg").write_text(header(t, "01", "Lab", "EXPERIMENTS AND TOOLS · OPEN SOURCE"))
        for item in LAB:
            (OUT / f"lab-{item['key']}-{name}.svg").write_text(lab_tile(t, item))
        (OUT / f"h-apps-{name}.svg").write_text(header(t, "02", "Apps", "SHIPPED · IN USE"))
        for p in PRODUCTS:
            (OUT / f"card-{p['key']}-{name}.svg").write_text(product_card(t, p))
        (OUT / f"h-stack-{name}.svg").write_text(header(t, "03", "Stack", "WHAT I WORK WITH"))
        (OUT / f"stack-{name}.svg").write_text(stack(t))
        (OUT / f"footer-{name}.svg").write_text(footer(t))
    total = sum(f.stat().st_size for f in OUT.glob("*.svg"))
    print(f"{len(list(OUT.glob('*.svg')))} panels, {total/1024:.0f} KB")


if __name__ == "__main__":
    main()


# ---------------------------------------------------------------------------------------------
# README: assembles the panels; each one switches with the viewer's light or dark theme.
# ---------------------------------------------------------------------------------------------

LAB_LINKS = {
    "dip-lib": "Digital-Image-Processing-Library", "freq": "Frequency-Decomposition-Explorer", "edge": "Edge-Vision",
    "adaptive": "RL-Adaptive-Filtering-Pathfinding", "simclr": "SimCLR-Augmentations-CIFAR10",
    "wind": "WindPowerForecasting-LSTM-RF", "cnn-depth": "MNIST-CNN-Layer-Analysis", "rdd": "Modified-RDD2022-Dataset",
}
APP_LINKS = {"shadhra": "https://shadhra.app", "khatwa": "https://ahmad-nayfeh.github.io/khatwa/",
             "marathon": "https://ahmad-nayfeh.github.io/marathon/"}


def pic(name, alt, width="100%"):
    return (f'<picture><source media="(prefers-color-scheme: dark)" srcset="assets/{name}-dark.svg">'
            f'<img src="assets/{name}-light.svg" width="{width}" alt="{alt}"></picture>')


def readme():
    gh = "https://github.com/Ahmad-Nayfeh/"
    lab_rows = []
    for i in range(0, len(LAB), 2):
        pair = LAB[i:i + 2]
        lab_rows.append('<p align="center">\n' + "\n".join(
            f'  <a href="{gh}{LAB_LINKS[x["key"]]}">{pic("lab-" + x["key"], x["name"], "49%")}</a>' for x in pair) + "\n</p>")
    apps = '<p align="center">\n' + "\n".join(
        f'  <a href="{APP_LINKS[p["key"]]}">{pic("card-" + p["key"], p["name"], "32%")}</a>' for p in PRODUCTS) + "\n</p>"
    return f'''<a href="https://ahmadnayfeh.vercel.app">{pic("hero", "Ahmad Nayfeh: AI, signal and image processing")}</a>

<p align="center">
  <a href="https://ahmadnayfeh.vercel.app"><b>Portfolio</b></a> &nbsp;·&nbsp;
  <a href="https://ahmadnayfeh.vercel.app/resume.pdf"><b>CV</b></a> &nbsp;·&nbsp;
  <a href="https://www.linkedin.com/in/ahmad-nayfeh2000/"><b>LinkedIn</b></a> &nbsp;·&nbsp;
  <a href="mailto:ahmadnayfeh2000@gmail.com"><b>Email</b></a>
</p>

<br>

{pic("h-lab", "Lab")}

{chr(10).join(lab_rows)}

<br>

{pic("h-apps", "Apps")}

{apps}

<br>

{pic("h-stack", "Stack")}

{pic("stack", "Stack")}

<br>

{pic("footer", "Notebook footer")}
'''


(ROOT / "README.md").write_text(readme())
