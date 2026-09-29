import pyxel
from game_v3 import Game as BaseGame


class Game(BaseGame):
    """Readability pass: explicit HP deltas and per-unit contribution summary."""

    def record(self, src, dst, kind, n, detail="", col=None):
        before = after = None
        if kind == "DAMAGE":
            if dst == "BOSS":
                after = self.bhp
                before = after + n
            elif dst in self.u:
                after = self.u[dst].hp
                before = after + n
        elif kind == "HEAL" and dst in self.u:
            after = self.u[dst].hp
            before = after - n
        self.events.append({
            "s": src, "d": dst, "k": kind, "n": n,
            "detail": detail, "col": col,
            "before": before, "after": after,
            "snap": self.snap(),
        })

    def contribution_lines(self):
        out = []
        for e in self.events:
            if e["k"] == "DAMAGE" and e["d"] == "BOSS":
                out.append(f"{self.name(e['s'])[:6]:6}  -{e['n']} DMG")
        return out

    def incoming_lines(self):
        out = []
        for e in self.events:
            if e["k"] == "DAMAGE" and e["s"] == "BOSS":
                out.append(f"{self.name(e['d'])[:6]:6}  -{e['n']} HP")
        return out

    def draw_readout(self):
        pyxel.rect(4, 202, 248, 94, 0)
        pyxel.rectb(4, 202, 248, 94, 5)

        if self.state == "READY":
            pyxel.text(10, 210, "BATTLE FLOW", 10)
            pyxel.text(10, 224, "FRONT attacks / MID supports / BACK recovers", 7)
            pyxel.text(10, 238, "Enemy damage can hit FRONT only.", 8)
            pyxel.text(10, 254, "Watch attacker -> target -> exact HP change.", 6)
            return

        if not self.events:
            return

        if self.state == "PLAY":
            e = self.current_event()
            s, d, k, n = self.name(e["s"]), self.name(e["d"]), e["k"], e["n"]
            col = 8 if k == "DAMAGE" else 11 if k == "HEAL" else 10
            pyxel.text(10, 208, f"ACTION {self.ei+1}/{len(self.events)}", 10)
            pyxel.text(166, 208, f"OUT {self.dealt}", 10)
            pyxel.text(10, 222, s, 10)
            pyxel.text(65, 222, ">", 6)
            pyxel.text(77, 222, d, col)

            if k == "DAMAGE":
                result = f"-{n} DAMAGE"
            elif k == "HEAL":
                result = f"+{n} HP"
            elif k == "SUPPORT":
                result = f"ATK +{n}"
            elif k == "GUARD":
                result = f"DAMAGE -{n}"
            else:
                result = "NO DAMAGE"
            pyxel.text(10, 237, result, col)

            if e.get("before") is not None and e.get("after") is not None:
                pyxel.text(112, 237, f"HP {e['before']} > {e['after']}", col)
            pyxel.text(10, 250, e["detail"][:40], 6)

            # Keep only the two immediately previous actions as context.
            y = 266
            for old in self.events[max(0, self.ei-2):self.ei]:
                pyxel.text(10, y, self.short(old)[:42], 5)
                y += 9
            return

        pyxel.text(10, 208, f"TURN {self.turn} RESULT", 10)
        pyxel.text(151, 208, f"OUT {self.dealt} / IN {self.taken}", 10)
        pyxel.text(10, 221, "DAMAGE BY UNIT", 6)
        contrib = self.contribution_lines()
        for i, line in enumerate(contrib[:4]):
            x = 10 + (i % 2) * 118
            y = 233 + (i // 2) * 12
            pyxel.text(x, y, line, 10 if i < 2 else 7)

        incoming = self.incoming_lines()
        if incoming:
            pyxel.text(10, 260, "ENEMY HIT", 8)
            pyxel.text(64, 260, " / ".join(incoming[:2])[:43], 8)
        else:
            pyxel.text(10, 260, "ENEMY HIT: NONE", 5)
        pyxel.text(10, 278, "ROTATE OR STAY?", 7)
