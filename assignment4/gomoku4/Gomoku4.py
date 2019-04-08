#!/usr/bin/env python
#/usr/local/bin/python3
# Set the path to your python3 above

from gtp_connection import GtpConnection
from board_util import GoBoardUtil, EMPTY
from simple_board import SimpleGoBoard

import random
import numpy as np

def undo(board,move):
    board.board[move]=EMPTY
    board.current_player=GoBoardUtil.opponent(board.current_player)

def play_move(board, move, color):
    board.play_move_gomoku(move, color)

def game_result(board):
    game_end, winner = board.check_game_end_gomoku()
    moves = board.get_empty_points()
    board_full = (len(moves) == 0)
    if game_end:
        #return 1 if winner == board.current_player else -1
        return winner
    if board_full:
        return 'draw'
    return None

class GomokuSimulationPlayer(object):
    """
    For each move do `n_simualtions_per_move` playouts,
    then select the one with best win-rate.
    playout could be either random or rule_based (i.e., uses pre-defined patterns) 
    """
    def __init__(self, n_simualtions_per_move=10, playout_policy='rule_based', board_size=7):
        assert(playout_policy in ['random', 'rule_based'])
        self.n_simualtions_per_move=n_simualtions_per_move
        self.board_size=board_size
        self.playout_policy=playout_policy

        #NOTE: pattern has preference, later pattern is ignored if an earlier pattern is found
        self.pattern_list=['Win', 'BlockWin', 'OpenFour', 'BlockOpenFour', 'Random']

        self.name="Gomoku3"
        self.version = 3.0
        self.best_move=None

    def get_move_score_based(self,color):
        score_c = self.Score(color)
        score_p = self.Score(3-color)
        #self.respond(score_c)
        score_c = self.Sort(score_c,1)
        score_p = self.Sort(score_p,2)

        x_P, y_P, max_P = self.Evaluate(score_p)
        x_C, y_C, max_C = self.Evaluate(score_c)
        if max_P>max_C and max_C<1000000:
            #self.respond("1")
            row = x_P
            col = y_P
        else:
            row = x_C
            col = y_C
        move = coord_to_point(row+1,col+1,7)
        return move

    def Evaluate(self,score):
        for i in range(7):
            for j in range(7):
                if score[i][j][0] == 4:
                    return i, j, 1000000
                score[i][j][4] = score[i][j][0]*1000 + score[i][j][1]*100 + score[i][j][2]*10 + score[i][j][3]
        row = 0
        col = 0
        max = 0
        for i in range(7):
            for j in range(7):
                if max < score[i][j][4]:
                    max = score[i][j][4]
                    row = i
                    col = j
        return row, col, max

    def Sort(self, score,type):
        for row in score:
            for point in row:
                if type == 1:
                    max_s = max(point[0],point[1],point[2],point[3])
                    point[0] = max_s
                    point[1] = max_s
                    point[2] = max_s
                    point[3] = max_s
                if type == 2:
                    max_s = max(point[0],point[1],point[2],point[3])
                    if max_s <= 43:
                        point[0] = 0
                        point[1] = 0
                        point[2] = 0
                        point[3] = 0
                    else:
                        point[0] = max_s
                        point[1] = max_s
                        point[2] = max_s
                        point[3] = max_s
        return score
    
    def checkcol(self,color,row,col,board2D,score):
        score = self.count(color,row,col,board2D,score,row,col,0,-1,0,0)
        score = self.count(color,row,col,board2D,score,row,col,0,1,0,0)
        return score
    def checkrow(self,color,row,col,board2D,score):
        score = self.count(color,row,col,board2D,score,row,col,-1,0,1,0)
        score = self.count(color,row,col,board2D,score,row,col,1,0,1,0)
        return score
    def checkdig1(self,color,row,col,board2D,score):
        score = self.count(color,row,col,board2D,score,row,col,1,-1,2,0)
        score = self.count(color,row,col,board2D,score,row,col,-1,1,2,0)
        return score
    def checkdig2(self,color,row,col,board2D,score):
        score = self.count(color,row,col,board2D,score,row,col,-1,-1,3,0)
        score = self.count(color,row,col,board2D,score,row,col,1,1,3,0)
        return score
    def checkfive(self,row,col,board2D,row_step,col_step,depth,color,orig_row,orig_col):
        cons = depth
        while col+col_step>= 0 and col +col_step <=6 and row+row_step>=0 and row+row_step<= 6:
            if (board2D[row+row_step][col+col_step] == 0 or board2D[row+row_step][col+col_step] == color) and cons < 5:
                cons += 1
                row = row+row_step
                row = col+col_step
            else:
                break
        row = orig_row
        col = orig_col
        while col-col_step>= 0 and col -col_step <=6 and row-row_step>=0 and row-row_step<= 6:
            if (board2D[row-row_step][col-col_step] == 0 or board2D[row-row_step][col-col_step] == color) and cons < 5:
                cons += 1
                row = row-row_step
                row = col-col_step
            else:
                break
        return cons
    def count(self,color,row,col,board2D,score,orig_row,orig_col,row_step,col_step,pos,depth):
        if col+col_step>= 0 and col +col_step <=6 and row+row_step>=0 and row+row_step<= 6:
            if board2D[row+row_step][col+col_step] != color:
                if board2D[row+row_step][col+col_step] == 0:
                    cons = self.checkfive(row,col,board2D,row_step,col_step,depth,color,row,col)
                    if cons == 5:
                        score[orig_row][orig_col][pos] += 1
                    else:
                        score[orig_row][orig_col][pos] -= 1

                if board2D[row+row_step][col+col_step] == 3-color:
                    score[orig_row][orig_col][pos] -= 2
                return score
            else:
                #self.respond(score[orig_row][orig_col])
                score[orig_row][orig_col][pos] += 20
                self.count(color,row+row_step,col+col_step,board2D,score,orig_row,orig_col,row_step,col_step,pos,depth+1)
        return score
    

    def Score(self,color):
        board2D = GoBoardUtil.get_twoD_board(self.board)
        score = [[[0 for dirc in range(5)] for col in range(7)] for row in range(7)]
        
        for i in range(7):
            for j in range(7):
                if board2D[i][j] == 0:
                    row = i
                    col = j
                    score = self.checkcol(color,row,col,board2D,score)
                    score = self.checkrow(color,row,col,board2D,score)
                    score = self.checkdig1(color,row,col,board2D,score)
                    score = self.checkdig2(color,row,col,board2D,score)
              
        return score

    def set_playout_policy(self, playout_policy='rule_based'):
        assert(playout_policy in ['random', 'rule_based'])
        self.playout_policy=playout_policy

    def _random_moves(self, board, color_to_play):
        return GoBoardUtil.generate_legal_moves_gomoku(board)
    
    def policy_moves(self, board, color_to_play):
        if(self.playout_policy=='random'):
            return "Random", self._random_moves(board, color_to_play)
        else:
            assert(self.playout_policy=='rule_based')
            assert(isinstance(board, SimpleGoBoard))
            ret=board.get_pattern_moves()
            if ret is None:
                #return "Random", self._random_moves(board, color_to_play)
                return "score_based", self.get_move_score_based(color_to_play)
            movetype_id, moves=ret
            return self.pattern_list[movetype_id], moves
    
    def _do_playout(self, board, color_to_play):
        res=game_result(board)
        simulation_moves=[]
        while(res is None):
            _ , candidate_moves = self.policy_moves(board, board.current_player)
            playout_move=random.choice(candidate_moves)
            play_move(board, playout_move, board.current_player)
            simulation_moves.append(playout_move)
            res=game_result(board)
        for m in simulation_moves[::-1]:
            undo(board, m)
        if res == color_to_play:
            return 1.0
        elif res == 'draw':
            return 0.0
        else:
            assert(res == GoBoardUtil.opponent(color_to_play))
            return -1.0

    def get_move(self, board, color_to_play):
        """
        The genmove function called by gtp_connection
        """
        moves=GoBoardUtil.generate_legal_moves_gomoku(board)
        toplay=board.current_player
        best_result, best_move=-1.1, None
        best_move=moves[0]
        wins = np.zeros(len(moves))
        visits = np.zeros(len(moves))
        while True:
            for i, move in enumerate(moves):
                play_move(board, move, toplay)
                res=game_result(board)
                if res == toplay:
                    undo(board, move)
                    #This move is a immediate win
                    self.best_move=move
                    return move
                ret=self._do_playout(board, toplay)
                wins[i] += ret
                visits[i] += 1
                win_rate = wins[i] / visits[i]
                if win_rate > best_result:
                    best_result=win_rate
                    best_move=move
                    self.best_move=best_move
                undo(board, move)
        assert(best_move is not None)
        return best_move

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(GomokuSimulationPlayer(), board)
    con.start_connection()

if __name__=='__main__':
    run()
