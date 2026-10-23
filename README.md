# Rubik Cube OX Game

ルービックキューブの展開図を使った ○× ゲームです。Pythonista 専用の描画を Tkinter に移植し、通常の Python 3 で実行できるようにしています。

## 起動

Python 3.10 以降と Tkinter が必要です。リポジトリのフォルダで実行します。

```sh
python -m pip install -r requirements.txt
python main.py
```

macOS / Windows では Tkinter を含む Python を使用してください。Ubuntu / Debian で Tkinter がない場合は `sudo apt install python3-tk` を実行します。`python` がない環境では `python3` を使用してください。

写真はスクリプトと同じフォルダから読み込むため、別の作業ディレクトリから `python /path/to/main.py` で起動することもできます。既存の `.pyui` ファイルは不要です。

## 操作

- ノーマルモードまたは怪獣モードを選び、AI・2人・3人対戦を選択します。
- 空いたマスをクリックして配置するか、盤面の外側の矢印をクリックして回転します。
- 中央の F 面で縦・横・斜めに同じマークを3つ揃えると勝利です。
- 怪獣モードでは怪獣のいるマスには配置できません。卵をクリックすると通常5個、金の卵は10個のマークが空きマスに配置されます。
- 左上のボタンでモード選択に戻ります。終了後は盤面をクリックするとタイトルへ戻ります。Esc キーでウィンドウを閉じます。

Pythonista の効果音は Tkinter の通知音に置き換えています。背景画像・怪獣移動・勝利演出は維持していますが、半透明表示は Tkinter の網掛けによる近似です。日本語・絵文字の見え方は OS のフォントに依存します。Linux では日本語フォント（例: Noto Sans CJK JP）の導入を推奨します。

## 検証

```sh
python -B -m unittest discover -s tests -v
```

GUI テストにはディスプレイが必要です。ディスプレイのない Linux では Xvfb をインストールし、次のように実行します。

```sh
xvfb-run -a python -B -m unittest discover -s tests -v
xvfb-run -a python main.py
```

通常の起動にはデスクトップ画面が必要です。画面なしで起動した場合は、対処方法を表示して終了します。
