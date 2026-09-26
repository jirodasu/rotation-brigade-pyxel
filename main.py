import pyxel

W = 256
H = 256

FRONT, MIDDLE, BACK = 0, 1, 2
ROWS = ["FRONT", "MIDDLE", "BACK"]


class Unit:
    def __init__(self, key, name, hp, front_atk, back_heal=0, mid_kind=None, mid_value=0):
        self.key = key
        self.name = name
        self.max_hp = hp
        self.hp = hp
        self.front_atk = front_atk
        self.back_heal = back_heal
        self.mid_kind = mid_kind
        self.mid_value = mid_value
        self.mid_ready = True

    @property
    def alive(self):
        return self.hp > 0

    def reset(self):
        self.hp = self.max_hp
        self.mid_ready = True


BOSS_DATA = [
    {
        "name": "GOLM",
        "hp": 700,
        "desc": "WHO TAKES THE HIT?",
        "pattern": [
            ("NORMAL", 16, "low"),
            ("NORMAL", 16, "low"),
            ("SMASH", 36, "low"),
            ("NORMAL", 16, "low"),
            ("CHARGE", 0, "none"),
            ("CRUSH", 46, "low"),
        ],
    },
    {
        "name": "VALGA",
        "hp": 660,
        "desc": "HOW MANY IN FRONT?",
        "pattern": [
            ("CLAW", 12, "low"),
            ("WING", 12, "aoe"),
            ("DIVE", 22, "high"),
            ("GALE", 18, "aoe"),
            ("FLY HIGH", 0, "none"),
            ("BREATH", 46, "aoe"),
        ],
    },
    {
        "name": "CALCITE",
        "hp": 400,
        "desc": "TIME YOUR DAMAGE",
        "pattern": [
            ("CRYSTAL", 16, "low"),
            ("PRESS", 22, "low"),
            ("CORE OPEN", 0, "none"),
            ("CRYSTAL", 16, "low"),
            ("PRESS+", 28, "low"),
            ("CORE OPEN", 0, "none"),
        ],
        "deadline": 15,
    },
]


class Game:
    def __init__(self):
        pyxel.init(W, H, title="ROTATION BRIGADE")
        pyxel.mouse(True)
        self.units = {
            "A": Unit("A", "ALLEN", 60, 20, 16),
            "B": Unit("B", "BELL", 55, 22, 14),
            "C": Unit("C", "CLAUDE", 75, 14, 20, "DEF", 10),
            "M": Unit("M", "MIRA", 48, 12, 12, "ATK", 10),
            "S": Unit("S", "SERA", 75, 8, 0, "DEF", 6),
            "R": Unit("R", "RAIN", 50, 14, 10, "RANGED", 18),
            "G": Unit("G", "GALD", 55, 17, 16, "ATK", 6),
        }
        self.boss_index = 0
        self.state = "TITLE"
        self.select = 0
        self.log = []
        self.turn = 1
        self.boss_hp = 1
        self.boss_max_hp = 1
        self.formation = [[None] * 4 for _ in range(3)]
        self.run()

    def run(self):
        pyxel.run(self.update, self.draw)

    def reset_battle(self):
        for u in self.units.values():
            u.reset()
        self.formation = [
            ["A", "B", "C", None],
            ["M", "G", None, "R"],
            [None, "S", None, None],
        ]
        boss = BOSS_DATA[self.boss_index]
        self.boss_hp = boss["hp"]
        self.boss_max_hp = boss["hp"]
        self.turn = 1
        self.select = 0
        self.state = "READY"
        self.log = ["PRESS Z / TAP START"]

    def update(self):
        if self.state == "TITLE":
            self.update_title()
        elif self.state == "READY":
            if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN) or self.clicked(88, 226, 80, 22):
                self.resolve_turn()
        elif self.state == "DECISION":
            if pyxel.btnp(pyxel.KEY_LEFT) or pyxel.btnp(pyxel.KEY_A):
                self.select = 0
            if pyxel.btnp(pyxel.KEY_RIGHT) or pyxel.btnp(pyxel.KEY_D):
                self.select = 1
            if self.clicked(16, 226, 102, 22):
                self.select = 0
                self.commit_decision()
            elif self.clicked(138, 226, 102, 22):
                self.select = 1
                self.commit_decision()
            elif pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN):
                self.commit_decision()
        elif self.state in ("WIN", "LOSE"):
            if pyxel.btnp(pyxel.KEY_R) or pyxel.btnp(pyxel.KEY_Z) or self.clicked(73, 226, 110, 22):
                self.reset_battle()
            if pyxel.btnp(pyxel.KEY_X):
                self.state = "TITLE"
        if pyxel.btnp(pyxel.KEY_Q):
            pyxel.quit()

    def update_title(self):
        if pyxel.btnp(pyxel.KEY_UP):
            self.boss_index = (self.boss_index - 1) % len(BOSS_DATA)
        if pyxel.btnp(pyxel.KEY_DOWN):
            self.boss_index = (self.boss_index + 1) % len(BOSS_DATA)
        for i in range(3):
            y = 92 + i * 35
            if self.clicked(38, y, 180, 27):
                self.boss_index = i
                self.reset_battle()
                return
        if pyxel.btnp(pyxel.KEY_Z) or pyxel.btnp(pyxel.KEY_RETURN):
            self.reset_battle()

    def clicked(self, x, y, w, h):
        return (
            pyxel.btnp(pyxel.MOUSE_BUTTON_LEFT)
            and x <= pyxel.mouse_x < x + w
            and y <= pyxel.mouse_y < y + h
        )

    def commit_decision(self):
        if self.select == 0:
            self.rotate()
            self.log = ["ROTATE"]
        else:
            self.log = ["STAY"]
        self.turn += 1
        self.resolve_turn()

    def rotate(self):
        old = [row[:] for row in self.formation]
        self.formation[FRONT] = old[MIDDLE]
        self.formation[MIDDLE] = old[BACK]
        self.formation[BACK] = old[FRONT]
        # Entering middle refreshes one-shot support.
        for c in range(4):
            key = self.formation[MIDDLE][c]
            if key is not None and old[MIDDLE][c] != key:
                self.units[key].mid_ready = True

    def resolve_turn(self):
        if self.state in ("WIN", "LOSE"):
            return
        self.log = []
        total = self.ally_phase()
        if self.boss_hp <= 0:
            self.boss_hp = 0
            self.state = "WIN"
            self.log.append("BOSS DOWN!")
            return

        if self.front_count() == 0:
            self.state = "LOSE"
            self.log.append("FRONT LINE BROKEN")
            return

        self.enemy_phase()
        self.cleanup_dead()
        if self.alive_count() == 0 or self.front_count() == 0:
            self.state = "LOSE"
            self.log.append("PARTY DOWN")
            return

        self.back_phase()
        self.cleanup_dead()

        boss = BOSS_DATA[self.boss_index]
        if boss.get("deadline") and self.turn >= boss["deadline"] and self.boss_hp > 0:
            self.state = "LOSE"
            self.log.append("FULL CRYSTALLIZE")
            return

        self.log.insert(0, f"PARTY DMG {total}")
        self.state = "DECISION"
        self.select = 0

    def ally_phase(self):
        total = 0
        mult = 1.0
        if self.boss_index == 2 and self.turn % 3 != 0:
            mult = 0.2

        for c in range(4):
            fkey = self.formation[FRONT][c]
            mkey = self.formation[MIDDLE][c]
            if fkey is not None and self.units[fkey].alive:
                front = self.units[fkey]
                dmg = front.front_atk
                if mkey is not None:
                    mid = self.units[mkey]
                    if mid.alive and mid.mid_kind == "ATK" and mid.mid_ready:
                        dmg += mid.mid_value
                        mid.mid_ready = False
                        self.log.append(f"{mid.name} ATK+{mid.mid_value}")
                dealt = max(1, int(round(dmg * mult)))
                self.boss_hp -= dealt
                total += dealt
            elif mkey is not None:
                mid = self.units[mkey]
                if mid.alive and mid.mid_kind == "RANGED":
                    dealt = max(1, int(round(mid.mid_value * mult)))
                    self.boss_hp -= dealt
                    total += dealt
        return total

    def enemy_phase(self):
        name, power, kind = self.current_enemy_action()
        self.log.append(f"ENEMY {name}")
        if power <= 0 or kind == "none":
            return

        fronts = []
        for c, key in enumerate(self.formation[FRONT]):
            if key is not None and self.units[key].alive:
                fronts.append((c, self.units[key]))
        if not fronts:
            return

        if kind == "aoe":
            for c, unit in fronts:
                self.apply_enemy_damage(c, unit, power)
        elif kind == "high":
            c, unit = max(fronts, key=lambda x: (x[1].hp, -x[0]))
            self.apply_enemy_damage(c, unit, power)
        else:
            c, unit = min(fronts, key=lambda x: (x[1].hp, x[0]))
            self.apply_enemy_damage(c, unit, power)

    def apply_enemy_damage(self, col, target, power):
        reduction = 0
        mkey = self.formation[MIDDLE][col]
        if mkey is not None:
            mid = self.units[mkey]
            if mid.alive and mid.mid_kind == "DEF" and mid.mid_ready:
                reduction = mid.mid_value
                mid.mid_ready = False
                self.log.append(f"{mid.name} DEF-{reduction}")
        dmg = max(1, power - reduction)
        target.hp -= dmg
        self.log.append(f"{target.name} -{dmg}")

    def back_phase(self):
        for c in range(4):
            bkey = self.formation[BACK][c]
            if bkey is None:
                continue
            back = self.units[bkey]
            if not back.alive:
                continue
            if bkey == "S":
                for r in (FRONT, MIDDLE):
                    key = self.formation[r][c]
                    if key is not None and self.units[key].alive:
                        u = self.units[key]
                        old = u.hp
                        u.hp = min(u.max_hp, u.hp + 4)
                        if u.hp > old:
                            self.log.append(f"SERA HEAL {u.name}+{u.hp-old}")
            elif back.back_heal > 0:
                old = back.hp
                back.hp = min(back.max_hp, back.hp + back.back_heal)
                if back.hp > old:
                    self.log.append(f"{back.name} +{back.hp-old}")

    def cleanup_dead(self):
        for r in range(3):
            for c in range(4):
                key = self.formation[r][c]
                if key is not None and not self.units[key].alive:
                    self.formation[r][c] = None

    def current_enemy_action(self):
        boss = BOSS_DATA[self.boss_index]
        return boss["pattern"][(self.turn - 1) % len(boss["pattern"])]

    def next_enemy_action(self, offset=1):
        boss = BOSS_DATA[self.boss_index]
        t = self.turn + offset
        return boss["pattern"][(t - 1) % len(boss["pattern"])]

    def alive_count(self):
        return sum(1 for u in self.units.values() if u.alive)

    def front_count(self):
        return sum(1 for key in self.formation[FRONT] if key is not None and self.units[key].alive)

    def draw(self):
        pyxel.cls(1)
        if self.state == "TITLE":
            self.draw_title()
        else:
            self.draw_battle()

    def draw_title(self):
        pyxel.text(74, 24, "ROTATION BRIGADE", 10)
        pyxel.text(55, 38, "FORMATION BATTLE PROTOTYPE", 6)
        pyxel.text(64, 60, "CHOOSE A BOSS", 7)
        for i, boss in enumerate(BOSS_DATA):
            y = 92 + i * 35
            active = i == self.boss_index
            pyxel.rect(38, y, 180, 27, 5 if active else 2)
            pyxel.rectb(38, y, 180, 27, 10 if active else 6)
            pyxel.text(47, y + 5, f"{i+1}. {boss['name']}", 10 if active else 7)
            pyxel.text(47, y + 15, boss["desc"], 6)
        pyxel.text(59, 214, "UP/DOWN + Z  /  TAP", 5)

    def draw_battle(self):
        boss = BOSS_DATA[self.boss_index]
        pyxel.text(6, 5, f"{boss['name']}  T{self.turn}", 10)
        pyxel.text(172, 5, f"ALIVE {self.alive_count()}/7", 7)
        self.draw_bar(6, 16, 244, 7, self.boss_hp, self.boss_max_hp, 8, 2)
        pyxel.text(8, 26, f"HP {self.boss_hp}/{self.boss_max_hp}", 7)

        # Enemy forecast
        pyxel.rect(6, 36, 244, 35, 0)
        pyxel.rectb(6, 36, 244, 35, 5)
        pyxel.text(10, 40, "ENEMY PLAN", 6)
        for i in range(3):
            if i == 0:
                name, pwr, kind = self.current_enemy_action()
                t = self.turn
            else:
                name, pwr, kind = self.next_enemy_action(i)
                t = self.turn + i
            extra = " ALL" if kind == "aoe" else ""
            pyxel.text(10 + i * 79, 52, f"T{t} {name}", 10 if i == 0 else 7)
            pyxel.text(10 + i * 79, 61, f"DMG {pwr}{extra}", 8 if pwr >= 36 else 6)

        # Formation grid
        gx, gy = 8, 81
        cell_w, cell_h = 57, 34
        for r in range(3):
            pyxel.text(8, gy + r * cell_h + 11, ROWS[r][0], 6)
            for c in range(4):
                x = 18 + c * cell_w
                y = gy + r * cell_h
                pyxel.rect(x, y, 52, 29, 0)
                pyxel.rectb(x, y, 52, 29, 13 if r == FRONT else (9 if r == MIDDLE else 12))
                key = self.formation[r][c]
                if key is None:
                    pyxel.text(x + 20, y + 11, "--", 5)
                    continue
                u = self.units[key]
                pyxel.text(x + 3, y + 3, u.name[:6], 7)
                hp_col = 8 if u.hp <= u.max_hp * 0.35 else 11
                pyxel.text(x + 3, y + 12, f"{max(0,u.hp):02}/{u.max_hp:02}", hp_col)
                if r == MIDDLE and u.mid_kind:
                    flag = "R" if u.mid_ready else "x"
                    pyxel.text(x + 37, y + 20, flag, 10 if u.mid_ready else 5)
                self.draw_bar(x + 3, y + 22, 32, 3, max(0, u.hp), u.max_hp, 11, 2)

        # Calcite armor status
        if self.boss_index == 2:
            status = "CORE OPEN x1.0" if self.turn % 3 == 0 else "ARMOR x0.2"
            pyxel.text(167, 185, status, 10 if self.turn % 3 == 0 else 6)

        # Log
        pyxel.rect(6, 186, 156, 35, 0)
        pyxel.rectb(6, 186, 156, 35, 5)
        for i, line in enumerate(self.log[:4]):
            pyxel.text(10, 190 + i * 7, line[:24], 7 if i == 0 else 6)

        if self.state == "READY":
            self.button(88, 226, 80, 22, "START", True)
        elif self.state == "DECISION":
            self.button(16, 226, 102, 22, "ROTATE", self.select == 0)
            self.button(138, 226, 102, 22, "STAY", self.select == 1)
        elif self.state == "WIN":
            pyxel.rect(55, 91, 146, 52, 0)
            pyxel.rectb(55, 91, 146, 52, 10)
            pyxel.text(104, 102, "VICTORY", 10)
            pyxel.text(77, 116, f"TURN {self.turn} / ALIVE {self.alive_count()}", 7)
            pyxel.text(67, 130, "R OR TAP TO RETRY", 6)
            self.button(73, 226, 110, 22, "RETRY", True)
        elif self.state == "LOSE":
            pyxel.rect(55, 91, 146, 52, 0)
            pyxel.rectb(55, 91, 146, 52, 8)
            pyxel.text(108, 102, "DEFEAT", 8)
            pyxel.text(77, 116, f"TURN {self.turn} / ALIVE {self.alive_count()}", 7)
            pyxel.text(67, 130, "R OR TAP TO RETRY", 6)
            self.button(73, 226, 110, 22, "RETRY", True)

    def button(self, x, y, w, h, label, active):
        pyxel.rect(x, y, w, h, 5 if active else 2)
        pyxel.rectb(x, y, w, h, 10 if active else 6)
        tw = len(label) * 4
        pyxel.text(x + (w - tw) // 2, y + 8, label, 10 if active else 7)

    def draw_bar(self, x, y, w, h, value, maximum, fg, bg):
        pyxel.rect(x, y, w, h, bg)
        if maximum > 0:
            fill = int(w * max(0, value) / maximum)
            pyxel.rect(x, y, fill, h, fg)
        pyxel.rectb(x, y, w, h, 7)


Game()
