#!/usr/bin/env python3
"""news-image-20261120: one image summing up the world news of Friday
20 November 2026. Pure Python 3 standard library, no network, fully
deterministic: byte-identical output on every run.

Layout (1024x1024, broadsheet front page on paper white):
  - masthead: THE DAY IN NEWS / FRIDAY - 20 NOVEMBER 2026
  - 2x3 grid of story panels, each with a drawn icon, a two-line
    headline and a detail line
  - footer: source line

Stories (all happened or were first reported on 2026-11-20, verified
against multiple outlets on the day):
  1. Global markets tumble on AI jitters; Nikkei -4.8%, dollar at a
     19-month high (Reuters, 20 Nov)
  2. Houthi missiles damage Riyadh's PIF tower; a tanker burns after
     hitting a mine near Hormuz; oil climbs (Reuters, 20 Nov)
  3. UK pledges 1,000+ drones to Ukraine in a GBP 260M package as
     Europe readies new peace talks (BBC / Berlin reporting, 20 Nov)
  4. Taiwan flags some 2,700 China-linked accounts to Meta ahead of
     the 28 November local elections (Reuters, 20 Nov)
  5. COP31 reaches its final day in Antalya with fossil fuels cut
     from the draft deal (Reuters / Le Monde, 20 Nov)
  6. GTA VI estimated at 24.6M copies and $2.36B on launch day, the
     biggest entertainment launch ever (Sensor Tower via BBC, 20 Nov)
"""

import os
import struct
import zlib

W, H = 1024, 1024

# ------------------------------------------------------------ typeface ----
# Hand-drawn 5x7 bitmap glyphs. '#' marks an inked cell.
GLYPHS = {
    'A': (".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'B': ("####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."),
    'C': (".####", "#....", "#....", "#....", "#....", "#....", ".####"),
    'D': ("###..", "#..#.", "#...#", "#...#", "#...#", "#..#.", "###.."),
    'E': ("#####", "#....", "#....", "####.", "#....", "#....", "#####"),
    'F': ("#####", "#....", "#....", "####.", "#....", "#....", "#...."),
    'G': (".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."),
    'H': ("#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"),
    'I': (".###.", "..#..", "..#..", "..#..", "..#..", "..#..", ".###."),
    'J': ("..###", "...#.", "...#.", "...#.", "...#.", "#..#.", ".##.."),
    'K': ("#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"),
    'L': ("#....", "#....", "#....", "#....", "#....", "#####", "#####"),
    'M': ("#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"),
    'N': ("#...#", "##..#", "#.#.#", "#..##", "#...#", "#...#", "#...#"),
    'O': (".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'P': ("####.", "#...#", "#...#", "####.", "#....", "#....", "#...."),
    'Q': (".###.", "#...#", "#...#", "#...#", "#.#.#", "#..#.", ".##.#"),
    'R': ("####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"),
    'S': (".####", "#....", "#....", ".###.", "....#", "....#", "####."),
    'T': ("#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."),
    'U': ("#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."),
    'V': ("#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."),
    'W': ("#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"),
    'X': ("#...#", ".#.#.", ".#.#.", "..#..", ".#.#.", ".#.#.", "#...#"),
    'Y': ("#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."),
    'Z': ("#####", "....#", "...#.", "..#..", ".#...", "#....", "#####"),
    '0': (".###.", "#...#", "#..##", "#.#.#", "##..#", "#...#", ".###."),
    '1': ("..#..", ".##..", "..#..", "..#..", "..#..", "..#..", ".###."),
    '2': (".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"),
    '3': ("####.", "....#", "....#", ".###.", "....#", "....#", "####."),
    '4': ("...#.", "..##.", ".#.#.", "#..#.", "#####", "...#.", "...#."),
    '5': ("#####", "#....", "####.", "....#", "....#", "#...#", ".###."),
    '6': (".###.", "#....", "#....", "####.", "#...#", "#...#", ".###."),
    '7': ("#####", "....#", "...#.", "..#..", "..#..", "..#..", "..#.."),
    '8': (".###.", "#...#", "#...#", ".###.", "#...#", "#...#", ".###."),
    '9': (".###.", "#...#", "#...#", ".####", "....#", "....#", ".###."),
    ' ': (".....", ".....", ".....", ".....", ".....", ".....", "....."),
    '.': (".....", ".....", ".....", ".....", ".....", ".##..", ".##.."),
    ',': (".....", ".....", ".....", ".....", ".##..", ".##..", ".#..."),
    "'": ("..#..", "..#..", ".#...", ".....", ".....", ".....", "....."),
    '-': (".....", ".....", ".....", "#####", ".....", ".....", "....."),
    ':': (".....", ".##..", ".##..", ".....", ".##..", ".##..", "....."),
    '/': ("....#", "...#.", "...#.", "..#..", ".#...", ".#...", "#...."),
    '$': ("..#..", ".####", "#.#.#", ".###.", "..#.#", "####.", "..#.."),
    '*': (".....", ".#.#.", "..#..", "#####", "..#..", ".#.#.", "....."),
    '!': ("..#..", "..#..", "..#..", "..#..", "..#..", ".....", "..#.."),
    '%': ("#...#", "#..#.", "...#.", "..#..", ".#...", "#..#.", "#...#"),
    '(': ("...#.", "..#..", ".#...", ".#...", ".#...", "..#..", "...#."),
    ')': (".#...", "..#..", "...#.", "...#.", "...#.", "..#..", ".#..."),
    '+': (".....", "..#..", "..#..", "#####", "..#..", "..#..", "....."),
}

# -------------------------------------------------------------- canvas ----
class Page:
    """A tiny RGB raster with the few primitives the front page needs."""

    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.buf = bytearray(bytes(bg) * (w * h))

    def put(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i:i + 3] = bytes(c)

    def fill(self, x, y, w, h, c):
        x0, y0 = max(0, x), max(0, y)
        x1, y1 = min(self.w, x + w), min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(c) * (x1 - x0)
        for yy in range(y0, y1):
            base = (yy * self.w + x0) * 3
            self.buf[base:base + len(row)] = row

    def frame(self, x, y, w, h, c, t=3):
        self.fill(x, y, w, t, c)
        self.fill(x, y + h - t, w, t, c)
        self.fill(x, y, t, h, c)
        self.fill(x + w - t, y, t, h, c)

    def seg(self, x0, y0, x1, y1, c, t=1):
        # Bresenham segment with a square brush of thickness t
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err, x, y = dx - dy, x0, y0
        while True:
            self.fill(x, y, t, t, c)
            if x == x1 and y == y1:
                return
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x += sx
            if e2 < dx:
                err += dx
                y += sy

    def disc(self, cx, cy, r, c, fill=True):
        for yy in range(cy - r, cy + r + 1):
            for xx in range(cx - r, cx + r + 1):
                d2 = (xx - cx) * (xx - cx) + (yy - cy) * (yy - cy)
                if fill and d2 <= r * r:
                    self.put(xx, yy, c)
                elif not fill and abs(d2 - r * r) <= 2 * r:
                    self.put(xx, yy, c)

    def fan(self, pts, c):
        # scanline fill of a simple polygon
        lo = max(0, min(p[1] for p in pts))
        hi = min(self.h - 1, max(p[1] for p in pts))
        n = len(pts)
        for y in range(lo, hi + 1):
            cuts = []
            for i in range(n):
                ax, ay = pts[i]
                bx, by = pts[(i + 1) % n]
                if (ay <= y < by) or (by <= y < ay):
                    cuts.append(ax + (y - ay) * (bx - ax) / (by - ay))
            cuts.sort()
            for i in range(0, len(cuts) - 1, 2):
                self.fill(int(cuts[i]), y, int(cuts[i + 1]) - int(cuts[i]) + 1,
                          1, c)

    def say(self, s, x, y, scale, c, align="left"):
        s = s.upper()
        w = len(s) * 6 * scale - scale
        if align == "center":
            x -= w // 2
        elif align == "right":
            x -= w
        for ci, ch in enumerate(s):
            glyph = GLYPHS.get(ch, GLYPHS[' '])
            ox = x + ci * 6 * scale
            for gy, row in enumerate(glyph):
                for gx, bit in enumerate(row):
                    if bit == '#':
                        self.fill(ox + gx * scale, y + gy * scale,
                                  scale, scale, c)


# ----------------------------------------------------------------- png ----
def save_png(page, path):
    stride = page.w * 3
    raw = bytearray()
    for y in range(page.h):
        raw.append(0)
        raw += page.buf[y * stride:(y + 1) * stride]
    payload = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", page.w, page.h,
                                        8, 2, 0, 0, 0))
           + chunk(b"IDAT", payload)
           + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)
    return len(png)


# ------------------------------------------------------------- palette ----
PAPER = (246, 240, 226)
CARD = (253, 251, 245)
INK = (18, 22, 30)
FAINT = (110, 112, 108)
RULE = (176, 32, 40)
GOLD = (206, 150, 40)
RED = (196, 44, 44)
TEAL = (28, 138, 128)
AMBER = (216, 138, 30)
BLUE = (52, 102, 184)
PINK = (214, 74, 138)
GREEN = (74, 158, 84)
SKY = (120, 178, 226)


# --------------------------------------------------------------- icons ----
# Each icon draws inside a 200x110 box with top-left corner (bx, by).

def icon_markets(pg, bx, by):
    # falling bars and a plunging arrow
    pg.seg(bx + 16, by + 12, bx + 16, by + 94, INK, 4)
    pg.seg(bx + 16, by + 94, bx + 188, by + 94, INK, 4)
    for i, bh in enumerate((58, 44, 30, 16)):
        pg.fill(bx + 34 + i * 38, by + 94 - bh, 24, bh, RED)
    pg.seg(bx + 30, by + 26, bx + 74, by + 44, INK, 6)
    pg.seg(bx + 74, by + 44, bx + 116, by + 58, INK, 6)
    pg.seg(bx + 116, by + 58, bx + 164, by + 82, INK, 6)
    pg.seg(bx + 164, by + 82, bx + 146, by + 84, INK, 6)
    pg.seg(bx + 164, by + 82, bx + 160, by + 64, INK, 6)
    pg.say("-4.8%", bx + 128, by + 6, 3, RED)


def icon_riyadh(pg, bx, by):
    # a tower, a missile arcing in, a burst, and sea waves below
    pg.fill(bx + 128, by + 30, 34, 66, (90, 96, 110))
    for wy in range(by + 38, by + 90, 12):
        for wx in (bx + 134, bx + 146):
            pg.fill(wx, wy, 6, 6, (240, 214, 120))
    pg.fill(bx + 124, by + 24, 42, 6, (70, 76, 90))
    pg.seg(bx + 20, by + 16, bx + 96, by + 44, INK, 7)
    pg.fan([(bx + 92, by + 38), (bx + 116, by + 48), (bx + 94, by + 56)],
           (240, 130, 40))
    for dx, dy in ((18, -8), (24, 4), (14, 14), (2, 20)):
        pg.seg(bx + 108, by + 46, bx + 108 + dx, by + 46 + dy,
               (240, 130, 40), 4)
    for xx in range(0, 200, 22):
        pg.seg(bx + xx, by + 102, bx + xx + 11, by + 96, BLUE, 3)
        pg.seg(bx + xx + 11, by + 96, bx + xx + 22, by + 102, BLUE, 3)


def icon_drone(pg, bx, by):
    # quadcopter seen from the front, flag chip beneath
    cx, cy = bx + 100, by + 48
    for rx, ry in ((cx - 62, cy - 26), (cx + 62, cy - 26),
                   (cx - 62, cy + 22), (cx + 62, cy + 22)):
        pg.disc(rx, ry, 13, INK, fill=False)
        pg.seg(rx - 13, ry, rx + 13, ry, INK, 3)
    pg.seg(cx - 52, cy - 18, cx + 52, cy + 14, INK, 5)
    pg.seg(cx - 52, cy + 14, cx + 52, cy - 18, INK, 5)
    pg.fill(cx - 18, cy - 12, 36, 22, (52, 60, 74))
    pg.disc(cx, cy + 16, 6, AMBER)
    pg.fill(bx + 70, by + 88, 60, 16, BLUE)
    pg.fill(bx + 70, by + 96, 60, 8, (240, 200, 60))


def icon_eye(pg, bx, by):
    # an eye over a row of account dots: platforms under scrutiny
    cx, cy = bx + 100, by + 44
    pg.fan([(bx + 28, cy), (cx, cy - 34), (bx + 172, cy), (cx, cy + 34)],
           (226, 238, 250))
    pg.disc(cx, cy, 15, BLUE)
    pg.disc(cx, cy, 7, INK)
    pg.disc(cx - 5, cy - 5, 3, CARD)
    for i in range(5):
        dx = bx + 34 + i * 34
        pg.disc(dx, by + 92, 7, TEAL)
        pg.fan([(dx - 9, by + 108), (dx + 9, by + 108), (dx, by + 98)],
               TEAL)


def icon_climate(pg, bx, by):
    # globe with a thermometer: talks under a warming world
    pg.disc(bx + 74, by + 54, 40, SKY)
    pg.fan([(bx + 52, by + 30), (bx + 72, by + 24), (bx + 80, by + 40),
            (bx + 64, by + 50), (bx + 48, by + 44)], GREEN)
    pg.fan([(bx + 84, by + 58), (bx + 102, by + 54), (bx + 104, by + 72),
            (bx + 88, by + 78), (bx + 80, by + 68)], GREEN)
    pg.seg(bx + 34, by + 54, bx + 114, by + 54, (46, 106, 160), 3)
    pg.fill(bx + 148, by + 14, 12, 62, CARD)
    pg.frame(bx + 148, by + 14, 12, 62, INK, 3)
    pg.fill(bx + 151, by + 44, 6, 29, RED)
    pg.disc(bx + 154, by + 84, 13, RED)
    pg.disc(bx + 154, by + 84, 6, (255, 170, 120))
    for i in range(4):
        pg.seg(bx + 160, by + 22 + i * 14, bx + 168, by + 22 + i * 14,
               INK, 3)


def icon_gta(pg, bx, by):
    # neon dusk bands, a big VI, palms at the edges
    bands = [(250, 196, 84), (246, 138, 92), (214, 74, 138), (128, 74, 190)]
    for i, c in enumerate(bands):
        pg.fill(bx + 24, by + 4 + i * 11, 152, 9, c)
    pg.say("VI", bx + 100, by + 50, 7, (30, 24, 44), align="center")
    pg.seg(bx + 14, by + 106, bx + 20, by + 66, (30, 24, 44), 5)
    for dx, dy in ((-26, -8), (-18, -20), (-2, -24)):
        pg.seg(bx + 20, by + 66, bx + 20 + dx, by + 66 + dy, (30, 24, 44), 3)
    pg.seg(bx + 186, by + 106, bx + 180, by + 66, (30, 24, 44), 5)
    for dx, dy in ((26, -8), (18, -20), (2, -24)):
        pg.seg(bx + 180, by + 66, bx + 180 + dx, by + 66 + dy,
               (30, 24, 44), 3)


# -------------------------------------------------------------- layout ----
STORIES = [
    ("MARKETS", RED, icon_markets,
     "MARKETS TUMBLE", "ON AI JITTERS", "NIKKEI -4.8% - DOLLAR HIGH"),
    ("SAUDI ARABIA", AMBER, icon_riyadh,
     "HOUTHI MISSILES", "HIT RIYADH TOWER", "OIL CLIMBS - HORMUZ TANKER"),
    ("UKRAINE", BLUE, icon_drone,
     "UK SENDS 1,000+", "DRONES TO UKRAINE", "EUROPE READIES TALKS"),
    ("TAIWAN", TEAL, icon_eye,
     "TAIWAN FLAGS", "2,700 ACCOUNTS", "META TOLD BEFORE VOTE"),
    ("CLIMATE", GREEN, icon_climate,
     "COP31 FINAL DAY", "FOSSIL FUELS CUT", "FROM ANTALYA DRAFT DEAL"),
    ("GAMES", PINK, icon_gta,
     "GTA VI SELLS", "24.6M ON DAY ONE", "$2.36B - BIGGEST LAUNCH"),
]


def front_page():
    pg = Page(W, H, PAPER)

    # masthead
    pg.say("THE DAY IN NEWS", W // 2, 26, 9, INK, align="center")
    pg.fill(40, 116, W - 80, 6, INK)
    pg.fill(40, 128, W - 80, 3, RULE)
    pg.say("FRIDAY - 20 NOVEMBER 2026", W // 2, 142, 5, RULE,
           align="center")
    pg.fill(40, 186, W - 80, 3, RULE)
    pg.fill(40, 193, W - 80, 6, INK)

    # 2 columns x 3 rows of story cards
    cx0, cy0, cw, chh, gx, gy = 28, 208, 474, 246, 20, 10
    for i, (tag, accent, icon, head1, head2, detail) in enumerate(STORIES):
        x = cx0 + (i % 2) * (cw + gx)
        y = cy0 + (i // 2) * (chh + gy)
        pg.fill(x, y, cw, chh, CARD)
        pg.frame(x, y, cw, chh, INK, 3)
        pg.fill(x, y, cw, 12, accent)
        pg.say(tag, x + 18, y + 24, 3, accent)
        icon(pg, x + (cw - 200) // 2, y + 48)
        pg.say(head1, x + cw // 2, y + 164, 4, INK, align="center")
        pg.say(head2, x + cw // 2, y + 196, 4, INK, align="center")
        pg.say(detail, x + cw // 2, y + 228, 2, FAINT, align="center")

    # footer
    pg.fill(40, 976, W - 80, 3, INK)
    pg.say("SOURCES: REUTERS - BBC - LE MONDE - SENSOR TOWER",
           W // 2, 986, 2, FAINT, align="center")
    return pg


def main():
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    size = save_png(front_page(), path)
    print("wrote %s (%d bytes)" % (path, size))


if __name__ == "__main__":
    main()
