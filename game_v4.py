import pyxel
from game_v3 import Game as BaseGame, EVENT_FRAMES


class Game(BaseGame):
    """Combat readability pass.

    Keeps battle rules intact and changes presentation only:
    - source/target are visually paired
    - damage appears at the actual target
    - HP before/after is explicit
    - each unit keeps a compact turn contribution badge
    - end-of-turn contribution summary is always available
    """

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

        self.events.append(
            {
                "s": src,
                "d": dst,
                "k": kind,
                "n": n,
                "detail": detail,
                "col": col,
                "before": before,
                "after": after,
                "snap": self.snap(),
            }
        )

    def visible_events(self):
        if self.state == "PLAY":
            return self.events[: self.ei + 1]
        return self.events

    def unit_mark(self, key):
        mark = None
        color = 6
        for e in self.visible_events():
            if e["k"] == "DAMAGE" and e["d"] == "BOSS" and e["s"] == key:
                mark, color = f"D{e['n']}", 10
            elif e["k"] == "DAMAGE" and e["s"] == "BOSS" and e["d"] == key:
                mark, color = f"H{e['n']}", 8
            elif e["k"] == "HEAL" and e["d"] == key:
                mark, color = f"+{e['n']}", 11
            elif e["k"] == "SUPPORT" and e["s"] == key:
                mark, color = f"S{e['n']}", 10
            elif e["k"] == "GUARD" and e["s"] == key:
                mark, color = f"G{e['n']}", 6
        return mark, color

    def contribution_lines(self):
        return [
            f"{self.name(e['s'])[:6]:6}  {e['n']:>2} DMG"
            for e in self.events
            if e["k"] == "DAMAGE" and e["d"] == "BOSS"
        ]

    def incoming_lines(self):
        return [
            f"{self.name(e['d'])[:6]:6}  -{e['n']} HP"
            for e in self.events
            if e["k"] == "DAMAGE" and e["s"] == "BOSS"
        ]

    def draw_formation(self):
        super().draw_formation()

        e = self.current_event() if self.state == "PLAY" and self.events else None

        for key in self.u:
            q = self.cell_rect(key)
            if not q:
                continue
            mark, color = self.unit_mark(key)
            if mark:
                x = q[0] + q[2] - (len(mark) * 4 + 5)
                y = q[1] + q[3] - 9
                pyxel.rect(x - 2, y - 1, len(mark) * 4 + 5, 9, 0)
                pyxel.text(x, y, mark, color)

        if e:
            if e["s"] != "BOSS":
                q = self.cell_rect(e["s"])
                if q:
                    pyxel.rect(q[0] + 2, q[1] - 8, 17, 8, 0)
                    pyxel.text(q[0] + 3, q[1] - 7, "ACT", 10)
            if e["d"] != "BOSS":
                q = self.cell_rect(e["d"])
                if q:
                    label = "HIT" if e["k"] == "DAMAGE" else "TO"
                    col = 8 if e["k"] == "DAMAGE" else 11 if e["k"] == "HEAL" else 10
                    pyxel.rect(q[0] + 31, q[1] - 8, 20, 8, 0)
                    pyxel.text(q[0] + 33, q[1] - 7, label, col)

    def action_type(self, e):
        if e["k"] == "DAMAGE":
            return "ENEMY ATTACK" if e["s"] == "BOSS" else "ALLY ATTACK"
        if e["k"] == "HEAL":
            return "RECOVERY"
        if e["k"] == "SUPPORT":
            return "ATTACK SUPPORT"
        if e["k"] == "GUARD":
            return "DEFENSE SUPPORT"
        return "ENEMY ACTION"

    def draw_name_box(self, x, y, w, name, color):
        pyxel.rect(x, y, w, 15, 1)
        pyxel.rectb(x, y, w, 15, color)
        pyxel.text(x + 4, y + 5, name[:10], color)

    def draw_readout(self):
        pyxel.rect(4, 202, 248, 94, 0)
        pyxel.rectb(4, 202, 248, 94, 5)

        if self.state == "READY":
            pyxel.text(10, 210, "BATTLE FLOW", 10)
            pyxel.text(10, 224, "FRONT attacks / MID supports / BACK recovers", 7)
            pyxel.text(10, 238, "Enemy damage can hit FRONT only.", 8)
            pyxel.text(10, 254, "During battle: ACT -> TARGET -> exact HP change.", 6)
            pyxel.text(10, 268, "D=damage  H=hit  S=support  G=guard", 5)
            return

        if not self.events:
            return

        if self.state == "PLAY":
            e = self.current_event()
            s, d, k, n = self.name(e["s"]), self.name(e["d"]), e["k"], e["n"]
            col = 8 if k == "DAMAGE" else 11 if k == "HEAL" else 10

            pyxel.text(10, 207, f"NOW {self.ei+1}/{len(self.events)}  {self.action_type(e)}", col)

            self.draw_name_box(10, 218, 88, s, 10)
            pyxel.text(105, 223, ">>>", 6)
            self.draw_name_box(126, 218, 88, d, col)

            if k == "DAMAGE":
                result = f"-{n}"
                result_label = "DAMAGE"
            elif k == "HEAL":
                result = f"+{n}"
                result_label = "HEAL"
            elif k == "SUPPORT":
                result = f"+{n}"
                result_label = "ATK"
            elif k == "GUARD":
                result = f"-{n}"
                result_label = "BLOCK"
            else:
                result = "0"
                result_label = "WAIT"

            pyxel.rect(10, 238, 70, 25, 1)
            pyxel.rectb(10, 238, 70, 25, col)
            w = self.big_w(result, 2)
            self.big_text(14, 243, result, col, 2)
            pyxel.text(16 + w, 249, result_label, col)

            if e.get("before") is not None and e.get("after") is not None:
                pyxel.text(90, 241, f"{d[:8]} HP", 7)
                pyxel.text(90, 253, f"{e['before']} -> {e['after']}", col)
            else:
                pyxel.text(90, 247, e["detail"][:35], 6)

            pyxel.text(10, 270, e["detail"][:44], 6)
            if self.ei > 0:
                pyxel.text(10, 282, "PREV " + self.short(self.events[self.ei - 1])[:38], 5)
            return

        pyxel.text(10, 208, f"TURN {self.turn} RESULT", 10)
        pyxel.text(151, 208, f"OUT {self.dealt} / IN {self.taken}", 10)
        pyxel.text(10, 221, "DAMAGE BY UNIT", 6)

        contrib = self.contribution_lines()
        for i, line in enumerate(contrib[:4]):
            x = 10 + (i % 2) * 118
            y = 233 + (i // 2) * 12
            pyxel.text(x, y, line, 10)

        incoming = self.incoming_lines()
        pyxel.text(10, 260, "ENEMY HIT", 8 if incoming else 5)
        pyxel.text(65, 260, " / ".join(incoming[:3])[:42] if incoming else "NONE", 8 if incoming else 5)

        pyxel.text(10, 276, "D/H/S/G badges remain on each unit for this turn.", 5)

    def draw_popup(self, cx, y, text, color):
        w = self.big_w(text, 2)
        x = max(2, min(252 - w, int(cx - w / 2)))
        pyxel.rect(x - 4, y - 4, w + 8, 19, 0)
        self.big_text(x + 1, y + 1, text, 0, 2)
        self.big_text(x, y, text, color, 2)

    def draw_fx(self, e):
        a, b = self.pos(e["s"]), self.pos(e["d"])
        if not a or not b:
            return

        k = e["k"]
        col = 8 if k == "DAMAGE" else 11 if k == "HEAL" else 10
        phase = min(1.0, self.tick / max(1, EVENT_FRAMES - 1))

        if a != b:
            pyxel.line(a[0], a[1], b[0], b[1], col)
            px = int(a[0] + (b[0] - a[0]) * phase)
            py = int(a[1] + (b[1] - a[1]) * phase)
            pyxel.circ(px, py, 2, col)

        if 5 <= self.tick <= 13:
            shake = 1 if self.tick % 2 == 0 else -1
            if e["d"] == "BOSS":
                pyxel.rectb(5 + shake, 5, 246, 49, col)
                pyxel.rectb(6 + shake, 6, 244, 47, col)
            else:
                q = self.cell_rect(e["d"])
                if q:
                    pyxel.rectb(q[0] + shake - 2, q[1] - 2, q[2] + 4, q[3] + 4, col)

        if k not in ("DAMAGE", "HEAL", "SUPPORT", "GUARD"):
            return

        prefix = "-" if k in ("DAMAGE", "GUARD") else "+"
        txt = prefix + str(e["n"])

        if e["d"] == "BOSS":
            self.draw_popup(199, 29, txt, col)
            tag = "DMG" if k == "DAMAGE" else "EFFECT"
            pyxel.text(222, 43, tag, col)
        else:
            q = self.cell_rect(e["d"])
            if not q:
                return
            cx = q[0] + q[2] // 2
            y = q[1] + 8
            self.draw_popup(cx, y, txt, col)
            tag = "DMG" if k == "DAMAGE" else "HEAL" if k == "HEAL" else "SUP" if k == "SUPPORT" else "BLOCK"
            pyxel.rect(q[0] + 2, q[1] + 18, len(tag) * 4 + 4, 8, 0)
            pyxel.text(q[0] + 4, q[1] + 19, tag, col)
