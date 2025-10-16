# main.py

# ===================================================================================
# ゲームを起動するためのメインファイルです。
# このファイルを実行すると、`game_scene.py` の `CubeTicTacToeScene` が
# 呼び出されてゲームが開始されます。
# ===================================================================================

import ui
from scene import SceneView
from game_scene import CubeTicTacToeScene

if __name__ == '__main__':
    screen_size = ui.get_screen_size()
    scene_view = SceneView(frame=(0, 0, screen_size.w, screen_size.h))
    scene_view.scene = CubeTicTacToeScene()
    scene_view.name = 'OX game'
    scene_view.present('fullscreen')
