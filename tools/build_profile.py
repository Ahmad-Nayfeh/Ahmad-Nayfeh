"""Builds the SVG panels of the GitHub profile README (light and dark).

Every panel is a self-contained SVG: fonts are subset and embedded, screenshots are embedded,
so GitHub renders them exactly as designed. Run from the repo root:

    python3 tools/build_profile.py
"""
import base64
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
TOOLS = ROOT / "tools"
OUT = ROOT / "assets"

THEMES = {
    "light": dict(bg="#F6F3EB", panel="#FFFDF8", grid="#E7E1D3", grid2="#DDD5C3", ink="#16181D",
                  muted="#5E6472", faint="#9AA0AC", accent="#C2410C", live="#15803D", shot_frame="#16181D"),
    "dark": dict(bg="#0B0F17", panel="#111722", grid="#161E2B", grid2="#1E2838", ink="#E8EDF5",
                 muted="#8C97A8", faint="#5B6678", accent="#F59E5B", live="#4ADE80", shot_frame="#2A3446"),
}

CHARS = "".join(chr(c) for c in range(32, 127)) + "·–—→↗×°"


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


FONTS = "".join([
    font_face("Plex", "ibm-plex-sans-latin-400-normal.woff2", 400),
    font_face("Plex", "ibm-plex-sans-latin-500-normal.woff2", 500),
    font_face("Plex", "ibm-plex-sans-latin-700-normal.woff2", 700),
    font_face("PlexMono", "ibm-plex-mono-latin-400-normal.woff2", 400),
    font_face("PlexMono", "ibm-plex-mono-latin-500-normal.woff2", 500),
])

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
<style>{FONTS}
.s{{{SANS}}} .m{{{MONO}}} .ink{{fill:{t['ink']}}} .mu{{fill:{t['muted']}}} .fa{{fill:{t['faint']}}} .ac{{fill:{t['accent']}}}
{extra_css}
@media (prefers-reduced-motion: reduce){{*{{animation:none!important}} .rise,.grid,.flow,.state{{opacity:1!important;transform:none!important}} .draw{{stroke-dashoffset:0!important}} .blade{{transform:none!important}} .off{{opacity:0!important}} .lamp{{fill:{t['live']}!important}}}}
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
# 1. Hero: the single-line diagram draws itself, the breaker closes, current flows to the loads.
# ---------------------------------------------------------------------------------------------

def hero(t):
    W, H = 1200, 470
    ink, acc, mu = t["ink"], t["accent"], t["muted"]
    css = f"""
.grid{{opacity:0;animation:fade .8s ease-out forwards}}
.rise{{opacity:0;transform:translateY(10px);animation:rise .9s cubic-bezier(.2,.7,.2,1) forwards}}
.d1{{animation-delay:.2s}} .d2{{animation-delay:.45s}} .d3{{animation-delay:.7s}} .d4{{animation-delay:.95s}}
.draw{{stroke-dasharray:var(--l);stroke-dashoffset:var(--l);animation:draw 1.4s ease-in-out forwards}}
.blade{{transform-box:fill-box;transform-origin:0% 0%;transform:rotate(-38deg);animation:close .35s cubic-bezier(.5,0,.3,1.4) forwards}}
.flow{{opacity:0;animation:fade .3s 3.4s forwards}}
.lamp{{fill:{t['panel']};animation:lamp .4s 3.3s forwards}}
.state{{opacity:0;animation:fade .3s 3.35s forwards}}
.off{{animation:out .2s 3.3s forwards}}
@keyframes fade{{to{{opacity:1}}}}
@keyframes out{{to{{opacity:0}}}}
@keyframes rise{{to{{opacity:1;transform:none}}}}
@keyframes draw{{to{{stroke-dashoffset:0}}}}
@keyframes close{{to{{transform:rotate(0deg)}}}}
@keyframes lamp{{to{{fill:{t['live']}}}}}
"""
    # Diagram geometry (right half).
    X = 760
    feeder = f'M{X+190} 40 V96'
    tx = f'<circle cx="{X+190}" cy="112" r="16"/><circle cx="{X+190}" cy="134" r="16"/>'
    after_tx = f'M{X+190} 150 V176'
    bus = f'M{X+20} 238 H{X+380}'
    outs = [X + 70, X + 190, X + 310]
    parts = []

    def path(d, length, delay, width=2, color=ink, extra=""):
        parts.append(f'<path d="{d}" class="draw" style="--l:{length};animation-delay:{delay}s" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" {extra}/>')

    path(feeder, 60, 0.6)
    parts.append(f'<g fill="none" stroke="{ink}" stroke-width="2" class="rise d2">{tx}</g>')
    path(after_tx, 30, 1.2)
    # Circuit breaker: box with a blade that closes.
    parts.append(f'<rect x="{X+178}" y="176" width="24" height="24" fill="{t["panel"]}" stroke="{ink}" stroke-width="2" class="rise d3"/>')
    path(f'M{X+190} 200 V238', 40, 1.4)
    path(bus, 362, 1.6, width=5)
    for i, x in enumerate(outs):
        d0 = 1.9 + i * 0.15
        path(f'M{x} 238 V266', 30, d0, color=acc)
        # Load-break switch blade: pivots at the top contact, closes at ~3s.
        parts.append(f'<line x1="{x}" y1="266" x2="{x}" y2="300" stroke="{acc}" stroke-width="2.4" stroke-linecap="round" class="blade" style="animation-delay:{2.7 + i * 0.12}s"/>')
        parts.append(f'<circle cx="{x}" cy="266" r="3" fill="{acc}"/>')
        path(f'M{x} 300 V344', 46, d0 + 0.3, color=acc)
        parts.append(f'<path d="M{x-9} 344 H{x+9} L{x} 360 Z" fill="none" stroke="{acc}" stroke-width="2" class="rise" style="animation-delay:{d0+0.6}s"/>')
        # Current: dots running down each feeder once energized.
        parts.append(
            f'<g class="flow"><circle r="3" fill="{acc}"><animateMotion dur="1.6s" begin="{3.4 + i*0.2}s" repeatCount="indefinite" '
            f'path="M{x} 238 V344"/></circle><circle r="3" fill="{acc}"><animateMotion dur="1.6s" begin="{4.2 + i*0.2}s" repeatCount="indefinite" path="M{x} 238 V344"/></circle></g>')
    parts.append(f'<g class="flow"><circle r="3" fill="{ink}"><animateMotion dur="2.4s" begin="3.4s" repeatCount="indefinite" path="M{X+190} 40 V96"/></circle></g>')

    labels = f'''
<g class="m" font-size="11" fill="{mu}" letter-spacing="1">
  <text x="{X+216}" y="118" class="rise d3">TX-01</text><text x="{X+216}" y="132" class="rise d3">13.8/0.4 kV</text>
  <text x="{X+212}" y="193" class="rise d3">CB-01</text>
  <text x="{X+330}" y="230" class="rise d4">BUS A</text>
  <text x="{outs[0]-20}" y="384" class="rise d4">LBS-1</text><text x="{outs[1]-20}" y="384" class="rise d4">LBS-2</text><text x="{outs[2]-20}" y="384" class="rise d4">LBS-3</text>
</g>
<g class="m" font-size="11" letter-spacing="1.5">
  <circle cx="{X+30}" cy="62" r="6" class="lamp" stroke="{ink}" stroke-width="1.2"/>
  <text x="{X+44}" y="66" fill="{mu}" class="off">DE-ENERGIZED</text>
  <text x="{X+44}" y="66" fill="{t['live']}" class="state">ENERGIZED</text>
</g>'''

    text = f'''
<g class="s">
  <text x="58" y="78" class="m mu rise d1" font-size="12" letter-spacing="2.5">DRAWING NO. AN-0001 · PROFILE</text>
  <text x="54" y="160" class="ink rise d1" font-size="72" font-weight="700" letter-spacing="-1">Ahmad Nayfeh</text>
  <rect x="58" y="184" width="72" height="5" fill="{acc}" class="rise d2"/>
  <text x="58" y="232" class="ink rise d2" font-size="28" font-weight="500">Electrical Design Engineer</text>
  <text x="58" y="268" class="ac rise d2" font-size="28" font-weight="500">+ AI Automation</text>
  <text x="58" y="318" class="mu rise d3" font-size="18">I design medium-voltage switchgear,</text>
  <text x="58" y="344" class="mu rise d3" font-size="18">and I build the software that removes</text>
  <text x="58" y="370" class="mu rise d3" font-size="18">the repetitive work around it.</text>
</g>'''
    tb_y = H - 60
    title_block = f'''
<g class="rise d4">
  <line x1="17" y1="{tb_y}" x2="{W-17}" y2="{tb_y}" stroke="{ink}" stroke-width="0.8"/>
  <g stroke="{ink}" stroke-width="0.6"><line x1="250" y1="{tb_y}" x2="250" y2="{H-17}"/><line x1="470" y1="{tb_y}" x2="470" y2="{H-17}"/><line x1="660" y1="{tb_y}" x2="660" y2="{H-17}"/><line x1="900" y1="{tb_y}" x2="900" y2="{H-17}"/></g>
  <g class="m" font-size="9.5" fill="{t['faint']}" letter-spacing="1.5">
    <text x="36" y="{tb_y+17}">LOCATION</text><text x="268" y="{tb_y+17}">EMPLOYER</text><text x="488" y="{tb_y+17}">STUDY</text><text x="678" y="{tb_y+17}">FOCUS</text><text x="918" y="{tb_y+17}">WEB</text>
  </g>
  <g class="m" font-size="12.5" fill="{ink}" letter-spacing="1">
    <text x="36" y="{tb_y+36}">RIYADH, SA</text><text x="268" y="{tb_y+36}">ALFANAR · MV SWITCHGEAR</text><text x="488" y="{tb_y+36}">M.SC. EE · KFUPM</text><text x="678" y="{tb_y+36}">DESIGN + AUTOMATION</text>
    <text x="918" y="{tb_y+36}" fill="{acc}">AHMADNAYFEH.VERCEL.APP</text>
  </g>
</g>'''
    body = grid(W, H, t) + frame(W, H, t) + text + "".join(parts) + labels + title_block
    return svg(W, H, body, t, css, "Ahmad Nayfeh, Electrical Design Engineer and AI Automation")


# ---------------------------------------------------------------------------------------------
# 2. Section headers: a numbered sheet tab.
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
# 3. Product cards: phone screenshot on a drawing sheet.
# ---------------------------------------------------------------------------------------------

PRODUCTS = [
    dict(key="shadhra", sheet="P-01", name="Shadhra", status="LIVE · WEB + GOOGLE PLAY",
         lines=["Save quotes from printed books:", "photograph a page, extract Arabic", "or English text, resurface it daily."],
         tags=["FastAPI", "React", "Expo", "OCR"], cta="shadhra.app", shot="shadhra.jpg", ratio=None),
    dict(key="khatwa", sheet="P-02", name="Khatwa", status="RELEASED · ANDROID",
         lines=["A walking app that plays like a game:", "quests, levels, streaks, and a phone", "lock until you walk."],
         tags=["Kotlin", "Compose", "Firebase", "OSM"], cta="Download", shot="khatwa.webp", ratio=None),
    dict(key="marathon", sheet="P-03", name="Reading Marathon", status="RELEASED · ANDROID",
         lines=["For reading groups: one shared book", "per challenge, a daily log, points,", "badges, analytics and PDF reports."],
         tags=["Kotlin", "Compose", "Firebase"], cta="Download", shot="marathon.png", ratio=2.05),
]


def product_card(t, p):
    W, H = 400, 640
    src, (iw, ih) = embed_image(p["shot"], 300, p["ratio"])
    sw = 196
    sh = int(ih * sw / iw)
    sh = min(sh, 380)
    px, py = (W - sw) // 2, 170
    tags_x = 32
    tag_svg = []
    for tag in p["tags"]:
        w = 14 + len(tag) * 7.6
        tag_svg.append(f'<rect x="{tags_x}" y="{H-96}" width="{w}" height="24" rx="12" fill="none" stroke="{t["faint"]}" stroke-width="1"/>'
                       f'<text x="{tags_x + w/2}" y="{H-79.5}" text-anchor="middle" class="m mu" font-size="11.5">{tag}</text>')
        tags_x += w + 8
    lines = "".join(f'<text x="32" y="{H-150 + i*20}" class="s mu" font-size="14.5">{l}</text>' for i, l in enumerate(p["lines"][:2]))
    lines += f'<text x="32" y="{H-150 + 2*20}" class="s mu" font-size="14.5">{p["lines"][2]}</text>' if len(p["lines"]) > 2 else ""
    body = f'''
{grid(W, H, t)}
<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{t['panel']}" fill-opacity="0.82" stroke="{t['ink']}" stroke-width="2"/>
<text x="32" y="44" class="m fa" font-size="11" letter-spacing="2">SHEET {p['sheet']}</text>
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
# 4. Research: three result blocks with the honest headline number.
# ---------------------------------------------------------------------------------------------

RESEARCH = [
    dict(code="R-01", big="25", unit="experiments", title="Distill-SSL",
         lines=["SimCLR, BYOL and DINO teachers", "distilled into a MobileNetV3-Small", "student on STL-10."]),
    dict(code="R-02", big="0.963", unit="Dice", title="MRI tumor segmentation",
         lines=["U-Net with a pretrained ResNet34", "encoder on BraTS-Africa. Slice-level", "split: an optimistic estimate."]),
    dict(code="R-03", big="25%", unit="noise, still holds", title="Bearing fault diagnosis",
         lines=["1D CNN on raw CWRU vibration,", "tested on an unseen motor load.", "Fails past 50% noise."]),
]


def research(t):
    W, H = 1200, 300
    cw = W / 3
    cells = []
    for i, r in enumerate(RESEARCH):
        x = i * cw
        cells.append(f'''
<g transform="translate({x},0)">
  <text x="32" y="44" class="m fa" font-size="11" letter-spacing="2">{r['code']}</text>
  <text x="30" y="122" class="s ink" font-size="64" font-weight="700" letter-spacing="-2">{r['big']}</text>
  <text x="34" y="150" class="m ac" font-size="13" letter-spacing="1">{r['unit'].upper()}</text>
  <text x="32" y="196" class="s ink" font-size="19" font-weight="500">{r['title']}</text>
  {''.join(f'<text x="32" y="{224 + j*21}" class="s mu" font-size="14.5">{l}</text>' for j, l in enumerate(r['lines']))}
</g>''')
        if i:
            cells.append(f'<line x1="{x}" y1="0" x2="{x}" y2="{H}" stroke="{t["ink"]}" stroke-width="0.8"/>')
    body = f'''{grid(W, H, t)}<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{t['panel']}" fill-opacity="0.85" stroke="{t['ink']}" stroke-width="2"/>{''.join(cells)}'''
    return svg(W, H, body, t, "", "Research")


# ---------------------------------------------------------------------------------------------
# 5. Toolbox as a bill of materials.
# ---------------------------------------------------------------------------------------------

BOM = [
    ("01", "ENGINEERING", "Medium-voltage switchgear design", "RMU · MRMU · LBS · autorecloser"),
    ("02", "ENGINEERING", "Single-line and wiring diagrams", "Customer approval to production"),
    ("03", "SOFTWARE", "Python · TypeScript · Kotlin", "FastAPI · React · Next.js"),
    ("04", "SOFTWARE", "Android", "Jetpack Compose · Firebase"),
    ("05", "MACHINE LEARNING", "PyTorch", "Computer vision · signal processing"),
    ("06", "AUTOMATION", "LLM tooling", "Pipelines that remove repetitive work"),
]


def bom(t):
    W = 1200
    row = 44
    H = 64 + row * len(BOM) + 2
    cols = [32, 110, 330, 760]
    head = "".join(f'<text x="{c}" y="40" class="m fa" font-size="11" letter-spacing="2">{h}</text>'
                   for c, h in zip(cols, ["ITEM", "CATEGORY", "COMPONENT", "NOTES"]))
    rows = []
    for i, (n, cat, comp, note) in enumerate(BOM):
        y = 64 + i * row
        if i % 2:
            rows.append(f'<rect x="2" y="{y}" width="{W-4}" height="{row}" fill="{t["grid"]}" fill-opacity="0.55"/>')
        rows.append(f'''<text x="{cols[0]}" y="{y+28}" class="m mu" font-size="13">{n}</text>
<text x="{cols[1]}" y="{y+28}" class="m ac" font-size="11.5" letter-spacing="1.5">{cat}</text>
<text x="{cols[2]}" y="{y+28}" class="s ink" font-size="16" font-weight="500">{comp}</text>
<text x="{cols[3]}" y="{y+28}" class="s mu" font-size="15">{note}</text>''')
    lines = "".join(f'<line x1="{c-14}" y1="20" x2="{c-14}" y2="{H}" stroke="{t["ink"]}" stroke-width="0.5"/>' for c in cols[1:])
    body = f'''<rect x="1" y="1" width="{W-2}" height="{H-2}" fill="{t['panel']}" stroke="{t['ink']}" stroke-width="2"/>
{''.join(rows)}{head}<line x1="0" y1="64" x2="{W}" y2="64" stroke="{t['ink']}" stroke-width="1"/>{lines}'''
    return svg(W, H, body, t, "", "Toolbox")


# ---------------------------------------------------------------------------------------------
# 6. Footer title block.
# ---------------------------------------------------------------------------------------------

def footer(t):
    W, H = 1200, 96
    cells = [("DRAWN BY", "AHMAD NAYFEH"), ("DATE", "2026"), ("SCALE", "1 : 1"), ("SHEET", "01 / 01"), ("STATUS", "IN SERVICE")]
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
    return svg(W, H, body, t, "", "Title block")


def main():
    OUT.mkdir(exist_ok=True)
    for name, t in THEMES.items():
        (OUT / f"hero-{name}.svg").write_text(hero(t))
        (OUT / f"h-products-{name}.svg").write_text(header(t, "01", "Products", "SHIPPED · IN USE"))
        (OUT / f"h-research-{name}.svg").write_text(header(t, "02", "Research", "M.SC. AND COURSE WORK"))
        (OUT / f"h-toolbox-{name}.svg").write_text(header(t, "03", "Bill of materials", "WHAT I WORK WITH"))
        for p in PRODUCTS:
            (OUT / f"card-{p['key']}-{name}.svg").write_text(product_card(t, p))
        (OUT / f"research-{name}.svg").write_text(research(t))
        (OUT / f"bom-{name}.svg").write_text(bom(t))
        (OUT / f"footer-{name}.svg").write_text(footer(t))
    for f in sorted(OUT.glob("*.svg")):
        print(f"{f.name:32} {f.stat().st_size/1024:7.1f} KB")


if __name__ == "__main__":
    main()
