#!/usr/bin/env python3
"""Draw the Rick-and-Morty-style space wallpaper (original art) -> wallpaper.svg / .png."""
import math, random

W, H = 2560, 1440
random.seed(42)
o = []
add = o.append
add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add('''<defs>
 <linearGradient id="sky" x1="0" y1="0" x2="1" y2="1">
  <stop offset="0" stop-color="#03060b"/><stop offset=".55" stop-color="#071019"/><stop offset="1" stop-color="#0a0714"/></linearGradient>
 <radialGradient id="neb1"><stop offset="0" stop-color="#3f9a2c" stop-opacity=".55"/><stop offset="1" stop-color="#3f9a2c" stop-opacity="0"/></radialGradient>
 <radialGradient id="neb2"><stop offset="0" stop-color="#1f8aa8" stop-opacity=".45"/><stop offset="1" stop-color="#1f8aa8" stop-opacity="0"/></radialGradient>
 <radialGradient id="neb3"><stop offset="0" stop-color="#8a3fb8" stop-opacity=".40"/><stop offset="1" stop-color="#8a3fb8" stop-opacity="0"/></radialGradient>
 <radialGradient id="portal" cx="50%" cy="50%" r="50%">
  <stop offset="0" stop-color="#f6ffd9"/><stop offset=".22" stop-color="#d4ff86"/><stop offset=".55" stop-color="#8fd14a"/>
  <stop offset=".85" stop-color="#2f7d32"/><stop offset="1" stop-color="#1c4d1c" stop-opacity="0"/></radialGradient>
 <radialGradient id="glow"><stop offset="0" stop-color="#97ce4c" stop-opacity=".55"/><stop offset="1" stop-color="#97ce4c" stop-opacity="0"/></radialGradient>
 <radialGradient id="pink" cx="35%" cy="30%"><stop offset="0" stop-color="#f7b7d4"/><stop offset=".55" stop-color="#c2468a"/><stop offset="1" stop-color="#4a0f35"/></radialGradient>
 <radialGradient id="orange" cx="35%" cy="30%"><stop offset="0" stop-color="#ffe7a0"/><stop offset=".6" stop-color="#e0962a"/><stop offset="1" stop-color="#5a3008"/></radialGradient>
 <radialGradient id="teal" cx="35%" cy="30%"><stop offset="0" stop-color="#b9f6ff"/><stop offset=".6" stop-color="#2f9fc2"/><stop offset="1" stop-color="#0b3346"/></radialGradient>
 <radialGradient id="shade" cx="70%" cy="70%"><stop offset=".45" stop-color="#000" stop-opacity="0"/><stop offset="1" stop-color="#000" stop-opacity=".65"/></radialGradient>
 <linearGradient id="flame" x1="1" y1="0" x2="0" y2="0"><stop offset="0" stop-color="#fff3b0"/><stop offset=".4" stop-color="#ffb347"/><stop offset="1" stop-color="#ff5a2a" stop-opacity="0"/></linearGradient>
 <filter id="blur"><feGaussianBlur stdDeviation="60"/></filter>
 <filter id="soft"><feGaussianBlur stdDeviation="3"/></filter>
</defs>''')
add(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
# nebulae
for cx, cy, rx, ry, g in [(640, 520, 900, 620, "neb1"), (2100, 1150, 900, 520, "neb2"), (1900, 260, 700, 420, "neb3"), (300, 1250, 600, 350, "neb2")]:
    add(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" fill="url(#{g})" filter="url(#blur)"/>')
# stars
for _ in range(900):
    x, y = random.uniform(0, W), random.uniform(0, H)
    r = random.choice([.6, .8, 1, 1.2, 1.5, 2]) if random.random() > .03 else random.uniform(2.4, 3.4)
    col = random.choice(["#ffffff"] * 8 + ["#d6ffb0", "#bfe8ff"])
    add(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="{r}" fill="{col}" opacity="{random.uniform(.35, 1):.2f}"/>')
for _ in range(14):  # sparkle crosses
    x, y, s = random.uniform(0, W), random.uniform(0, H), random.uniform(6, 13)
    add(f'<path d="M{x-s} {y}L{x+s} {y}M{x} {y-s}L{x} {y+s}" stroke="#eaffd0" stroke-width="1.6" opacity=".8"/>')

# planets
RING = 'cx="2230" cy="310" rx="330" ry="58" fill="none" stroke="#ffd3ea" stroke-width="12" opacity=".6" transform="rotate(-14 2230 310)"'
add(f'<ellipse {RING}/>')  # back half of the ring, hidden by the planet
add('<circle cx="2230" cy="300" r="190" fill="url(#pink)"/><circle cx="2230" cy="300" r="190" fill="url(#shade)"/>')
add('<path d="M1900 310 A330 58 0 0 0 2560 310" fill="none" stroke="#ffd3ea" stroke-width="12" opacity=".6" transform="rotate(-14 2230 310)"/>')  # front half
add('<circle cx="1650" cy="1220" r="70" fill="url(#orange)"/><circle cx="1650" cy="1220" r="70" fill="url(#shade)"/>')
add('<circle cx="1180" cy="170" r="34" fill="url(#teal)"/><circle cx="1180" cy="170" r="34" fill="url(#shade)"/>')
add('<circle cx="2420" cy="1000" r="22" fill="url(#teal)" opacity=".8"/>')

# the portal
PX, PY, PR = 620, 760, 380
add(f'<circle cx="{PX}" cy="{PY}" r="{PR*1.7}" fill="url(#glow)"/>')
add(f'<circle cx="{PX}" cy="{PY}" r="{PR}" fill="url(#portal)"/>')
def spiral(arms, turns, r0, r1, width, color, op, rot):
    for a in range(arms):
        pts = []
        for i in range(80):
            t = i / 79
            ang = rot + a * 2 * math.pi / arms + t * turns * 2 * math.pi
            r = r1 + (r0 - r1) * t
            pts.append((PX + r * math.cos(ang), PY + r * math.sin(ang)))
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts)
        add(f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}" stroke-linecap="round" opacity="{op}"/>')
spiral(5, 1.1, 40, PR * .95, 34, "#e9ffb8", .55, 0)
spiral(5, 1.1, 30, PR * .9, 18, "#2f7d32", .55, .6)
spiral(7, .8, 20, PR * .75, 8, "#ffffff", .35, 1.2)
add(f'<circle cx="{PX}" cy="{PY}" r="70" fill="#f8ffe6" opacity=".9" filter="url(#soft)"/>')
for _ in range(40):  # portal sparks
    ang, r = random.uniform(0, 2 * math.pi), random.uniform(PR * .95, PR * 1.35)
    add(f'<circle cx="{PX + r*math.cos(ang):.0f}" cy="{PY + r*math.sin(ang):.0f}" r="{random.uniform(2, 6):.1f}" fill="#c6f36b" opacity="{random.uniform(.4, .9):.2f}"/>')

# Rick's space cruiser, flying out of the portal
S = 'stroke="#0b0d10" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"'
add('<g transform="translate(1040 560) rotate(-8) scale(3.1)">')
add('<path d="M-30 52 Q-110 40 -170 47 Q-110 58 -30 64 Z" fill="url(#flame)"/>')
add('<path d="M-6 44 Q-60 30 -100 44 Q-60 60 -6 60 Z" fill="#fff3b0" opacity=".85"/>')
add(f'<path d="M0 40 Q6 26 52 28 L150 33 Q205 40 208 55 Q204 70 150 72 L48 72 Q8 70 0 56 Z" fill="#c9ced6" {S.replace("7","3")}/>')
add('<path d="M20 60 L180 60" stroke="#8a929e" stroke-width="3"/>')
add(f'<path d="M76 32 Q90 2 128 4 Q160 8 162 36 Z" fill="#9fe3f5" fill-opacity=".8" {S.replace("7","3")}/>')
# Rick and Morty in the cockpit (tiny heads)
add('<path d="M96 30 L90 20 L97 22 L95 12 L101 19 L104 9 L108 19 L114 12 L113 22 L120 20 L114 30 Z" fill="#b8e3f2" stroke="#0b0d10" stroke-width="2" stroke-linejoin="round"/>')
add('<circle cx="105" cy="26" r="8" fill="#f2dcc8" stroke="#0b0d10" stroke-width="2"/><circle cx="102" cy="25" r="2.2" fill="#fff" stroke="#0b0d10" stroke-width="1"/><circle cx="108" cy="25" r="2.2" fill="#fff" stroke="#0b0d10" stroke-width="1"/>')
add('<circle cx="137" cy="27" r="8" fill="#f4d8bf" stroke="#0b0d10" stroke-width="2"/><path d="M129 25 Q130 16 137 16 Q145 16 145 25 Q140 20 137 22 Q133 19 129 25 Z" fill="#6b3f1d" stroke="#0b0d10" stroke-width="2" stroke-linejoin="round"/>')
add('<circle cx="134" cy="27" r="2.4" fill="#fff" stroke="#0b0d10" stroke-width="1"/><circle cx="140" cy="27" r="2.4" fill="#fff" stroke="#0b0d10" stroke-width="1"/>')
add('<path d="M30 72 L18 92 M170 72 L184 92" stroke="#0b0d10" stroke-width="5" stroke-linecap="round"/>')
add('<circle cx="60" cy="50" r="5" fill="#ff5a5a" stroke="#0b0d10" stroke-width="2"/><circle cx="185" cy="54" r="5" fill="#97ce4c" stroke="#0b0d10" stroke-width="2"/>')
add('</g>')

# a few floating bits from the show's vibe: a lost Plumbus-ish blob, a Meeseeks box-style cube, a flying saucer
add(f'<g transform="translate(1900 820) rotate(18)"><ellipse cx="0" cy="0" rx="46" ry="22" fill="#e89bb0" {S.replace("7","4")}/><circle cx="-30" cy="-6" r="16" fill="#f2b9c8" stroke="#0b0d10" stroke-width="4"/><path d="M20 -18 L32 -40" stroke="#0b0d10" stroke-width="4"/><circle cx="34" cy="-44" r="7" fill="#c97b8f" stroke="#0b0d10" stroke-width="3"/></g>')
add(f'<g transform="translate(2050 600) rotate(-12)"><rect x="-38" y="-30" width="76" height="60" rx="8" fill="#5aa9d6" {S.replace("7","4")}/><circle cx="0" cy="0" r="14" fill="#9fe3f5" stroke="#0b0d10" stroke-width="4"/></g>')
add(f'<g transform="translate(1420 1060) rotate(-6) scale(1.2)"><ellipse cx="0" cy="10" rx="70" ry="18" fill="#9aa3ad" {S.replace("7","4")}/><path d="M-34 6 Q-30 -26 0 -28 Q30 -26 34 6 Z" fill="#b6f0c0" fill-opacity=".8" stroke="#0b0d10" stroke-width="4"/><circle cx="-40" cy="14" r="5" fill="#ffd34d"/><circle cx="0" cy="18" r="5" fill="#ffd34d"/><circle cx="40" cy="14" r="5" fill="#ffd34d"/></g>')

# tagline
add('<text x="2480" y="1370" text-anchor="end" font-family="Impact, \'Anton\', \'DejaVu Sans\', sans-serif" font-weight="900" font-size="64" letter-spacing="4" fill="#c6f36b" stroke="#0b0d10" stroke-width="8" paint-order="stroke" opacity=".9">WUBBA LUBBA DUB DUB</text>')
add('</svg>')
open("wallpaper.svg", "w").write("\n".join(o))
