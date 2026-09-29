"""Headless checks for battle playback and FRONT-only enemy damage."""
from pathlib import Path
from unittest.mock import patch
import importlib.util
import sys
import types
import unittest

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT))

stub = types.ModuleType("pyxel")
stub.init = stub.mouse = stub.run = lambda *args, **kwargs: None
stub.btnp = lambda *args, **kwargs: False
stub.quit = lambda *args, **kwargs: None
stub.__getattr__ = lambda name: 0

with patch.dict(sys.modules, pyxel=stub):
    spec = importlib.util.spec_from_file_location("battle_v4", ROOT / "game_v4.py")
    battle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(battle)


class PlaybackTests(unittest.TestCase):
    def game(self, boss=0):
        g = battle.Game()
        g.bi = boss
        g.reset()
        return g

    def finish(self, g):
        while g.state == "PLAY":
            g.next_event()

    def test_first_turn_sources_targets_amounts_and_hp_delta(self):
        g = self.game(0)
        g.resolve()
        events = [(e["s"], e["d"], e["k"], e["n"]) for e in g.events]
        self.assertEqual(
            events,
            [
                ("M", "A", "SUPPORT", 10),
                ("A", "BOSS", "DAMAGE", 30),
                ("G", "B", "SUPPORT", 6),
                ("B", "BOSS", "DAMAGE", 28),
                ("C", "BOSS", "DAMAGE", 14),
                ("R", "BOSS", "DAMAGE", 18),
                ("BOSS", "B", "DAMAGE", 16),
                ("S", "B", "HEAL", 4),
            ],
        )
        allen_hit = g.events[1]
        self.assertEqual((allen_hit["before"], allen_hit["after"]), (700, 670))
        bell_hit = g.events[6]
        self.assertEqual((bell_hit["before"], bell_hit["after"]), (55, 39))

        self.finish(g)
        self.assertEqual(g.state, "DECISION")
        self.assertEqual((g.bhp, g.u["B"].hp, g.dealt, g.taken), (610, 43, 90, 16))

    def test_valga_front_all_hits_front_row_only(self):
        g = self.game(1)
        g.turn = 2  # WING: FRONT ALL
        front_before = {k: g.u[k].hp for k in ("A", "B", "C")}
        middle_back_before = {k: g.u[k].hp for k in ("M", "G", "R", "S")}

        g.resolve()
        enemy_targets = [
            e["d"] for e in g.events if e["k"] == "DAMAGE" and e["s"] == "BOSS"
        ]
        self.assertEqual(enemy_targets, ["A", "B", "C"])

        self.finish(g)
        for k in ("A", "B", "C"):
            self.assertLess(g.u[k].hp, front_before[k])
        for k in ("M", "G", "R", "S"):
            self.assertEqual(g.u[k].hp, middle_back_before[k])

    def test_playback_reaches_same_final_snapshot_as_direct_calculation(self):
        for boss in range(3):
            replay = self.game(boss)
            direct = self.game(boss)

            direct.calc()
            expected = direct.snap()
            expected_state = direct.state

            replay.resolve()
            self.finish(replay)

            self.assertEqual(replay.snap(), expected)
            self.assertEqual(replay.state, expected_state)

    def test_unit_marks_explain_turn_contribution(self):
        g = self.game(0)
        g.resolve()
        self.finish(g)
        self.assertEqual(g.unit_mark("A"), ("D30", 10))
        self.assertEqual(g.unit_mark("B"), ("H16", 8))
        self.assertEqual(g.unit_mark("M"), ("S10", 10))


if __name__ == "__main__":
    unittest.main()
