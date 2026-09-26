"""Headless checks of action playback; no Pyxel window required."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch

stub = types.ModuleType('pyxel')
stub.init = stub.mouse = stub.run = lambda *args, **kwargs: None
stub.btnp = lambda *args: False
stub.__getattr__ = lambda name: 0
spec = importlib.util.spec_from_file_location('battle', Path(__file__).parents[1] / 'main.py')
battle = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, pyxel=stub):
    spec.loader.exec_module(battle)


class PlaybackTests(unittest.TestCase):
    def game(self, boss=0):
        g = battle.Game()
        g.boss_index = boss
        g.reset_battle()
        return g

    def finish(self, g):
        while g.state == 'PLAYBACK':
            g.advance_event()

    def test_first_turn_has_all_sources_targets_and_amounts(self):
        g = self.game()
        g.resolve_turn()
        self.assertEqual([(e['source'], e['target'], e['kind'], e['amount']) for e in g.events], [
            ('M', 'A', 'SUPPORT', 10), ('A', 'BOSS', 'DAMAGE', 30),
            ('G', 'B', 'SUPPORT', 6), ('B', 'BOSS', 'DAMAGE', 28),
            ('C', 'BOSS', 'DAMAGE', 14), ('R', 'BOSS', 'DAMAGE', 18),
            ('BOSS', 'B', 'DAMAGE', 16), ('S', 'B', 'HEAL', 4)])
        self.assertEqual(g.boss_hp, 700)  # support is not a hit
        g.advance_event()
        self.assertEqual(g.boss_hp, 670)
        self.finish(g)
        self.assertEqual((g.boss_hp, g.units['B'].hp, g.turn_damage), (610, 43, 90))

    def test_pause_and_final_transition(self):
        g = self.game()
        g.resolve_turn()
        g.paused = True
        before = g.snapshot()
        for _ in range(100):
            g.update_playback()
        self.assertEqual(g.snapshot(), before)
        self.assertEqual(g.event_index, 0)
        g.paused = False
        for _ in range(40):
            g.update_playback()
        self.assertEqual(g.event_index, 1)
        self.finish(g)
        self.assertEqual(g.state, 'DECISION')

    def test_replay_results_match_calculation_for_each_boss(self):
        for boss in range(3):
            g, reference = self.game(boss), self.game(boss)
            for turn in range(40):
                if turn:
                    for obj in (g, reference):
                        if turn % 3:
                            obj.rotate()
                        obj.turn += 1
                reference.calculate_turn()
                g.resolve_turn()
                self.finish(g)
                self.assertEqual(g.snapshot(), reference.snapshot())
                self.assertEqual(g.state, reference.state)
                if g.state in ('WIN', 'LOSE'):
                    break
            self.assertIn(g.state, ('WIN', 'LOSE'))

    def test_history_and_reset_do_not_reapply_damage(self):
        g = self.game()
        g.resolve_turn()
        self.finish(g)
        before = g.snapshot()
        for index in range(len(g.events)):
            g.event_index = index
            g.update()
        self.assertEqual(g.snapshot(), before)
        g.reset_battle()
        self.assertEqual(g.events, [])
        self.assertEqual(g.event_index, -1)
        self.assertEqual(g.boss_hp, 700)


if __name__ == '__main__':
    unittest.main()
