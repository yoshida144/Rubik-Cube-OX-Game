# game_scene.py

# ===================================================================================
# ゲームの「見た目(UI)」と「ユーザー操作」を担当するファイルです。
# - 盤面、ボタン、怪獣、卵などの描画
# - 画面のタッチイベントの処理
# - ゲームの進行管理(タイトル→モード選択→プレイ画面など)
# - アニメーションの制御
# - AIの思考ルーチン
# など、ユーザーが直接触れる部分を専門に扱います。
# ===================================================================================

from scene import *
import ui
import random
import copy
import sound
import math
from constants import *
from game_logic import GameLogic

# --- AIの思考ロジックをまとめたクラス ---
class AIPlayer:
    # ... (AIの思考ロジック、元のコードから変更なし)
    def make_move(self, scene):
        game_logic = scene.game
        
        def is_valid_move(pos_tuple):
            if not pos_tuple: return False
            face, r, c = pos_tuple
            if game_logic.marker_state[face][r][c] is not None: return False
            if scene.game_ruleset == 'custom' and pos_tuple in game_logic.kaiju_positions: return False
            if scene.game_ruleset == 'custom' and pos_tuple in game_logic.egg_positions: return False
            return True

        if scene.game_ruleset == 'custom':
            golden_eggs = [pos for pos, type in game_logic.egg_positions.items() if type == 'golden']
            if golden_eggs: scene._handle_egg_effect(golden_eggs[0]); scene.end_turn(); return
            f_face_eggs = [pos for pos in game_logic.egg_positions if pos[0] == 'F']
            if f_face_eggs: scene._handle_egg_effect(f_face_eggs[0]); scene.end_turn(); return

        move = self.find_winning_or_blocking_move('X', game_logic.marker_state)
        if move and is_valid_move(('F', move[0], move[1])): game_logic.marker_state['F'][move[0]][move[1]] = 'X'; scene.end_turn(); return
        
        for rotation in ALL_MOVES:
            sim_state = self.simulate_rotation(game_logic.marker_state, rotation)
            if self.check_win_on_board(sim_state['F'], 'X'): scene.handle_rotate_action(rotation); scene.end_turn(); return
            
        move = self.find_winning_or_blocking_move('O', game_logic.marker_state)
        if move and is_valid_move(('F', move[0], move[1])): game_logic.marker_state['F'][move[0]][move[1]] = 'X'; scene.end_turn(); return

        empty_cells = []
        for face_key in FACE_KEYS:
            for r in range(3):
                for c in range(3):
                    if is_valid_move((face_key, r, c)): empty_cells.append((face_key, r, c))
        if empty_cells:
            face, r, c = random.choice(empty_cells)
            game_logic.marker_state[face][r][c] = 'X'; scene.end_turn()

    def find_winning_or_blocking_move(self, marker, state):
        board = state['F']
        lines = [((0,0),(0,1),(0,2)),((1,0),(1,1),(1,2)),((2,0),(2,1),(2,2)),((0,0),(1,0),(2,0)),((0,1),(1,1),(2,1)),((0,2),(1,2),(2,2)),((0,0),(1,1),(2,2)),((0,2),(1,1),(2,0))]
        for line in lines:
            values = [board[r][c] for r, c in line]
            if values.count(marker) == 2 and values.count(None) == 1: return line[values.index(None)]
        return None

    def check_win_on_board(self, board, marker):
        lines = [[board[0][0],board[0][1],board[0][2]],[board[1][0],board[1][1],board[1][2]],[board[2][0],board[2][1],board[2][2]],[board[0][0],board[1][0],board[2][0]],[board[0][1],board[1][1],board[2][1]],[board[0][2],board[1][2],board[2][2]],[board[0][0],board[1][1],board[2][2]],[board[0][2],board[1][1],board[2][0]]]
        for line in lines:
            if line[0] is not None and line[0] == marker and line[0] == line[1] == line[2]: return True
        return False
        
    def simulate_rotation(self, original_state, move):
        state = copy.deepcopy(original_state); s = state
        def rotate_face_sim(face_key, clockwise=True):
            face = s[face_key]
            if clockwise: s[face_key] = [list(row) for row in zip(*face[::-1])]
            else: s[face_key] = [list(row) for row in zip(*face)][::-1]
        face_moves = {"U": ('U', True), "U'": ('U', False), "D": ('D', True), "D'": ('D', False), "R": ('R', False), "R'": ('R', True), "L": ('L', False), "L'": ('L', True), "F": ('F', True), "F'": ('F', False), "B": ('B', True), "B'": ('B', False)}
        if move in face_moves: face, clockwise = face_moves[move]; rotate_face_sim(face, clockwise)
        # (Rest of the simulation logic is the same as the original rotate)
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

class CubeTicTacToeScene(Scene):
    """
    ゲームの描画、アニメーション、タッチ操作を管理するメインクラス。
    """
    def setup(self):
        # ... (初期化処理)
        self.background_color = '#F1F1F1'
        self.game = GameLogic()
        self.ai = AIPlayer()
        
        self.current_player = 'O'; self.game_over = False; self.winner = None
        self.status_message = "Oのターン"
        
        self.game_phase = 'title'
        self.game_mode = None
        self.game_ruleset = None
        self.num_kaiju = 1
        
        self.normal_mode_button_rect = None
        self.custom_mode_button_rect = None
        self.ai_button_rect = None
        self.twoplayer_button_rect = None
        self.threeplayer_button_rect = None
        self.rules_start_button_rect = None
        self.back_button_rect = None
        self.kaiju_plus_button_rect = None
        self.kaiju_minus_button_rect = None
        
        self.victory_particles = []; self.animation_timer = 0
        self.state_history = []
        
        self.kaiju_draw_positions = []
        self.kaiju_animations = []
        self.is_kaiju_animating = False
        self.kaiju_anim_progress = 0
        
        self.buttons = {}
        self.face_origins = {}
        
        self.reset_game_scene()

    def reset_game_scene(self):
        # ... (ゲーム画面の状態をリセット)
        self.game.reset()
        self.current_player = 'O'; self.game_over = False; self.winner = None
        self.status_message = "Oのターン"; self.victory_particles.clear(); self.animation_timer = 0
        self.state_history.clear()
        
        self.kaiju_draw_positions.clear(); self.kaiju_animations.clear()
        self.is_kaiju_animating = False
        
        if self.game_ruleset == 'custom':
            self.game.place_kaiju(self.num_kaiju)
            
    def update(self):
        # ... (アニメーションなどの毎フレーム処理)
        if self.game_over:
            self.animation_timer += 1
            if self.winner:
                for p in self.victory_particles: p['x'] += p['vx']; p['y'] += p['vy']; p['vy'] -= 0.2
                self.victory_particles = [p for p in self.victory_particles if p['y'] > -50]
        
        if self.is_kaiju_animating:
            self.kaiju_anim_progress += 0.05
            if self.kaiju_anim_progress >= 1.0:
                self.is_kaiju_animating = False
                for anim_data in self.kaiju_animations:
                    self.kaiju_draw_positions[anim_data['kaiju_index']] = anim_data['end_pos']
                self.kaiju_animations.clear()
                self._switch_player_and_continue()
            else:
                for anim_data in self.kaiju_animations:
                    idx = anim_data['kaiju_index']
                    start_x, start_y = anim_data['start_pos']
                    end_x, end_y = anim_data['end_pos']
                    self.kaiju_draw_positions[idx] = (start_x + (end_x - start_x) * self.kaiju_anim_progress, start_y + (end_y - start_y) * self.kaiju_anim_progress)

    def draw(self):
        # ... (現在のゲームフェーズに応じた画面全体の描画)
        center_x, center_y = self.size.w / 2, self.size.h / 2
        if self.game_phase == 'playing':
            tint(1,1,1,1); image('IMG_0473.JPG',0,0,self.size.w,self.size.h)
            fill(0, 0, 0, 0.5); rect(0, 0, self.size.w, self.size.h)
            header_height = 60
            fill(0, 0, 0, 0.7); rect(0, self.size.h - header_height, self.size.w, header_height)
            back_btn_w, back_btn_h = 120, 40
            back_btn_x, back_btn_y = 10, self.size.h - header_height + (header_height - back_btn_h) / 2
            self.back_button_rect = Rect(back_btn_x, back_btn_y, back_btn_w, back_btn_h)
            fill(0.3, 0.3, 0.3, 0.8); rect(*self.back_button_rect)
            self.draw_stylish_text('↩︎ モード選択へ', 'Futura-CondensedMedium', 18, back_btn_x + back_btn_w/2, back_btn_y + back_btn_h/2, 'white')
            self.draw_stylish_text(self.status_message, 'Futura-CondensedMedium', 70, center_x, self.size.h - 30 - header_height / 2, 'white')
            mode_text = 'vs AI' if self.game_mode == 'AI' else ('vs Player' if self.game_mode == '2P' else '3 Players')
            self.draw_stylish_text(mode_text, 'Futura-CondensedMedium', 18, self.size.w - 60, self.size.h - header_height / 2, (0.8, 0.8, 0.8, 1.0))
            face_total_size = TILE_SIZE * 3 + GAP * 2
            face_offsets = { 'U': (0, 1), 'L': (-1, 0), 'F': (0, 0), 'R': (1, 0), 'B': (2, 0), 'D': (0, -1) }
            self.face_origins.clear()
            for face_key, (offset_x, offset_y) in face_offsets.items():
                origin_x = center_x + offset_x * (face_total_size + FACE_GAP) - face_total_size / 2
                origin_y = center_y + offset_y * (face_total_size + FACE_GAP) - face_total_size / 2 - 30
                self.face_origins[face_key] = (origin_x, origin_y)
                if face_key == 'F':
                  glow_padding = 5; fill('#00A0FF'); stroke_weight(0)
                  rect(origin_x - glow_padding, origin_y - glow_padding, face_total_size + glow_padding * 2, face_total_size + glow_padding * 2)
                self.draw_face(face_key, origin_x, origin_y, self.game.marker_state[face_key])
            self.draw_buttons(self.face_origins, face_total_size)
            if self.game_ruleset == 'custom' and self.game.kaiju_positions:
                self.draw_kaiju()
            if self.game_over:
                fill(0, 0, 0, 0.6); rect(0, 0, self.size.w, self.size.h)
                scale = 1.0 + math.sin(self.animation_timer * 0.1) * 0.1
                if self.winner:
                    win_text = ""; text_color = "white"
                    if self.winner == 'X' and self.game_mode == 'AI': win_text = "YOUR LOSE!"; text_color = '#AAAAAA'
                    elif self.winner == 'O': win_text = "O WIN!"; text_color = 'red'
                    elif self.winner == 'X': win_text = "X WIN!"; text_color = 'blue'
                    elif self.winner == '△': win_text = "△ WIN!"; text_color = 'green'
                    self.draw_stylish_text(win_text, 'Futura-CondensedExtraBold', 100 * scale, center_x, center_y, text_color)
                    for p in self.victory_particles: text(p['emoji'], 'AppleColorEmoji', 50, p['x'], p['y'])
                else:
                    self.draw_stylish_text("DRAW", 'Futura-CondensedExtraBold', 120 * scale, center_x, center_y, 'white')
        elif self.game_phase == 'rules':
            # ... (rule drawing logic from original code)
            tint(1,1,1,1); image('IMG_0479.JPG',0,0,self.size.w,self.size.h)
            fill(0, 0, 0, 0.7); rect(0, 0, self.size.w, self.size.h)
            rules = ["ルール説明", " ", "1. 自分のターンにできることは", "   「キューブを回転」「マークを配置」", "   「卵を選択」のいずれかです。"]
            if self.game_ruleset == 'custom':
                rules.extend([" ", "2. 怪獣のマスにはマークを置けません。", "   回転で一緒に動き、1ターンごとに動きます。", " ", "3. 怪獣が動いた跡には卵が残ります。", "   卵を選択するとマークが複数配置されます。", "   (10回に1度、金の卵になります)"])
            else:
                rules.extend([" ", "2. 盤面で縦・横・斜めに3つ揃えると勝利です。", "3. 同じ盤面が3回繰り返されると引き分けです。"])
            y_pos = self.size.h - 150
            for i, line in enumerate(rules):
                font_size = 36 if i == 0 else 24; text(line, 'HiraginoSans-W6', font_size, center_x, y_pos); y_pos -= 38
            btn_w, btn_h = 300, 80; btn_x, btn_y = center_x - btn_w / 2, 100
            self.rules_start_button_rect = Rect(btn_x, btn_y, btn_w, btn_h)
            fill(0.1, 0.8, 0.5, 0.8); stroke_weight(3); stroke(0.4, 1.0, 0.8, 1.0); rect(*self.rules_start_button_rect)
            tint('white'); text('ゲーム開始', 'Helvetica-Bold', 40, center_x, btn_y + btn_h/2)
        elif self.game_phase == 'player_selection':
            # ... (player selection drawing logic from original code)
            tint(1,1,1,1); image('IMG_0474.JPG',0,0,self.size.w,self.size.h)
            fill(0, 0, 0, 0.5); rect(0,0,self.size.w, self.size.h)
            mode_text = "ノーマルモード" if self.game_ruleset == 'normal' else "カスタマイズモード"
            self.draw_stylish_text(mode_text, 'HiraginoSans-W6', 40, center_x, self.size.h - 100, 'white')
            btn_w, btn_h = 300, 60; btn_spacing = 20
            
            if self.game_ruleset == 'custom':
                self.draw_stylish_text('怪獣の数', 'HiraginoSans-W6', 24, center_x, self.size.h - 180, 'white')
                btn_size = 50
                self.kaiju_minus_button_rect = Rect(center_x - 100 - btn_size/2, self.size.h - 240, btn_size, btn_size)
                fill(0.8, 0.2, 0.2); rect(*self.kaiju_minus_button_rect)
                self.draw_stylish_text('-', 'Helvetica-Bold', 40, self.kaiju_minus_button_rect.center().x, self.kaiju_minus_button_rect.center().y, 'white')
                self.draw_stylish_text(str(self.num_kaiju), 'Helvetica-Bold', 50, center_x, self.size.h - 215, 'white')
                self.kaiju_plus_button_rect = Rect(center_x + 100 - btn_size/2, self.size.h - 240, btn_size, btn_size)
                fill(0.2, 0.8, 0.2); rect(*self.kaiju_plus_button_rect)
                self.draw_stylish_text('+', 'Helvetica-Bold', 40, self.kaiju_plus_button_rect.center().x, self.kaiju_plus_button_rect.center().y, 'white')

            ai_btn_y = center_y - btn_h - btn_spacing
            self.ai_button_rect = Rect(center_x - btn_w / 2, ai_btn_y, btn_w, btn_h)
            fill(0.1, 0.5, 0.8, 0.7); stroke_weight(3); stroke(0.4, 0.8, 1.0, 1.0); rect(*self.ai_button_rect)
            tint('white'); text('AIと対戦', 'Helvetica-Bold', 32, center_x, ai_btn_y + btn_h / 2)
            self.twoplayer_button_rect = Rect(center_x - btn_w / 2, center_y, btn_w, btn_h)
            fill(0.8, 0.1, 0.5, 0.7); stroke_weight(3); stroke(1.0, 0.4, 0.8, 1.0); rect(*self.twoplayer_button_rect)
            tint('white'); text('2人で対戦', 'Helvetica-Bold', 32, center_x, center_y + btn_h / 2)
            p3_btn_y = center_y + btn_h + btn_spacing
            self.threeplayer_button_rect = Rect(center_x - btn_w / 2, p3_btn_y, btn_w, btn_h)
            fill(0.1, 0.8, 0.5, 0.7); stroke_weight(3); stroke(0.4, 1.0, 0.8, 1.0); rect(*self.threeplayer_button_rect)
            tint('white'); text('3人で対戦', 'Helvetica-Bold', 32, center_x, p3_btn_y + btn_h / 2)
            back_btn_w, back_btn_h = 120, 40
            self.back_button_rect = Rect(10, 10, back_btn_w, back_btn_h)
            fill(0.3, 0.3, 0.3, 0.8); rect(*self.back_button_rect)
            self.draw_stylish_text('↩︎ 戻る', 'Futura-CondensedMedium', 18, 10 + back_btn_w/2, 10 + back_btn_h/2, 'white')
        else: # title phase
            # ... (title drawing logic from original code)
            tint(1,1,1,1); image('IMG_0474.JPG',0,0,self.size.w,self.size.h)
            self.draw_stylish_text('3D Cube OX Game', 'Futura-CondensedExtraBold', 80, center_x, self.size.h - 150, 'white')
            btn_w, btn_h = 350, 70; btn_spacing = 30
            normal_btn_y = center_y - btn_h/2 - btn_spacing
            self.normal_mode_button_rect = Rect(center_x - btn_w / 2, normal_btn_y, btn_w, btn_h)
            fill(0.1, 0.5, 0.8, 0.8); stroke_weight(3); stroke(0.4, 0.8, 1.0, 1.0); rect(*self.normal_mode_button_rect)
            self.draw_stylish_text('ノーマルモード', 'HiraginoSans-W6', 36, center_x, normal_btn_y + btn_h / 2, 'white')
            custom_btn_y = center_y + btn_h/2
            self.custom_mode_button_rect = Rect(center_x - btn_w / 2, custom_btn_y, btn_w, btn_h)
            fill(0.8, 0.1, 0.5, 0.8); stroke_weight(3); stroke(1.0, 0.4, 0.8, 1.0); rect(*self.custom_mode_button_rect)
            self.draw_stylish_text('怪獣モード', 'HiraginoSans-W6', 36, center_x, custom_btn_y + btn_h / 2, 'white')

        stroke_weight(1); stroke('grey'); tint(1,1,1,1)

    def draw_kaiju(self):
        # ... (怪獣の描画)
        if not hasattr(self, 'face_origins') or not self.face_origins: return
        if len(self.kaiju_draw_positions) != len(self.game.kaiju_positions):
            self.kaiju_draw_positions = [(0,0)] * len(self.game.kaiju_positions)
        for i, (face, r, c) in enumerate(self.game.kaiju_positions):
            is_this_kaiju_animating = any(anim['kaiju_index'] == i for anim in self.kaiju_animations)
            if not is_this_kaiju_animating:
                if face in self.face_origins:
                    origin_x, origin_y = self.face_origins[face]
                    px = origin_x + c * (TILE_SIZE + GAP) + TILE_SIZE / 2
                    py = origin_y + (2 - r) * (TILE_SIZE + GAP) + TILE_SIZE / 2
                    self.kaiju_draw_positions[i] = (px, py)
                else: continue
            px, py = self.kaiju_draw_positions[i]
            if px == 0 and py == 0: continue
            shadow_offset = 4
            tint(0, 0, 0, 0.4); text('🦖', 'AppleColorEmoji', TILE_SIZE * 1.1, px + shadow_offset, py - shadow_offset)
            tint(1, 1, 1, 1); text('🦖', 'AppleColorEmoji', TILE_SIZE * 1.1, px, py)

    def draw_face(self, face_key, origin_x, origin_y, face_markers):
        # ... (面の描画、卵の描画を含む)
        for row in range(3):
            for col in range(3):
                color = self.game.cube_state[face_key][2 - row][col]; fill(color); stroke('#00FFFF'); stroke_weight(2)
                px = origin_x + col * (TILE_SIZE + GAP); py = origin_y + row * (TILE_SIZE + GAP)
                rect(px, py, TILE_SIZE, TILE_SIZE)
                tile_pos = (face_key, 2-row, col)
                if tile_pos in self.game.egg_positions:
                    egg_type = self.game.egg_positions[tile_pos]
                    emoji = '🌟' if egg_type == 'golden' else '🥚'
                    text(emoji, 'AppleColorEmoji', 40, px + TILE_SIZE/2, py + TILE_SIZE/2)
                marker = face_markers[2 - row][col]
                if marker:
                    marker_colors = {'O': '#FF0000', 'X': '#0000FF', '△': '#2ECC71'}
                    self.draw_stylish_text(marker, 'Helvetica-Bold', 36, px + TILE_SIZE/2, py + TILE_SIZE/2, marker_colors.get(marker, 'black'))
                    
    def draw_stylish_text(self, text_str, font_name, font_size, x, y, main_color):
        shadow_offset = 2; tint(0, 0, 0, 0.6); text(text_str, font_name, font_size, x + shadow_offset, y - shadow_offset)
        tint(main_color); text(text_str, font_name, font_size, x, y); tint(1, 1, 1, 1)

    def draw_buttons(self, face_origins, face_size):
        self.buttons.clear(); btn_padding = BUTTON_SIZE/2 + 10
        player_colors = {'O': '#C0392B', 'X': '#2980B9', '△': '#27AE60'}
        button_color = player_colors.get(self.current_player, '#808080')
        u_origin_x, u_origin_y = face_origins['U']; d_origin_x, d_origin_y = face_origins['D']
        for i in range(3):
            px = u_origin_x + i * (TILE_SIZE + GAP) + TILE_SIZE / 2
            self.buttons[('top', i)] = Rect(px - BUTTON_SIZE/2, u_origin_y + face_size + btn_padding - BUTTON_SIZE/2, BUTTON_SIZE, BUTTON_SIZE)
            self.buttons[('bottom', i)] = Rect(px - BUTTON_SIZE/2, d_origin_y - btn_padding - BUTTON_SIZE/2, BUTTON_SIZE, BUTTON_SIZE)
        l_origin_x, l_origin_y = face_origins['L']; b_origin_x, b_origin_y = face_origins['B']
        for i in range(3):
            py = l_origin_y + i * (TILE_SIZE + GAP) + TILE_SIZE / 2
            self.buttons[('left', 2-i)] = Rect(l_origin_x - btn_padding - BUTTON_SIZE/2, py - BUTTON_SIZE/2, BUTTON_SIZE, BUTTON_SIZE)
            self.buttons[('right', 2-i)] = Rect(b_origin_x + face_size + btn_padding - BUTTON_SIZE/2, py - BUTTON_SIZE/2, BUTTON_SIZE, BUTTON_SIZE)
        for key, rect in self.buttons.items():
            px, py = rect.center().x, rect.center().y
            arrow = ''
            if key[0] == 'top': arrow = '↓'
            elif key[0] == 'bottom': arrow = '↑'
            elif key[0] == 'left': arrow = '→'
            elif key[0] == 'right': arrow = '←'
            stroke_weight(0); fill(button_color); ellipse(*rect)
            tint('white'); text(arrow, 'Helvetica-Bold', 28, px, py)
        tint(1,1,1,1)

    def touch_began(self, touch):
        # ... (タッチイベントの振り分け)
        if self.game_phase == 'playing':
            if self.is_kaiju_animating: return
            if self.back_button_rect and touch.location in self.back_button_rect:
                self.game_phase = 'player_selection'; self.reset_game_scene(); return
            if self.game_over:
                self.game_phase = 'title'; self.reset_game_scene(); return
            if self.game_mode == 'AI' and self.current_player == 'X': return
            action_taken = False
            for key, rect_val in self.buttons.items():
                if touch.location in rect_val:
                    bank, index = key; self.handle_rotate_action(self._get_move_from_button(bank, index)); action_taken = True; break
            if not action_taken:
                for face_key, (origin_x, origin_y) in self.face_origins.items():
                    face_rect = Rect(origin_x, origin_y, TILE_SIZE * 3 + GAP * 2, TILE_SIZE * 3 + GAP * 2)
                    if touch.location in face_rect:
                        col = int((touch.location.x - origin_x) / (TILE_SIZE + GAP)); row = int((touch.location.y - origin_y) / (TILE_SIZE + GAP))
                        tile_pos = (face_key, 2 - row, col)
                        if self.game_ruleset == 'custom' and tile_pos in self.game.egg_positions:
                            self._handle_egg_effect(tile_pos); action_taken = True
                        elif self.game_ruleset == 'custom' and tile_pos in self.game.kaiju_positions:
                            self.status_message = "怪獣がいて置けない!"; sound.play_effect('game:Error')
                        elif self.game.marker_state[face_key][2-row][col] is None:
                            self.game.marker_state[face_key][2-row][col] = self.current_player; action_taken = True
                        break
            if action_taken: self.end_turn()
        elif self.game_phase == 'rules':
            if self.rules_start_button_rect and touch.location in self.rules_start_button_rect: self.game_phase = 'playing'; self.reset_game_scene()
        elif self.game_phase == 'player_selection':
            if self.ai_button_rect and touch.location in self.ai_button_rect: self.game_mode = 'AI'; self.game_phase = 'rules'
            elif self.twoplayer_button_rect and touch.location in self.twoplayer_button_rect: self.game_mode = '2P'; self.game_phase = 'rules'
            elif self.threeplayer_button_rect and touch.location in self.threeplayer_button_rect: self.game_mode = '3P'; self.game_phase = 'rules'
            elif self.back_button_rect and touch.location in self.back_button_rect: self.game_phase = 'title'
            elif self.game_ruleset == 'custom':
                if self.kaiju_plus_button_rect and touch.location in self.kaiju_plus_button_rect: self.num_kaiju = min(MAX_KAIJU_TOTAL, self.num_kaiju + 1)
                elif self.kaiju_minus_button_rect and touch.location in self.kaiju_minus_button_rect: self.num_kaiju = max(1, self.num_kaiju - 1)
        else: # title phase
            if self.normal_mode_button_rect and touch.location in self.normal_mode_button_rect: self.game_ruleset = 'normal'; self.game_phase = 'player_selection'
            elif self.custom_mode_button_rect and touch.location in self.custom_mode_button_rect: self.game_ruleset = 'custom'; self.game_phase = 'player_selection'
                
    def end_turn(self):
        # ... (ターン終了時の処理)
        self.check_win()
        if self.game_over: return
        
        if self.game_ruleset == 'custom' and self.game.kaiju_positions:
            self.delay(0.5, self._trigger_kaiju_move)
        else:
            self._switch_player_and_continue()
    
    def _handle_egg_effect(self, egg_pos):
        # ... (卵の効果処理)
        egg_type = self.game.egg_positions.pop(egg_pos)
        num_marks = GOLDEN_EGG_MARKERS if egg_type == 'golden' else NORMAL_EGG_MARKERS
        sound.play_effect('game:Ding_3')
        
        empty_spots = []
        for face in FACE_KEYS:
            for r in range(3):
                for c in range(3):
                    pos = (face, r, c)
                    if self.game.marker_state[face][r][c] is None and pos not in self.game.kaiju_positions and pos not in self.game.egg_positions:
                        empty_spots.append(pos)
        random.shuffle(empty_spots)
        
        if empty_spots:
            num_to_place = min(num_marks, len(empty_spots))
            self.status_message = f"{num_to_place}個のマークが出現!"
            for i in range(num_to_place):
                face, r, c = empty_spots[i]
                self.game.marker_state[face][r][c] = self.current_player
        else:
            self.status_message = "空きマスがなかった!"
            sound.play_effect('game:Error')
            
    def _trigger_kaiju_move(self, *args):
        # ... (怪獣の移動トリガー)
        if not self.game.kaiju_positions: self._switch_player_and_continue(); return
        num_to_move = random.randint(1, len(self.game.kaiju_positions))
        self.status_message = f"{num_to_move}体の怪獣が動く!"
        sound.play_effect('arcade:Jump_1')
        indices_to_move = random.sample(range(len(self.game.kaiju_positions)), num_to_move)
        
        self.kaiju_animations.clear()
        occupied_tiles = set(self.game.kaiju_positions)
        new_positions = {}

        for i in indices_to_move:
            start_pos = self.game.kaiju_positions[i]
            occupied_tiles.remove(start_pos)
            next_pos = self._get_next_step_to_f_face(start_pos) if start_pos[0] != 'F' else self._get_random_move_on_face(start_pos, occupied_tiles)
            
            if next_pos and next_pos not in occupied_tiles:
                new_positions[i] = next_pos
                occupied_tiles.add(next_pos)
            else:
                occupied_tiles.add(start_pos)

        for i, new_pos in new_positions.items():
            old_pos = self.game.kaiju_positions[i]
            self.game.kaiju_positions[i] = new_pos
            self.game.total_kaiju_moves += 1
            egg_type = 'golden' if self.game.total_kaiju_moves % GOLDEN_EGG_INTERVAL == 0 else 'normal'
            self.game.egg_positions[old_pos] = egg_type
            if new_pos in self.game.egg_positions: del self.game.egg_positions[new_pos]
            
            self.game.marker_state[new_pos[0]][new_pos[1]][new_pos[2]] = None
            
            start_px, start_py = self.kaiju_draw_positions[i]
            end_px, end_py = self._get_pixel_coords(new_pos)
            self.kaiju_animations.append({'kaiju_index': i, 'start_pos': (start_px, start_py), 'end_pos': (end_px, end_py)})

        if self.kaiju_animations:
            self.kaiju_anim_progress = 0
            self.is_kaiju_animating = True
        else:
            self._switch_player_and_continue()

    def _get_random_move_on_face(self, start_pos, occupied_tiles):
        start_face, start_r, start_c = start_pos
        possible_moves = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0: continue
                new_r, new_c = start_r + dr, start_c + dc
                if 0 <= new_r < 3 and 0 <= new_c < 3:
                    possible_moves.append((start_face, new_r, new_c))
        valid_moves = [p for p in possible_moves if p not in occupied_tiles]
        return random.choice(valid_moves) if valid_moves else None
    
    def _get_pixel_coords(self, pos):
        face, r, c = pos
        if face in self.face_origins:
            ox, oy = self.face_origins[face]
            return (ox + c * (TILE_SIZE + GAP) + TILE_SIZE / 2, oy + (2 - r) * (TILE_SIZE + GAP) + TILE_SIZE / 2)
        return (0, 0)
        
    def _get_next_step_to_f_face(self, current_pos):
        face, r, c = current_pos
        if face == 'U': return ('F', 0, c) if r == 0 else (face, r - 1, c)
        elif face == 'D': return ('F', 2, c) if r == 2 else (face, r + 1, c)
        elif face == 'L': return ('F', r, 0) if c == 2 else (face, r, c + 1)
        elif face == 'R': return ('F', r, 2) if c == 0 else (face, r, c - 1)
        elif face == 'B': return ('R', r, 2) if c == 0 else (face, r, c - 1)
        return current_pos

    def _switch_player_and_continue(self):
        # ... (プレイヤー交代)
        if self.game_mode == '3P':
            self.current_player = {'O':'X', 'X':'△', '△':'O'}[self.current_player]
        else:
            self.current_player = 'X' if self.current_player == 'O' else 'O'
        self.check_win()
        if self.game_over: return
        if self.game_mode == 'AI' and self.current_player == 'X':
            self.status_message = "AI 考え中... 🤔"; self.delay(0.5, self.ai.make_move, self)
        else:
            self.status_message = f"{self.current_player}のターン"
            
    def check_win(self):
        # ... (勝利判定)
        board = self.game.marker_state['F']
        winners = [p for p in ['O', 'X', '△'] if self.ai.check_win_on_board(board, p)]
        if len(winners) >= 2: self.game_over = True; self.winner = None; self.status_message = "引き分け!"; sound.play_effect('game:Error')
        elif len(winners) == 1: self.winner = winners[0]; self.game_over = True; self.trigger_victory_effect()
        
    def trigger_victory_effect(self):
        # ... (勝利演出)
        if self.winner == 'X' and self.game_mode == 'AI':
            sound.play_effect('game:Loss_1'); self.victory_particles.clear(); self.animation_timer = 0
        else:
            sound.play_effect('arcade:Powerup_1'); self.victory_particles.clear(); self.animation_timer = 0
            for _ in range(30): self.victory_particles.append({'x': self.size.w / 2, 'y': 50, 'vx': random.uniform(-5, 5), 'vy': random.uniform(12, 22), 'emoji': random.choice(['🎉', '🎊', '✨', '🏆'])})

    def _get_move_from_button(self, bank, index):
        moves = {
            ('left', 0): "U'", ('left', 1): "E'", ('left', 2): "D",
            ('right', 0): "U", ('right', 1): "E", ('right', 2): "D'",
            ('top', 0): "L'", ('top', 1): "M", ('top', 2): "R",
            ('bottom', 0): "L", ('bottom', 1): "M'", ('bottom', 2): "R'"
        }
        return moves.get((bank, index), "")
        
    def handle_rotate_action(self, move):
        # ... (回転実行と怪獣の位置更新)
        if not move: return
        if self.game_ruleset == 'custom' and self.game.kaiju_positions:
            for i, (face, r, c) in enumerate(self.game.kaiju_positions):
                self.game.marker_state[face][r][c] = f'KAIJU_{i}'
        self.game.rotate(move)
        if self.game_ruleset == 'custom' and self.game.kaiju_positions:
            new_positions = [None] * len(self.game.kaiju_positions)
            for f in FACE_KEYS:
                for r_idx in range(3):
                    for c_idx in range(3):
                        marker = self.game.marker_state[f][r_idx][c_idx]
                        if isinstance(marker, str) and marker.startswith('KAIJU_'):
                            kaiju_index = int(marker.split('_')[1])
                            new_positions[kaiju_index] = (f, r_idx, c_idx)
                            self.game.marker_state[f][r_idx][c_idx] = None
            self.game.kaiju_positions = new_positions

