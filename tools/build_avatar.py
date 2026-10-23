"""Profile picture in the same drawing-sheet style as the README panels.

Writes assets/avatar.svg; tools/render_avatar.js turns it into a 1024px PNG for upload.
Everything important sits inside the central circle, because GitHub crops avatars round.
"""
from build_profile import FONTS, THEMES, ROOT

t = THEMES["dark"]
S = 1024
C = S / 2
ink, acc, mu, grid = t["ink"], t["accent"], t["muted"], t["grid"]

lines = []
for i in range(0, S + 1, 32):
    major = i % 128 == 0
    col = t["grid2"] if major else grid
    w = 1.6 if major else 0.8
    lines.append(f'<line x1="{i}" y1="0" x2="{i}" y2="{S}" stroke="{col}" stroke-width="{w}"/>')
    lines.append(f'<line x1="0" y1="{i}" x2="{S}" y2="{i}" stroke="{col}" stroke-width="{w}"/>')

# A single-line diagram fragment under the monogram: bus with three closed load-break switches.
bus_y = 640
xs = [C - 150, C, C + 150]
sld = [f'<line x1="{C-230}" y1="{bus_y}" x2="{C+230}" y2="{bus_y}" stroke="{ink}" stroke-width="10" stroke-linecap="round"/>']
for x in xs:
    sld.append(f'<line x1="{x}" y1="{bus_y}" x2="{x}" y2="{bus_y+56}" stroke="{acc}" stroke-width="6" stroke-linecap="round"/>')
    sld.append(f'<circle cx="{x}" cy="{bus_y+56}" r="8" fill="{acc}"/>')
    sld.append(f'<line x1="{x}" y1="{bus_y+56}" x2="{x}" y2="{bus_y+108}" stroke="{acc}" stroke-width="6" stroke-linecap="round"/>')
    sld.append(f'<path d="M{x-20} {bus_y+108} H{x+20} L{x} {bus_y+142} Z" fill="none" stroke="{acc}" stroke-width="5" stroke-linejoin="round"/>')
# Incoming feeder from the top of the circle into the monogram's frame.
feeder = f'<line x1="{C}" y1="150" x2="{C}" y2="250" stroke="{ink}" stroke-width="6" stroke-linecap="round"/><circle cx="{C}" cy="150" r="10" fill="{ink}"/>'

svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{S}" height="{S}" viewBox="0 0 {S} {S}">
<style>{FONTS}</style>
<defs>
  <radialGradient id="glow" cx="50%" cy="46%" r="55%">
    <stop offset="0" stop-color="{t['panel']}" stop-opacity="1"/>
    <stop offset="1" stop-color="{t['bg']}" stop-opacity="1"/>
  </radialGradient>
</defs>
<rect width="{S}" height="{S}" fill="url(#glow)"/>
<g opacity="0.9">{''.join(lines)}</g>
<circle cx="{C}" cy="{C}" r="430" fill="none" stroke="{ink}" stroke-width="2.5" opacity="0.55"/>
<circle cx="{C}" cy="{C}" r="416" fill="none" stroke="{ink}" stroke-width="1" opacity="0.35" stroke-dasharray="4 10"/>
{feeder}
<rect x="{C-250}" y="250" width="500" height="300" fill="{t['panel']}" stroke="{ink}" stroke-width="5"/>
<text x="{C}" y="478" text-anchor="middle" font-family="Plex" font-weight="700" font-size="250" letter-spacing="-6" fill="{ink}">AN</text>
<rect x="{C-250}" y="550" width="500" height="18" fill="{acc}"/>
<line x1="{C}" y1="568" x2="{C}" y2="{bus_y}" stroke="{ink}" stroke-width="6"/>
{''.join(sld)}
</svg>
'''
(ROOT / "assets" / "avatar.svg").write_text(svg)
print("assets/avatar.svg", round(len(svg) / 1024), "KB")
