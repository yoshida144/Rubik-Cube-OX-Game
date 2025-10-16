# game_logic.py

# ===================================================================================
# ゲームの「ロジック(ルールや状態管理)」を担当するファイルです。
# - キューブの各マスの色やマークの状態
# - 怪獣や卵の位置情報
# - キューブの回転処理
# といった、「ゲームのデータ」とその操作を専門に扱います。
# ===================================================================================

import copy
import random
import math
from constants import *

class GameLogic:
    """
    ゲームの状態(データ)と、それを変更するルールを管理するクラス。
    """
    def __init__(self):
        # ... (以下、初期化処理)
        self.cube_state = {}
        self.marker_state = {}
        self.kaiju_positions = []
        self.egg_positions = {}
        self.total_kaiju_moves = 0
        self.reset()

    def reset(self):
        # ... (ゲームの状態を全て初期化する)
        for key in FACE_KEYS:
            self.cube_state[key] = [[COLORS[key]] * 3 for _ in range(3)]
            self.marker_state[key] = [[None] * 3 for _ in range(3)]
        self.kaiju_positions.clear()
        self.egg_positions.clear()
        self.total_kaiju_moves = 0

    def place_kaiju(self, num_kaiju):
        # ... (指定された数の怪獣をルールに従って配置する)
        self.kaiju_positions.clear()
        f_spots = [('F', r, c) for r in range(3) for c in range(3)]
        other_spots = [(f, r, c) for f in FACE_KEYS if f != 'F' for r in range(3) for c in range(3)]
        random.shuffle(f_spots); random.shuffle(other_spots)

        num_on_f = min(num_kaiju, MAX_KAIJU_ON_F_FACE)
        self.kaiju_positions.extend(f_spots[:num_on_f])
        
        remaining = num_kaiju - num_on_f
        if remaining > 0:
            self.kaiju_positions.extend(other_spots[:remaining])

        for face, r, c in self.kaiju_positions:
            self.marker_state[face][r][c] = None

    def rotate_face(self, face_key, clockwise=True):
        # ... (指定された「面」だけを90度回転させる)
        for state in [self.cube_state, self.marker_state]:
            face = state[face_key]
            if clockwise: state[face_key] = [list(row) for row in zip(*face[::-1])]
            else: state[face_key] = [list(row) for row in zip(*face)][::-1]

    def rotate(self, move):
        # ... (指定された「層」(U, D, Mなど)を回転させる複雑な処理)
        s, m = self.cube_state, self.marker_state
        face_moves = {"U":('U',True), "U'":('U',False), "D":('D',True), "D'":('D',False), "R":('R',False), "R'":('R',True), "L":('L',False), "L'":('L',True), "F":('F',True), "F'":('F',False), "B":('B',True), "B'":('B',False)}
        if move in face_moves: face, clockwise = face_moves[move]; self.rotate_face(face, clockwise)
        # (以下、各層の回転ロジックは元のコードと同じ)
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
