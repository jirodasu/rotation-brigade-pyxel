import pyxel
from game_v3 import Unit
from game_jp import Game as JapaneseGame
from jp_embedded_font import GLYPH, ROWS

W, H = 300, 430
CELL = 12
COLS = 16

class Game(JapaneseGame):
    def __init__(self):
        pyxel.init(W, H, title="回転旅団", fps=30)
        pyxel.mouse(True)

        # Build the Japanese glyph atlas entirely in memory.
        atlas = pyxel.image(1)
        atlas.cls(0)
        for i, glyph in enumerate(ROWS):
            sx = (i % COLS) * CELL
            sy = (i // COLS) * CELL
            for yy, bits in enumerate(glyph):
                for xx in range(CELL):
                    if bits & (1 << (11 - xx)):
                        atlas.pset(sx + xx, sy + yy, 7)

        self.u = {
            "A": Unit("A", "ALLEN", 60, 20, 16),
            "B": Unit("B", "BELL", 55, 22, 14),
            "C": Unit("C", "CLAUDE", 75, 14, 20, "DEF", 10),
            "M": Unit("M", "MIRA", 48, 12, 12, "ATK", 10),
            "S": Unit("S", "SERA", 75, 8, 0, "DEF", 6),
            "R": Unit("R", "RAIN", 50, 14, 10, "RANGED", 18),
            "G": Unit("G", "GALD", 55, 17, 16, "ATK", 6),
        }
        self.bi = 0
        self.state = "TITLE"
        self.sel = 0
        self.events = []
        self.ei = -1
        self.tick = 0
        self.paused = False
        self.turn = 1
        self.bhp = 1
        self.bmax = 1
        self.form = [[None] * 4 for _ in range(3)]
        self.dealt = 0
        self.taken = 0
        self.final = None
        self.final_state = "READY"
        pyxel.run(self.update, self.draw)

    def text_width(self, text, scale=1):
        return sum((10 if ch in GLYPH else 4) * scale for ch in str(text))

    def jtext(self, x, y, text, col=7, scale=1):
        cx = x
        pyxel.pal(7, col)
        for ch in str(text):
            if ch in GLYPH:
                i = GLYPH[ch]
                sx = (i % COLS) * CELL
                sy = (i // COLS) * CELL
                if scale == 1:
                    pyxel.blt(cx, y, 1, sx, sy, CELL, CELL, 0)
                    cx += 10
                else:
                    for yy, bits in enumerate(ROWS[i]):
                        for xx in range(CELL):
                            if bits & (1 << (11 - xx)):
                                pyxel.rect(cx + xx * scale, y + yy * scale, scale, scale, col)
                    cx += 10 * scale
            else:
                pyxel.text(cx, y + (2 if scale == 1 else 4), ch, col)
                cx += 4 * scale
        pyxel.pal()
