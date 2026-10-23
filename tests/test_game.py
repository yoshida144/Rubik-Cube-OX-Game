"""Logic checks and real Tkinter interaction checks (use Xvfb in CI)."""
import copy
import os
import random
import sys
import tempfile
import tkinter as tk
import unittest
from types import SimpleNamespace

from constants import ALL_MOVES, FACE_KEYS
from game_logic import GameLogic
from game_scene import AIPlayer, CubeTicTacToeScene


class LogicTests(unittest.TestCase):
    def test_ai_simulation_uses_same_moves_without_mutation(self):
        game = GameLogic()
        for f in FACE_KEYS:
            game.marker_state[f] = [[f'{f}{r}{c}' for c in range(3)] for r in range(3)]
        original = copy.deepcopy(game.marker_state)
        for move in ALL_MOVES:
            expected = GameLogic()
            expected.marker_state = copy.deepcopy(original)
            expected.rotate(move)
            self.assertEqual(AIPlayer().simulate_rotation(original, move), expected.marker_state)
            self.assertEqual(game.marker_state, original)

    def test_win_and_block(self):
        game = GameLogic()
        game.marker_state['F'][0] = ['O', 'O', None]
        ai = AIPlayer()
        self.assertEqual(ai.find_winning_or_blocking_move('O', game.marker_state), (0, 2))
        self.assertFalse(ai.check_win_on_board(game.marker_state['F'], 'O'))
        game.marker_state['F'][0][2] = 'O'
        self.assertTrue(ai.check_win_on_board(game.marker_state['F'], 'O'))


@unittest.skipUnless(os.environ.get('DISPLAY') or os.name == 'nt' or sys.platform == 'darwin', 'requires a display (Linux: Xvfb)')
class DesktopTests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.geometry('1200x1000')
        self.scene = CubeTicTacToeScene(self.root)
        self.root.update()
        self.scene.frame()

    def tearDown(self):
        self.scene.cancel_delays()
        self.root.destroy()

    def click(self, rectangle):
        point = rectangle.center()
        self.scene.canvas.event_generate('<Button-1>', x=round(point.x), y=round(self.scene.size.h - point.y))
        self.root.update()
        self.scene.frame()

    def start(self, mode='2P', custom=False):
        self.click(self.scene.custom_mode_button_rect if custom else self.scene.normal_mode_button_rect)
        self.assertEqual(self.scene.game_phase, 'player_selection')
        self.click({'AI': self.scene.ai_button_rect, '2P': self.scene.twoplayer_button_rect,
                    '3P': self.scene.threeplayer_button_rect}[mode])
        self.assertEqual(self.scene.game_phase, 'rules')
        self.click(self.scene.rules_start_button_rect)
        self.assertEqual(self.scene.game_phase, 'playing')
        self.assertGreater(len(self.scene.canvas.find_all()), 50)

    def click_cell(self, face, row, col):
        x, y = self.scene._get_pixel_coords((face, row, col))
        from desktop_scene import Rect
        self.click(Rect(x - 1, y - 1, 2, 2))

    def test_normal_placement_rotation_and_win(self):
        self.start()
        self.click_cell('F', 0, 0)
        self.assertEqual(self.scene.game.marker_state['F'][0][0], 'O')
        self.assertEqual(self.scene.current_player, 'X')
        self.click(self.scene.buttons[('left', 0)])
        self.assertEqual(self.scene.current_player, 'O')
        self.scene.game.marker_state['F'][2] = ['O', 'O', None]
        self.click_cell('F', 2, 2)
        self.assertTrue(self.scene.game_over)
        self.assertEqual(self.scene.winner, 'O')

    def test_main_entry_point(self):
        import subprocess
        import sys
        from pathlib import Path
        code = """
import sys
sys.path.insert(0, sys.argv[1])
import main
from game_scene import CubeTicTacToeScene
original = CubeTicTacToeScene.run
def short_run(scene):
    scene.root.after(250, scene.root.destroy)
    original(scene)
CubeTicTacToeScene.run = short_run
raise SystemExit(main.main())
"""
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-B', '-c', code,
                                     str(Path(__file__).resolve().parents[1])],
                                    cwd=directory, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn('Traceback', result.stderr)

    def test_three_players(self):
        self.start('3P')
        for col, marker in enumerate(('O', 'X', '△')):
            self.click_cell('F', 0, col)
            self.assertEqual(self.scene.game.marker_state['F'][0][col], marker)
        self.assertEqual(self.scene.current_player, 'O')

    def test_ai_scheduled_and_reset_cancels_callbacks(self):
        self.start('AI')
        self.click_cell('F', 0, 0)
        self.assertTrue(self.scene.pending)
        self.root.after(650, self.root.quit)
        self.root.mainloop()
        self.assertEqual(self.scene.current_player, 'O')
        self.assertEqual(sum(cell == 'X' for b in self.scene.game.marker_state.values() for row in b for cell in row), 1)
        self.click_cell('F', 1, 0)
        self.click(self.scene.back_button_rect)
        self.assertFalse(self.scene.pending)
        self.assertEqual(self.scene.game_phase, 'player_selection')

    def test_custom_eggs_and_kaiju_animation(self):
        random.seed(7)
        self.start('3P', custom=True)
        occupied = self.scene.game.kaiju_positions[0]
        self.click_cell(*occupied)
        self.assertEqual(self.scene.current_player, 'O')
        self.scene.game.egg_positions[('B', 0, 0)] = 'golden'
        self.scene._handle_egg_effect(('B', 0, 0))
        self.assertEqual(sum(cell == 'O' for b in self.scene.game.marker_state.values() for row in b for cell in row), 10)
        self.scene._trigger_kaiju_move()
        for _ in range(22):
            self.scene.frame()
        self.assertFalse(self.scene.is_kaiju_animating)
        self.assertTrue(self.scene.game.egg_positions)
        self.assertEqual(self.scene.current_player, 'X')


if __name__ == '__main__':
    unittest.main()
