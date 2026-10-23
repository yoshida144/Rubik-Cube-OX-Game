"""Run the desktop game with ordinary Python 3."""
import sys


def main():
    try:
        import tkinter as tk
        from game_scene import CubeTicTacToeScene
    except ImportError as exc:
        print(f'必要なライブラリがありません: {exc}\n'
              'Pillow: python -m pip install -r requirements.txt\n'
              'Ubuntu/Debian の Tkinter: sudo apt install python3-tk', file=sys.stderr)
        return 1
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        print(f'画面を開けません: {exc}\nデスクトップ環境で実行してください。'
              'ヘッドレス検証には xvfb-run を使用できます。', file=sys.stderr)
        return 1
    root.title('Rubik Cube OX Game')
    root.geometry('1200x1000')
    root.minsize(1120, 960)
    scene = CubeTicTacToeScene(root)
    scene.run()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
