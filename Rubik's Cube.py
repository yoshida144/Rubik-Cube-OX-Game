from scene import *
import random

class CubeTicTacToeScene(Scene):
    def setup(self):
        self.background_color = '#F1F1F1'
        neutral_color = 'white'
        self.COLORS = {
            'U': neutral_color, 'D': neutral_color, 'F': neutral_color,
            'B': neutral_color, 'R': neutral_color, 'L': neutral_color,
        }
        self.FACE_KEYS = ['U', 'L', 'F', 'R', 'B', 'D']
        
        self.tile_size = 45
        self.gap = 4
        self.face_gap = 15
        self.btn_size = 40
        
        self.buttons = {}
        self.cube_state = {}
        
        self.marker_state = {}
        self.current_player = 'O'
        self.game_over = False
        self.winner = None
        self.status_message = "Oのターン"
        
        self.reset_game()

    def reset_game(self):
        for key in self.FACE_KEYS:
            self.cube_state[key] = [[self.COLORS[key]] * 3 for _ in range(3)]
            self.marker_state[key] = [[None] * 3 for _ in range(3)]
        
        self.current_player = 'O'
        self.game_over = False
        self.winner = None
        self.status_message = "Oのターン"
        self.cracker_animation = None

    def draw(self):
        self.rect_color1 = '#404040'
        self.rect_color2 = '#505050'
        fill(self.rect_color1)
        rect(340,190,840,640)
        fill(self.rect_color2)
        rect(350,200,820,620)
        
        center_x, center_y = self.size.w / 2, self.size.h / 2
        face_total_size = self.tile_size * 3 + self.gap * 2
        
        face_offsets = {
            'U': (0, 1), 'L': (-1, 0), 'F': (0, 0),
            'R': (1, 0), 'B': (2, 0), 'D': (0, -1)
        }
        
        self.face_origins = {}
        for face_key, (offset_x, offset_y) in face_offsets.items():
            origin_x = center_x + offset_x * (face_total_size + self.face_gap) - face_total_size / 2
            origin_y = center_y + offset_y * (face_total_size + self.face_gap) - face_total_size / 2
            self.face_origins[face_key] = (origin_x, origin_y)
            
            if face_key == 'F':
                glow_padding = 5
                fill('#00A0FF')
                stroke_weight(0)
                rect(origin_x - glow_padding, 
                     origin_y - glow_padding, 
                     face_total_size + glow_padding * 2, 
                     face_total_size + glow_padding * 2)

            self.draw_face(face_key, origin_x, origin_y, self.marker_state[face_key])
        
        self.draw_buttons(self.face_origins, face_total_size)
        
        tint('black')
        text(self.status_message, 'Helvetica-Bold', 24, self.size.w / 2, self.size.h - 40)
        
        if self.game_over and self.winner and self.cracker_animation:
            tint(1, 1, 1, 1)
            emoji_size = 100
            padding = 50
            text(self.cracker_animation, 'AppleColorEmoji', emoji_size, padding, self.size.h - padding)
            text(self.cracker_animation, 'AppleColorEmoji', emoji_size, self.size.w - padding, self.size.h - padding)
            
        tint(1,1,1,1)

    def draw_face(self, face_key, origin_x, origin_y, face_markers):
        face_colors = self.cube_state[face_key]
        for row in range(3):
            for col in range(3):
                color = face_colors[2 - row][col]
                fill(color)
                stroke('grey')
                stroke_weight(1)
                px = origin_x + col * (self.tile_size + self.gap)
                py = origin_y + row * (self.tile_size + self.gap)
                rect(px, py, self.tile_size, self.tile_size)
                
                marker = face_markers[2 - row][col]
                if marker:
                    if marker == 'O':
                        tint('#FF0000')
                    elif marker == 'X':
                        tint('#0000FF')
                    else:
                        tint('white') 
                    
                    text(marker, 'Helvetica-Bold', 36, px + self.tile_size/2, py + self.tile_size/2)

    def draw_buttons(self, face_origins, face_size):
        self.buttons.clear()
        btn_padding = self.btn_size/2 + 5
        u_origin_x, u_origin_y = face_origins['U']
        d_origin_x, d_origin_y = face_origins['D']
        for i in range(3):
            px = u_origin_x + i * (self.tile_size + self.gap) + self.tile_size / 2
            py_up = u_origin_y + face_size + btn_padding
            btn_rect_up = Rect(px - self.btn_size/2, py_up - self.btn_size/2, self.btn_size, self.btn_size)
            fill('#c0c0c0'); rect(*btn_rect_up); tint('black'); text('↓', 'Helvetica-Bold', 24, px, py_up);
            self.buttons[('top', i)] = btn_rect_up
            py_down = d_origin_y - btn_padding
            btn_rect_down = Rect(px - self.btn_size/2, py_down - self.btn_size/2, self.btn_size, self.btn_size)
            fill('#c0c0c0'); rect(*btn_rect_down); tint('black'); text('↑', 'Helvetica-Bold', 24, px, py_down);
            self.buttons[('bottom', i)] = btn_rect_down
        l_origin_x, l_origin_y = face_origins['L']
        b_origin_x, b_origin_y = face_origins['B']
        for i in range(3):
            py = l_origin_y + i * (self.tile_size + self.gap) + self.tile_size / 2
            px_left = l_origin_x - btn_padding
            btn_rect_left = Rect(px_left - self.btn_size/2, py - self.btn_size/2, self.btn_size, self.btn_size)
            fill('#c0c0c0'); rect(*btn_rect_left); tint('black'); text('→', 'Helvetica-Bold', 24, px_left, py);
            self.buttons[('left', 2-i)] = btn_rect_left
            px_right = b_origin_x + face_size + btn_padding
            btn_rect_right = Rect(px_right - self.btn_size/2, py - self.btn_size/2, self.btn_size, self.btn_size)
            fill('#c0c0c0'); rect(*btn_rect_right); tint('black'); text('←', 'Helvetica-Bold', 24, px_right, py); 
            self.buttons[('right', 2-i)] = btn_rect_right

    def touch_began(self, touch):
        if self.game_over:
            face_size = self.tile_size * 3 + self.gap * 2
            f_origin_x, f_origin_y = self.face_origins['F']
            f_face_rect = Rect(f_origin_x, f_origin_y, face_size, face_size)
            if touch.location in f_face_rect:
                self.reset_game()
            return
        action_taken = False
        for key, rect_val in self.buttons.items():
            if touch.location in rect_val:
                bank, index = key
                self.handle_rotate(bank, index)
                action_taken = True
                break
        if not action_taken:
            for face_key, (origin_x, origin_y) in self.face_origins.items():
                face_size = self.tile_size * 3 + self.gap * 2
                face_rect = Rect(origin_x, origin_y, face_size, face_size)
                if touch.location in face_rect:
                    col = int((touch.location.x - origin_x) / (self.tile_size + self.gap))
                    row = int((touch.location.y - origin_y) / (self.tile_size + self.gap))
                    if self.marker_state[face_key][2-row][col] is None:
                        self.marker_state[face_key][2-row][col] = self.current_player
                        action_taken = True
                    break
        if action_taken:
            self.end_turn()

    def end_turn(self):
        self.check_win()
        if not self.game_over:
            self.current_player = 'X' if self.current_player == 'O' else 'O'
            self.status_message = f"{self.current_player}のターン"

    def check_win(self):
        board = self.marker_state['F']
        lines = []
        for i in range(3):
            lines.append([board[i][0], board[i][1], board[i][2]])
            lines.append([board[0][i], board[1][i], board[2][i]])
        lines.append([board[0][0], board[1][1], board[2][2]])
        lines.append([board[0][2], board[1][1], board[2][0]])
        for line in lines:
            if line[0] and line[0] == line[1] == line[2]:
                self.winner = line[0]
                self.game_over = True
                self.status_message = f"{self.winner} の勝利! 中央をタップしてリセット"
                self.cracker_animation = "🎉"
                return
    
    def handle_rotate(self, bank, index):
        move = ""
        if bank == 'left':
            if index == 0:      # 上ボタン
                move = "U'"
            elif index == 1:    # 中央ボタン
                move = "E'"
            elif index == 2:    # 下ボタン
                move = "D"
        elif bank == 'right':
            if index == 0:      # 上ボタン
                move = "U"
            elif index == 1:    # 中央ボタン
                move = "E"
            elif index == 2:    # 下ボタン
                move = "D'"
        elif bank == 'top':     # 上の↓ボタン群
            if index == 0:      # 左ボタン
                move = "L'"
            elif index == 1:    # 中央ボタン
                move = "M"
            elif index == 2:    # 右ボタン
                move = "R"
        elif bank == 'bottom':  # 下の↑ボタン群
            if index == 0:      # 左ボタン
                move = "L"
            elif index == 1:    # 中央ボタン
                move = "M'"
            elif index == 2:    # 右ボタン
                move = "R'"
            
        if move:
            self.rotate(move)

    def rotate_face(self, face_key, clockwise=True):
        for state in [self.cube_state, self.marker_state]:
            face = state[face_key]
            if clockwise:
                state[face_key] = [list(row) for row in zip(*face[::-1])]
            else:
                state[face_key] = [list(row) for row in zip(*face)][::-1]

    def rotate(self, move):
        s = self.cube_state
        m = self.marker_state
        
        face_moves = {"U": ('U', True), "U'": ('U', False), "D": ('D', True), "D'": ('D', False),
                      "R": ('R', False), "R'": ('R', True), "L": ('L', False), "L'": ('L', True),
                      "F": ('F', True), "F'": ('F', False), "B": ('B', True), "B'": ('B', False)}
        
        if move in face_moves:
            face, clockwise = face_moves[move]
            self.rotate_face(face, clockwise)

        if move in ("D", "D'"):
            temp_s_f, temp_m_f = s['F'][2][:], m['F'][2][:]
            temp_s_r, temp_m_r = s['R'][2][:], m['R'][2][:]
            temp_s_b, temp_m_b = s['B'][2][:], m['B'][2][:]
            temp_s_l, temp_m_l = s['L'][2][:], m['L'][2][:]
            if move == "D": 
                s['R'][2], m['R'][2] = temp_s_f, temp_m_f
                s['F'][2], m['F'][2] = temp_s_l, temp_m_l
                s['L'][2], m['L'][2] = temp_s_b, temp_m_b
                s['B'][2], m['B'][2] = temp_s_r, temp_m_r
            else: 
                s['L'][2], m['L'][2] = temp_s_f, temp_m_f
                s['F'][2], m['F'][2] = temp_s_r, temp_m_r
                s['R'][2], m['R'][2] = temp_s_b, temp_m_b
                s['B'][2], m['B'][2] = temp_s_l, temp_m_l

        elif move in ("U", "U'"):
            temp_s_f, temp_m_f = s['F'][0][:], m['F'][0][:]
            temp_s_r, temp_m_r = s['R'][0][:], m['R'][0][:]
            temp_s_b, temp_m_b = s['B'][0][:], m['B'][0][:]
            temp_s_l, temp_m_l = s['L'][0][:], m['L'][0][:]
            if move == "U":
                s['L'][0], m['L'][0] = temp_s_f, temp_m_f
                s['F'][0], m['F'][0] = temp_s_r, temp_m_r
                s['R'][0], m['R'][0] = temp_s_b, temp_m_b
                s['B'][0], m['B'][0] = temp_s_l, temp_m_l
            else: 
                s['R'][0], m['R'][0] = temp_s_f, temp_m_f
                s['F'][0], m['F'][0] = temp_s_l, temp_m_l
                s['L'][0], m['L'][0] = temp_s_b, temp_m_b
                s['B'][0], m['B'][0] = temp_s_r, temp_m_r

        elif move in ("R", "R'"):
            temp_s_u, temp_m_u = [s['U'][i][2] for i in range(3)], [m['U'][i][2] for i in range(3)]
            temp_s_f, temp_m_f = [s['F'][i][2] for i in range(3)], [m['F'][i][2] for i in range(3)]
            temp_s_d, temp_m_d = [s['D'][i][2] for i in range(3)], [m['D'][i][2] for i in range(3)]
            temp_s_b, temp_m_b = [s['B'][i][0] for i in range(3)], [m['B'][i][0] for i in range(3)]
            if move == "R":
                for i in range(3):
                    s['F'][i][2], m['F'][i][2] = temp_s_u[i], temp_m_u[i]
                    s['D'][i][2], m['D'][i][2] = temp_s_f[i], temp_m_f[i]
                    s['B'][2-i][0], m['B'][2-i][0] = temp_s_d[i], temp_m_d[i]
                    s['U'][i][2], m['U'][i][2] = temp_s_b[2-i], temp_m_b[2-i]
            else: 
                for i in range(3):
                    s['B'][2-i][0], m['B'][2-i][0] = temp_s_u[i], temp_m_u[i]
                    s['D'][i][2], m['D'][i][2] = temp_s_b[2-i], temp_m_b[2-i]
                    s['F'][i][2], m['F'][i][2] = temp_s_d[i], temp_m_d[i]
                    s['U'][i][2], m['U'][i][2] = temp_s_f[i], temp_m_f[i]

        elif move in ("L", "L'"):
            temp_s_u, temp_m_u = [s['U'][i][0] for i in range(3)], [m['U'][i][0] for i in range(3)]
            temp_s_f, temp_m_f = [s['F'][i][0] for i in range(3)], [m['F'][i][0] for i in range(3)]
            temp_s_d, temp_m_d = [s['D'][i][0] for i in range(3)], [m['D'][i][0] for i in range(3)]
            temp_s_b, temp_m_b = [s['B'][i][2] for i in range(3)], [m['B'][i][2] for i in range(3)]
            if move == "L":
                for i in range(3):
                    s['B'][2-i][2], m['B'][2-i][2] = temp_s_u[i], temp_m_u[i]
                    s['D'][i][0], m['D'][i][0] = temp_s_b[2-i], temp_m_b[2-i]
                    s['F'][i][0], m['F'][i][0] = temp_s_d[i], temp_m_d[i]
                    s['U'][i][0], m['U'][i][0] = temp_s_f[i], temp_m_f[i]
            else: 
                for i in range(3):
                    s['F'][i][0], m['F'][i][0] = temp_s_u[i], temp_m_u[i]
                    s['D'][i][0], m['D'][i][0] = temp_s_f[i], temp_m_f[i]
                    s['B'][2-i][2], m['B'][2-i][2] = temp_s_d[i], temp_m_d[i]
                    s['U'][i][0], m['U'][i][0] = temp_s_b[2-i], temp_m_b[2-i]

        elif move in ("M", "M'"):
            temp_s_u, temp_m_u = [s['U'][i][1] for i in range(3)], [m['U'][i][1] for i in range(3)]
            temp_s_f, temp_m_f = [s['F'][i][1] for i in range(3)], [m['F'][i][1] for i in range(3)]
            temp_s_d, temp_m_d = [s['D'][i][1] for i in range(3)], [m['D'][i][1] for i in range(3)]
            temp_s_b, temp_m_b = [s['B'][i][1] for i in range(3)], [m['B'][i][1] for i in range(3)]
            if move == "M":
                for i in range(3):
                    s['F'][i][1], m['F'][i][1] = temp_s_u[i], temp_m_u[i]
                    s['D'][i][1], m['D'][i][1] = temp_s_f[i], temp_m_f[i]
                    s['B'][2-i][1], m['B'][2-i][1] = temp_s_d[i], temp_m_d[i]
                    s['U'][i][1], m['U'][i][1] = temp_s_b[2-i], temp_m_b[2-i]
            else: 
                for i in range(3):
                    s['B'][2-i][1], m['B'][2-i][1] = temp_s_u[i], temp_m_u[i]
                    s['D'][i][1], m['D'][i][1] = temp_s_b[2-i], temp_m_b[2-i]
                    s['F'][i][1], m['F'][i][1] = temp_s_d[i], temp_m_d[i]
                    s['U'][i][1], m['U'][i][1] = temp_s_f[i], temp_m_f[i]

        elif move in ("E", "E'"):
            temp_s_f, temp_m_f = s['F'][1][:], m['F'][1][:]
            temp_s_r, temp_m_r = s['R'][1][:], m['R'][1][:]
            temp_s_b, temp_m_b = s['B'][1][:], m['B'][1][:]
            temp_s_l, temp_m_l = s['L'][1][:], m['L'][1][:]
            if move == "E": 
                s['L'][1], m['L'][1] = temp_s_f, temp_m_f
                s['B'][1], m['B'][1] = temp_s_l, temp_m_l
                s['R'][1], m['R'][1] = temp_s_b, temp_m_b
                s['F'][1], m['F'][1] = temp_s_r, temp_m_r
            else: 
                s['R'][1], m['R'][1] = temp_s_f, temp_m_f
                s['B'][1], m['B'][1] = temp_s_r, temp_m_r
                s['L'][1], m['L'][1] = temp_s_b, temp_m_b
                s['F'][1], m['F'][1] = temp_s_l, temp_m_l

# 実行
if __name__ == '__main__':
    run(CubeTicTacToeScene())
