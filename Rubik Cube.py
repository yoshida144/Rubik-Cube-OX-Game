from scene import *
import ui
import random
import copy
import sound
import math

class CubeTicTacToeScene(Scene):
    # --- 初期設定 ---
    def setup(self):
        self.background_color = '#F1F1F1'
        # キューブのタイルの基本色を設定
        neutral_color = (0.8, 0.9, 1.0, 0.7)
        self.COLORS = {
            'U': neutral_color, 'D': neutral_color, 'F': neutral_color,
            'B': neutral_color, 'R': neutral_color, 'L': neutral_color,
        }
        # ゲームで使う定数を定義
        self.FACE_KEYS = ['U', 'L', 'F', 'R', 'B', 'D'] # 各面のキー
        self.ALL_MOVES = ["U", "U'", "D", "D'", "L", "L'", "R", "R'", "F", "F'", "B", "B'", "M", "M'", "E", "E'"] # AIが思考に使う全回転操作
        
        # UIのサイズ関連の変数を定義
        self.tile_size = 45; self.gap = 4; self.face_gap = 15; self.btn_size = 40
        
        # ゲームの状態を管理する変数を初期化
        self.buttons = {}; self.cube_state = {}; self.marker_state = {}
        self.current_player = 'O'; self.game_over = False; self.winner = None
        self.status_message = "Oのターン"
        
        # ゲームの進行状況を管理
        self.game_phase = 'title' # 'title', 'rules', 'playing' のいずれか
        self.game_mode = None     # 'AI', '2P', '3P' のいずれか
        
        # 各画面のボタンの領域を保持する変数
        self.ai_button_rect = None
        self.twoplayer_button_rect = None
        self.threeplayer_button_rect = None
        self.rules_start_button_rect = None
        self.back_button_rect = None
        
        # 勝利時の演出用
        self.victory_particles = []
        self.animation_timer = 0
        
        # ゲーム状態の履歴を保存するリスト
        self.state_history = []
        
        # ゲーム状態をリセットして開始
        self.reset_game()

    # --- ゲーム状態を初期化する関数 ---
    def reset_game(self):
        # キューブの各面の色とマークの状態を空にする
        for key in self.FACE_KEYS:
            self.cube_state[key] = [[self.COLORS[key]] * 3 for _ in range(3)]
            self.marker_state[key] = [[None] * 3 for _ in range(3)]
        
        # ゲーム進行に関する変数を初期状態に戻す
        self.current_player = 'O'; self.game_over = False; self.winner = None
        self.status_message = "Oのターン"; self.victory_particles.clear(); self.animation_timer = 0
        
        # 新しいゲーム開始時に盤面の履歴をクリアし、開始時の盤面を記録
        self.state_history.clear()
        self.state_history.append(self._get_state_snapshot())

    # --- 毎フレーム呼ばれる更新処理 ---
    def update(self):
        # ゲームオーバーの場合、勝利演出のアニメーションを処理する
        if self.game_over:
            self.animation_timer += 1
            if self.winner: # 勝者がいる場合のみパーティクルを動かす
                for particle in self.victory_particles:
                    particle['x'] += particle['vx']; particle['y'] += particle['vy']; particle['vy'] -= 0.2
                # 画面外に出たパーティクルを削除して軽くする
                self.victory_particles = [p for p in self.victory_particles if p['y'] > -50]

    # --- 毎フレーム呼ばれる描画処理のメイン関数 ---
    def draw(self):
        center_x, center_y = self.size.w / 2, self.size.h / 2

        # --- 1. ゲームプレイ中の描画 ---
        if self.game_phase == 'playing':
            tint(1,1,1,1); image('IMG_0473.JPG',0,0,self.size.w,self.size.h)
            fill(0, 0, 0, 0.5); rect(0, 0, self.size.w, self.size.h)
            header_height = 60
            fill(0, 0, 0, 0.7); rect(0, self.size.h - header_height, self.size.w, header_height)
            back_btn_w, back_btn_h = 120, 40
            back_btn_x, back_btn_y = 10, self.size.h - header_height + (header_height - back_btn_h) / 2
            self.back_button_rect = Rect(back_btn_x, back_btn_y, back_btn_w, back_btn_h)
            fill(0.3, 0.3, 0.3, 0.8); rect(*self.back_button_rect)
            self.draw_stylish_text('↩︎ タイトルへ', 'Futura-CondensedMedium', 18, back_btn_x + back_btn_w/2, back_btn_y + back_btn_h/2, 'white')
            self.draw_stylish_text(self.status_message, 'Futura-CondensedMedium', 70, center_x, self.size.h - 30 - header_height / 2, 'white')
            mode_text = 'vs AI' if self.game_mode == 'AI' else ('vs Player' if self.game_mode == '2P' else '3 Players')
            self.draw_stylish_text(mode_text, 'Futura-CondensedMedium', 18, self.size.w - 60, self.size.h - header_height / 2, (0.8, 0.8, 0.8, 1.0))
            face_total_size = self.tile_size * 3 + self.gap * 2
            face_offsets = { 'U': (0, 1), 'L': (-1, 0), 'F': (0, 0), 'R': (1, 0), 'B': (2, 0), 'D': (0, -1) }
            self.face_origins = {}
            for face_key, (offset_x, offset_y) in face_offsets.items():
                origin_x = center_x + offset_x * (face_total_size + self.face_gap) - face_total_size / 2
                origin_y = center_y + offset_y * (face_total_size + self.face_gap) - face_total_size / 2 - 30
                self.face_origins[face_key] = (origin_x, origin_y)
                if face_key == 'F':
                  glow_padding = 5; fill('#00A0FF'); stroke_weight(0)
                  rect(origin_x - glow_padding, origin_y - glow_padding, face_total_size + glow_padding * 2, face_total_size + glow_padding * 2)
                self.draw_face(face_key, origin_x, origin_y, self.marker_state[face_key])
            self.draw_buttons(self.face_origins, face_total_size)

            # ゲームオーバー時の演出
            if self.game_over:
                # ### 追加 ### 画面全体を覆う半透明の黒い四角を描画して背景をぼかす(暗くする)
                fill(0, 0, 0, 0.6)
                rect(0, 0, self.size.w, self.size.h)
                
                scale = 1.0 + math.sin(self.animation_timer * 0.1) * 0.1
                
                # 勝者がいる場合の処理
                if self.winner:
                    win_text = ""
                    text_color = "white"
                    
                    if self.winner == 'X' and self.game_mode == 'AI':
                        win_text = "YOUR LOSE!"
                        text_color = '#AAAAAA'
                    elif self.winner == 'O':
                        win_text = "O WIN!"
                        text_color = 'red'
                    elif self.winner == 'X':
                        win_text = "X WIN!"
                        text_color = 'blue'
                    elif self.winner == '△':
                        win_text = "△ WIN!"
                        text_color = 'green'
                        
                    self.draw_stylish_text(win_text, 'Futura-CondensedExtraBold', 100 * scale, center_x, center_y, text_color)
                    
                    for p in self.victory_particles:
                        text(p['emoji'], 'AppleColorEmoji', 50, p['x'], p['y'])
                
                # 引き分けの場合の処理
                else:
                    draw_text = "DRAW"
                    self.draw_stylish_text(draw_text, 'Futura-CondensedExtraBold', 120 * scale, center_x, center_y, 'white')

        # --- 2. ルール説明画面の描画 ---
        elif self.game_phase == 'rules':
            tint(1,1,1,1); image('IMG_0479.JPG',0,0,self.size.w,self.size.h)
            fill(0, 0, 0, 0.7); rect(0, 0, self.size.w, self.size.h)
            rules = ["ルール説明", " ", "1. 自分のターンにできることは", "   「キューブを回転」か「マークを配置」の", "   どちらか1つです。", " ", "2. 青く光る盤面の上で、自分のマークを", "   縦・横・斜めに3つ揃えると勝利です。", " ", "3. 同じ盤面が3回繰り返されると", "   引き分け(千日手)となります。", " ", "頑張ってね〜!"]
            tint('white'); start_y = center_y + 180
            for i, line in enumerate(rules):
                font_size = 36 if i == 0 else 24; text(line, 'HiraginoSans-W6', font_size, center_x, start_y - i * 38)
            btn_w, btn_h = 300, 80; btn_x, btn_y = center_x - btn_w / 2, center_y - 400
            self.rules_start_button_rect = Rect(btn_x, btn_y, btn_w, btn_h)
            fill(0.1, 0.8, 0.5, 0.8); stroke_weight(3); stroke(0.4, 1.0, 0.8, 1.0); rect(*self.rules_start_button_rect)
            tint('white'); text('ゲーム開始', 'Helvetica-Bold', 40, center_x, btn_y + btn_h/2)
        # --- 3. タイトル画面の描画 ---
        else:
            tint(1,1,1,1); image('IMG_0474.JPG',0,0,self.size.w,self.size.h)
            btn_w, btn_h = 300, 60; btn_spacing = 20
            ai_btn_x = center_x - btn_w / 2; ai_btn_y = center_y - btn_h - btn_spacing
            self.ai_button_rect = Rect(ai_btn_x, ai_btn_y, btn_w, btn_h)
            fill(0.1, 0.5, 0.8, 0.7); stroke_weight(3); stroke(0.4, 0.8, 1.0, 1.0); rect(*self.ai_button_rect)
            tint('white'); text('AIと対戦', 'Helvetica-Bold', 32, center_x, ai_btn_y + btn_h / 2)
            p2_btn_x = center_x - btn_w / 2; p2_btn_y = center_y
            self.twoplayer_button_rect = Rect(p2_btn_x, p2_btn_y, btn_w, btn_h)
            fill(0.8, 0.1, 0.5, 0.7); stroke_weight(3); stroke(1.0, 0.4, 0.8, 1.0); rect(*self.twoplayer_button_rect)
            tint('white'); text('2人で対戦', 'Helvetica-Bold', 32, center_x, p2_btn_y + btn_h / 2)
            p3_btn_x = center_x - btn_w / 2; p3_btn_y = center_y + btn_h + btn_spacing
            self.threeplayer_button_rect = Rect(p3_btn_x, p3_btn_y, btn_w, btn_h)
            fill(0.1, 0.8, 0.5, 0.7); stroke_weight(3); stroke(0.4, 1.0, 0.8, 1.0); rect(*self.threeplayer_button_rect)
            tint('white'); text('3人で対戦', 'Helvetica-Bold', 32, center_x, p3_btn_y + btn_h / 2)
        stroke_weight(1); stroke('grey'); tint(1,1,1,1)

    # --- 影付きの文字を描画する補助関数 ---
    def draw_stylish_text(self, text_str, font_name, font_size, x, y, main_color):
        shadow_offset = 2; tint(0, 0, 0, 0.6)
        text(text_str, font_name, font_size, x + shadow_offset, y - shadow_offset)
        tint(main_color); text(text_str, font_name, font_size, x, y); tint(1, 1, 1, 1)

    # --- キューブの1つの面を描画する関数 ---
    def draw_face(self, face_key, origin_x, origin_y, face_markers):
        face_colors = self.cube_state[face_key]
        for row in range(3):
            for col in range(3):
                color = face_colors[2 - row][col]; fill(color); stroke('#00FFFF'); stroke_weight(2)
                px = origin_x + col * (self.tile_size + self.gap); py = origin_y + row * (self.tile_size + self.gap)
                rect(px, py, self.tile_size, self.tile_size)
                marker = face_markers[2 - row][col]
                if marker:
                    marker_colors = {'O': '#FF0000', 'X': '#0000FF', '△': '#2ECC71'}
                    self.draw_stylish_text(marker, 'Helvetica-Bold', 36, px + self.tile_size/2, py + self.tile_size/2, marker_colors.get(marker, 'black'))

    # --- 回転用矢印ボタンを描画する関数 ---
    def draw_buttons(self, face_origins, face_size):
        self.buttons.clear(); btn_padding = self.btn_size/2 + 10
        arrow_font = 'Helvetica-Bold'; arrow_size = 28
        player_colors = {'O': '#C0392B', 'X': '#2980B9', '△': '#27AE60'}
        button_color = player_colors.get(self.current_player, '#808080')
        button_positions = {}
        u_origin_x, u_origin_y = face_origins['U']; d_origin_x, d_origin_y = face_origins['D']
        for i in range(3):
            px = u_origin_x + i * (self.tile_size + self.gap) + self.tile_size / 2
            button_positions[('top', i)] = (px, u_origin_y + face_size + btn_padding, '↓')
            button_positions[('bottom', i)] = (px, d_origin_y - btn_padding, '↑')
        l_origin_x, l_origin_y = face_origins['L']; b_origin_x, b_origin_y = face_origins['B']
        for i in range(3):
            py = l_origin_y + i * (self.tile_size + self.gap) + self.tile_size / 2
            button_positions[('left', 2-i)] = (l_origin_x - btn_padding, py, '→')
            button_positions[('right', 2-i)] = (b_origin_x + face_size + btn_padding, py, '←')
        for key, (px, py, arrow) in button_positions.items():
            self.buttons[key] = Rect(px - self.btn_size/2, py - self.btn_size/2, self.btn_size, self.btn_size)
            stroke_weight(0); fill(button_color); ellipse(px - self.btn_size/2, py - self.btn_size/2, self.btn_size, self.btn_size)
            tint('white'); text(arrow, arrow_font, arrow_size, px, py); tint(1, 1, 1, 1)

    # --- 画面がタッチされた時の処理 ---
    def touch_began(self, touch):
        # 1. ゲームプレイ中のタッチ処理
        if self.game_phase == 'playing':
            if self.back_button_rect and touch.location in self.back_button_rect:
                self.game_phase = 'title'; self.reset_game(); return
            if self.game_over:
                f_face_rect = Rect(self.face_origins['F'][0], self.face_origins['F'][1], self.tile_size * 3 + self.gap * 2, self.tile_size * 3 + self.gap * 2)
                if touch.location in f_face_rect: self.game_phase = 'title'; self.reset_game()
                return
            if self.game_mode == 'AI' and self.current_player == 'X': return
            action_taken = False
            for key, rect_val in self.buttons.items():
                if touch.location in rect_val:
                    bank, index = key; self.handle_rotate(bank, index); action_taken = True; break
            if not action_taken:
                for face_key, (origin_x, origin_y) in self.face_origins.items():
                    face_rect = Rect(origin_x, origin_y, self.tile_size * 3 + self.gap * 2, self.tile_size * 3 + self.gap * 2)
                    if touch.location in face_rect:
                        col = int((touch.location.x - origin_x) / (self.tile_size + self.gap)); row = int((touch.location.y - origin_y) / (self.tile_size + self.gap))
                        if self.marker_state[face_key][2-row][col] is None:
                            self.marker_state[face_key][2-row][col] = self.current_player; action_taken = True
                        break
            if action_taken: self.end_turn()
        # 2. ルール説明画面のタッチ処理
        elif self.game_phase == 'rules':
            if self.rules_start_button_rect and touch.location in self.rules_start_button_rect:
                self.game_phase = 'playing'; self.reset_game()
        # 3. タイトル画面のタッチ処理
        else:
            if self.ai_button_rect and touch.location in self.ai_button_rect:
                self.game_mode = 'AI'; self.game_phase = 'rules'
            elif self.twoplayer_button_rect and touch.location in self.twoplayer_button_rect:
                self.game_mode = '2P'; self.game_phase = 'rules'
            elif self.threeplayer_button_rect and touch.location in self.threeplayer_button_rect:
                self.game_mode = '3P'; self.game_phase = 'rules'

    # --- ターン終了時の処理 ---
    def end_turn(self):
        self.check_win()
        if self.game_over: return
        
        # 千日手判定
        current_snapshot = self._get_state_snapshot()
        self.state_history.append(current_snapshot)
        if self.state_history.count(current_snapshot) >= 3:
            self.handle_draw(); return
        
        # プレイヤー交代
        if self.game_mode == '3P':
            if self.current_player == 'O': self.current_player = 'X'
            elif self.current_player == 'X': self.current_player = '△'
            else: self.current_player = 'O'
        else:
            self.current_player = 'X' if self.current_player == 'O' else 'O'
        
        # AIのターンならAIを呼び出す
        if self.game_mode == 'AI' and self.current_player == 'X':
            self.status_message = "AI 考え中... 🤔"
            self.delay(0.5, self.ai_make_move)
        else:
            self.status_message = f"{self.current_player}のターン"
    
    # --- 引き分け(千日手)発生時の処理 ---
    def handle_draw(self):
        self.game_over = True; self.winner = None
        self.status_message = "引き分け (千日手)"; sound.play_effect('game:Error')
    
    # --- 現在の盤面状態を比較可能なタプルとして取得する関数 ---
    def _get_state_snapshot(self):
        sorted_face_keys = sorted(self.FACE_KEYS)
        marker_tuples = []; cube_state_tuples = []
        for key in sorted_face_keys:
            marker_face_tuple = tuple(tuple(row) for row in self.marker_state[key])
            marker_tuples.append(marker_face_tuple)
            cube_face_tuple = tuple(tuple(row) for row in self.cube_state[key])
            cube_state_tuples.append(cube_face_tuple)
        return (tuple(marker_tuples), tuple(cube_state_tuples))

    # --- AIの思考ルーチン ---
    def ai_make_move(self, *args):
        if self.game_over: return
        # 優先度1A: F面に置けば勝てるか?
        move = self.find_winning_or_blocking_move('X', self.marker_state)
        if move: self.marker_state['F'][move[0]][move[1]] = 'X'; self.end_turn(); return
        # 優先度1B: 回転すれば勝てるか?
        for rotation in self.ALL_MOVES:
            simulated_state = self.simulate_rotation(self.marker_state, rotation)
            if self.check_win_on_board(simulated_state['F'], 'X'): self.rotate(rotation); self.end_turn(); return
        # 優先度2A: F面に置かないと負けるか?
        move = self.find_winning_or_blocking_move('O', self.marker_state)
        if move: self.marker_state['F'][move[0]][move[1]] = 'X'; self.end_turn(); return
        # 優先度2B: 相手が回転すると勝つのを防ぐ
        for rotation in self.ALL_MOVES:
            simulated_state = self.simulate_rotation(self.marker_state, rotation)
            blocking_move = self.find_winning_or_blocking_move('O', simulated_state)
            if blocking_move:
                original_pos = self.find_original_position(blocking_move, rotation)
                if original_pos and self.marker_state[original_pos[0]][original_pos[1]][original_pos[2]] is None:
                    self.marker_state[original_pos[0]][original_pos[1]][original_pos[2]] = 'X'; self.end_turn(); return
        # 優先度3: 回転してリーチを作る
        for rotation in self.ALL_MOVES:
            simulated_state = self.simulate_rotation(self.marker_state, rotation)
            if self.find_winning_or_blocking_move('X', simulated_state): self.rotate(rotation); self.end_turn(); return
        # 優先度4: F面の中央が空いていれば取る
        if self.marker_state['F'][1][1] is None: self.marker_state['F'][1][1] = 'X'; self.end_turn(); return
        # 優先度5: F面の角が空いていればランダムで取る
        corners = [(0, 0), (0, 2), (2, 0), (2, 2)]; random.shuffle(corners)
        for r, c in corners:
            if self.marker_state['F'][r][c] is None: self.marker_state['F'][r][c] = 'X'; self.end_turn(); return
        # 優先度6: 残りの空きマスにランダムで置く
        empty_cells = []
        for face_key in self.FACE_KEYS:
            for r in range(3):
                for c in range(3):
                    if self.marker_state[face_key][r][c] is None: empty_cells.append((face_key, r, c))
        if empty_cells: face, r, c = random.choice(empty_cells); self.marker_state[face][r][c] = 'X'; self.end_turn()

    # --- F面上でリーチになっている箇所を探すAI用関数 ---
    def find_winning_or_blocking_move(self, marker, state):
        board = state['F']
        lines = [((0,0),(0,1),(0,2)),((1,0),(1,1),(1,2)),((2,0),(2,1),(2,2)),((0,0),(1,0),(2,0)),((0,1),(1,1),(2,1)),((0,2),(1,2),(2,2)),((0,0),(1,1),(2,2)),((0,2),(1,1),(2,0))]
        for line in lines:
            values = [board[r][c] for r, c in line]
            if values.count(marker) == 2 and values.count(None) == 1: return line[values.index(None)]
        return None

    # --- 盤面(3x3)上で指定マークが揃っているか判定する関数 ---
    def check_win_on_board(self, board, marker):
        lines = [[board[0][0],board[0][1],board[0][2]],[board[1][0],board[1][1],board[1][2]],[board[2][0],board[2][1],board[2][2]],[board[0][0],board[1][0],board[2][0]],[board[0][1],board[1][1],board[2][1]],[board[0][2],board[1][2],board[2][2]],[board[0][0],board[1][1],board[2][2]],[board[0][2],board[1][1],board[2][0]]]
        for line in lines:
            if line[0] == marker and line[0] == line[1] == line[2]: return True
        return False
        
    # --- (AI用) 回転後の位置から回転前の位置を逆算する関数 ---
    def find_original_position(self, target_pos, rotation_move):
        inverse_rotations = { "U": "U'", "U'": "U", "D": "D'", "D'": "D", "L": "L'", "L'": "L", "R": "R'", "R'": "R", "F": "F'", "F'": "F", "B": "B'", "B'": "B", "M": "M'", "M'": "M", "E": "E'", "E'": "E" }
        temp_state = {fk: [[None]*3 for _ in range(3)] for fk in self.FACE_KEYS}; temp_state['F'][target_pos[0]][target_pos[1]] = 'TARGET'
        final_state = self.simulate_rotation(temp_state, inverse_rotations[rotation_move])
        for fk in self.FACE_KEYS:
            for r in range(3):
                for c in range(3):
                    if final_state[fk][r][c] == 'TARGET': return (fk, r, c)
        return None

    # --- (AI用) 実際のゲーム状態を変更せずに回転をシミュレーションする関数 ---
    def simulate_rotation(self, original_state, move):
        state = copy.deepcopy(original_state); s = state
        def rotate_face_sim(face_key, clockwise=True):
            face = s[face_key]
            if clockwise: s[face_key] = [list(row) for row in zip(*face[::-1])]
            else: s[face_key] = [list(row) for row in zip(*face)][::-1]
        face_moves = {"U": ('U', True), "U'": ('U', False), "D": ('D', True), "D'": ('D', False), "R": ('R', False), "R'": ('R', True), "L": ('L', False), "L'": ('L', True), "F": ('F', True), "F'": ('F', False), "B": ('B', True), "B'": ('B', False)}
        if move in face_moves: face, clockwise = face_moves[move]; rotate_face_sim(face, clockwise)
        if move in ("D", "D'"):
            temp_f=s['F'][2][:]; temp_r=s['R'][2][:]; temp_b=s['B'][2][:]; temp_l=s['L'][2][:]
            if move == "D": s['R'][2]=temp_f; s['F'][2]=temp_l; s['L'][2]=temp_b; s['B'][2]=temp_r
            else: s['L'][2]=temp_f; s['F'][2]=temp_r; s['R'][2]=temp_b; s['B'][2]=temp_l
        elif move in ("U", "U'"):
            temp_f=s['F'][0][:]; temp_r=s['R'][0][:]; temp_b=s['B'][0][:]; temp_l=s['L'][0][:]
            if move == "U": s['L'][0]=temp_f; s['F'][0]=temp_r; s['R'][0]=temp_b; s['B'][0]=temp_l
            else: s['R'][0]=temp_f; s['F'][0]=temp_l; s['L'][0]=temp_b; s['B'][0]=temp_r
        elif move in ("R", "R'"):
            temp_u=[s['U'][i][2] for i in range(3)]; temp_f=[s['F'][i][2] for i in range(3)]; temp_d=[s['D'][i][2] for i in range(3)]; temp_b=[s['B'][i][0] for i in range(3)]
            if move == "R":
                for i in range(3): s['F'][i][2]=temp_u[i]; s['D'][i][2]=temp_f[i]; s['B'][2-i][0]=temp_d[i]; s['U'][i][2]=temp_b[2-i]
            else:
                for i in range(3): s['B'][2-i][0]=temp_u[i]; s['D'][i][2]=temp_b[2-i]; s['F'][i][2]=temp_d[i]; s['U'][i][2]=temp_f[i]
        elif move in ("L", "L'"):
            temp_u=[s['U'][i][0] for i in range(3)]; temp_f=[s['F'][i][0] for i in range(3)]; temp_d=[s['D'][i][0] for i in range(3)]; temp_b=[s['B'][i][2] for i in range(3)]
            if move == "L":
                for i in range(3): s['B'][2-i][2]=temp_u[i]; s['D'][i][0]=temp_b[2-i]; s['F'][i][0]=temp_d[i]; s['U'][i][0]=temp_f[i]
            else:
                for i in range(3): s['F'][i][0]=temp_u[i]; s['D'][i][0]=temp_f[i]; s['B'][2-i][2]=temp_d[i]; s['U'][i][0]=temp_b[2-i]
        elif move in ("M", "M'"):
            temp_u=[s['U'][i][1] for i in range(3)]; temp_f=[s['F'][i][1] for i in range(3)]; temp_d=[s['D'][i][1] for i in range(3)]; temp_b=[s['B'][i][1] for i in range(3)]
            if move == "M":
                for i in range(3): s['F'][i][1]=temp_u[i]; s['D'][i][1]=temp_f[i]; s['B'][2-i][1]=temp_d[i]; s['U'][i][1]=temp_b[2-i]
            else:
                for i in range(3): s['B'][2-i][1]=temp_u[i]; s['D'][i][1]=temp_b[2-i]; s['F'][i][1]=temp_d[i]; s['U'][i][1]=temp_f[i]
        elif move in ("E", "E'"):
            temp_f=s['F'][1][:]; temp_r=s['R'][1][:]; temp_b=s['B'][1][:]; temp_l=s['L'][1][:]
            if move == "E": s['L'][1]=temp_f; s['B'][1]=temp_l; s['R'][1]=temp_b; s['F'][1]=temp_r
            else: s['R'][1]=temp_f; s['B'][1]=temp_r; s['L'][1]=temp_b; s['F'][1]=temp_l
        return state

    # --- 勝利条件を満たしたかチェックし、勝利/引き分け処理を行う関数 ---
    def check_win(self):
        if self.game_over: return
        board = self.marker_state['F']
        winners = [p for p in ['O', 'X', '△'] if self.check_win_on_board(board, p)]
        
        if len(winners) >= 2:
            self.game_over = True; self.winner = None; self.status_message = "引き分け!"; sound.play_effect('game:Error')
        elif len(winners) == 1:
            self.winner = winners[0]; self.game_over = True
            self.trigger_victory_effect()
            
    # --- 勝利演出を開始する補助関数 ---
    def trigger_victory_effect(self):
        # AI勝利時(プレイヤーの敗北時)は残念な効果音にし、パーティクルを出さない
        if self.winner == 'X' and self.game_mode == 'AI':
            sound.play_effect('game:Loss_1')
            self.victory_particles.clear()
            self.animation_timer = 0
        # それ以外の勝利の場合
        else:
            sound.play_effect('arcade:Powerup_1')
            self.victory_particles.clear(); self.animation_timer = 0
            for _ in range(30):
                particle = {'x': self.size.w / 2, 'y': 50, 'vx': random.uniform(-5, 5), 'vy': random.uniform(12, 22), 'emoji': random.choice(['🎉', '🎊', '✨', '🏆'])}
                self.victory_particles.append(particle)

    # --- 押された矢印ボタンに応じて、どの回転操作を行うかを決定する関数 ---
    def handle_rotate(self, bank, index):
        move = ""
        if bank == 'left':
            if index == 0:
                move = "U'"
            elif index == 1:
                move = "E'"
            elif index == 2:
                move = "D"
        elif bank == 'right':
            if index == 0:
                move = "U"
            elif index == 1:
                move = "E"
            elif index == 2:
                move = "D'"
        elif bank == 'top':
            if index == 0:
                move = "L'"
            elif index == 1:
                move = "M"
            elif index == 2:
                move = "R"
        elif bank == 'bottom':
            if index == 0:
                move = "L"
            elif index == 1:
                move = "M'"
            elif index == 2:
                move = "R'"
        
        if move:
            self.rotate(move)

    # --- 1つの面を90度回転させる関数 (U, D, R, L, F, Bの操作) ---
    def rotate_face(self, face_key, clockwise=True):
        for state in [self.cube_state, self.marker_state]:
            face = state[face_key]
            if clockwise: state[face_key] = [list(row) for row in zip(*face[::-1])]
            else: state[face_key] = [list(row) for row in zip(*face)][::-1]

    # --- キューブの層を回転させる中心的な関数 ---
    def rotate(self, move):
        s, m = self.cube_state, self.marker_state
        face_moves = {"U":('U',True), "U'":('U',False), "D":('D',True), "D'":('D',False), "R":('R',False), "R'":('R',True), "L":('L',False), "L'":('L',True), "F":('F',True), "F'":('F',False), "B":('B',True), "B'":('B',False)}
        if move in face_moves: face, clockwise = face_moves[move]; self.rotate_face(face, clockwise)
        if move in ("D","D'"):
            temp_s_f,temp_m_f=s['F'][2][:],m['F'][2][:]; temp_s_r,temp_m_r=s['R'][2][:],m['R'][2][:]; temp_s_b,temp_m_b=s['B'][2][:],m['B'][2][:]; temp_s_l,temp_m_l=s['L'][2][:],m['L'][2][:]
            if move=="D": s['R'][2],m['R'][2]=temp_s_f,temp_m_f; s['F'][2],m['F'][2]=temp_s_l,temp_m_l; s['L'][2],m['L'][2]=temp_s_b,temp_m_b; s['B'][2],m['B'][2]=temp_s_r,temp_m_r
            else: s['L'][2],m['L'][2]=temp_s_f,temp_m_f; s['F'][2],m['F'][2]=temp_s_r,temp_m_r; s['R'][2],m['R'][2]=temp_s_b,temp_m_b; s['B'][2],m['B'][2]=temp_s_l,temp_m_l
        elif move in ("U","U'"):
            temp_s_f,temp_m_f=s['F'][0][:],m['F'][0][:]; temp_s_r,temp_m_r=s['R'][0][:],m['R'][0][:]; temp_s_b,temp_m_b=s['B'][0][:],m['B'][0][:]; temp_s_l,temp_m_l=s['L'][0][:],m['L'][0][:]
            if move=="U": s['L'][0],m['L'][0]=temp_s_f,temp_m_f; s['F'][0],m['F'][0]=temp_s_r,temp_m_r; s['R'][0],m['R'][0]=temp_s_b,temp_m_b; s['B'][0],m['B'][0]=temp_s_l,temp_m_l
            else: s['R'][0],m['R'][0]=temp_s_f,temp_m_f; s['F'][0],m['F'][0]=temp_s_l,temp_m_l; s['L'][0],m['L'][0]=temp_s_b,temp_m_b; s['B'][0],m['B'][0]=temp_s_r,temp_m_r
        elif move in ("R","R'"):
            temp_s_u,temp_m_u=[s['U'][i][2] for i in range(3)],[m['U'][i][2] for i in range(3)]; temp_s_f,temp_m_f=[s['F'][i][2] for i in range(3)],[m['F'][i][2] for i in range(3)]; temp_s_d,temp_m_d=[s['D'][i][2] for i in range(3)],[m['D'][i][2] for i in range(3)]; temp_s_b,temp_m_b=[s['B'][i][0] for i in range(3)],[m['B'][i][0] for i in range(3)]
            if move=="R":
                for i in range(3): s['F'][i][2],m['F'][i][2]=temp_s_u[i],temp_m_u[i]; s['D'][i][2],m['D'][i][2]=temp_s_f[i],temp_m_f[i]; s['B'][2-i][0],m['B'][2-i][0]=temp_s_d[i],temp_m_d[i]; s['U'][i][2],m['U'][i][2]=temp_s_b[2-i],temp_m_b[2-i]
            else:
                for i in range(3): s['B'][2-i][0],m['B'][2-i][0]=temp_s_u[i],temp_m_u[i]; s['D'][i][2],m['D'][i][2]=temp_s_b[2-i],temp_m_b[2-i]; s['F'][i][2],m['F'][i][2]=temp_s_d[i],temp_m_d[i]; s['U'][i][2],m['U'][i][2]=temp_s_f[i],temp_m_f[i]
        elif move in ("L","L'"):
            temp_s_u,temp_m_u=[s['U'][i][0] for i in range(3)],[m['U'][i][0] for i in range(3)]; temp_s_f,temp_m_f=[s['F'][i][0] for i in range(3)],[m['F'][i][0] for i in range(3)]; temp_s_d,temp_m_d=[s['D'][i][0] for i in range(3)],[m['D'][i][0] for i in range(3)]; temp_s_b,temp_m_b=[s['B'][i][2] for i in range(3)],[m['B'][i][2] for i in range(3)]
            if move=="L":
                for i in range(3): s['B'][2-i][2],m['B'][2-i][2]=temp_s_u[i],temp_m_u[i]; s['D'][i][0],m['D'][i][0]=temp_s_b[2-i],temp_m_b[2-i]; s['F'][i][0],m['F'][i][0]=temp_s_d[i],temp_m_d[i]; s['U'][i][0],m['U'][i][0]=temp_s_f[i],temp_m_f[i]
            else:
                for i in range(3): s['F'][i][0],m['F'][i][0]=temp_s_u[i],temp_m_u[i]; s['D'][i][0],m['D'][i][0]=temp_s_f[i],temp_m_f[i]; s['B'][2-i][2],m['B'][2-i][2]=temp_s_d[i],temp_m_d[i]; s['U'][i][0],m['U'][i][0]=temp_s_b[2-i],temp_m_b[2-i]
        elif move in ("M","M'"):
            temp_s_u,temp_m_u=[s['U'][i][1] for i in range(3)],[m['U'][i][1] for i in range(3)]; temp_s_f,temp_m_f=[s['F'][i][1] for i in range(3)],[m['F'][i][1] for i in range(3)]; temp_s_d,temp_m_d=[s['D'][i][1] for i in range(3)],[m['D'][i][1] for i in range(3)]; temp_s_b,temp_m_b=[s['B'][i][1] for i in range(3)],[m['B'][i][1] for i in range(3)]
            if move=="M":
                for i in range(3): s['F'][i][1],m['F'][i][1]=temp_s_u[i],temp_m_u[i]; s['D'][i][1],m['D'][i][1]=temp_s_f[i],temp_m_f[i]; s['B'][2-i][1],m['B'][2-i][1]=temp_s_d[i],temp_m_d[i]; s['U'][i][1],m['U'][i][1]=temp_s_b[2-i],temp_m_b[2-i]
            else:
                for i in range(3): s['B'][2-i][1],m['B'][2-i][1]=temp_s_u[i],temp_m_u[i]; s['D'][i][1],m['D'][i][1]=temp_s_b[2-i],temp_m_b[2-i]; s['F'][i][1],m['F'][i][1]=temp_s_d[i],temp_m_d[i]; s['U'][i][1],m['U'][i][1]=temp_s_f[i],temp_m_f[i]
        elif move in ("E","E'"):
            temp_s_f,temp_m_f=s['F'][1][:],m['F'][1][:]; temp_s_r,temp_m_r=s['R'][1][:],m['R'][1][:]; temp_s_b,temp_m_b=s['B'][1][:],m['B'][1][:]; temp_s_l,temp_m_l=s['L'][1][:],m['L'][1][:]
            if move=="E": s['L'][1],m['L'][1]=temp_s_f,temp_m_f; s['B'][1],m['B'][1]=temp_s_l,temp_m_l; s['R'][1],m['R'][1]=temp_s_b,temp_m_b; s['F'][1],m['F'][1]=temp_s_r,temp_m_r
            else: s['R'][1],m['R'][1]=temp_s_f,temp_m_f; s['B'][1],m['B'][1]=temp_s_r,temp_m_r; s['L'][1],m['L'][1]=temp_s_b,temp_m_b; s['F'][1],m['F'][1]=temp_s_l,temp_m_l

# --- ゲームを実行 ---
if __name__ == '__main__':
    screen_size = ui.get_screen_size()
    scene_view = SceneView(frame=(0, 0, screen_size.w, screen_size.h))
    scene_view.scene = CubeTicTacToeScene()
    scene_view.name = 'OX game'
    scene_view.present('fullscreen')
