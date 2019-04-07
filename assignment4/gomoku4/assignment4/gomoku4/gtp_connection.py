"""
gtp_connection.py
Module for playing games of Go using GoTextProtocol

Parts of this code were originally based on the gtp module 
in the Deep-Go project by Isaac Henrion and Amos Storkey 
at the University of Edinburgh.
"""
import traceback
from sys import stdin, stdout, stderr
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, PASS, \
                       MAXSIZE, coord_to_point
import numpy as np
import re
import signal

class GtpConnection():

    def __init__(self, go_engine, board, debug_mode = False):
        """
        Manage a GTP connection for a Go-playing engine

        Parameters
        ----------
        go_engine:
            a program that can reply to a set of GTP commandsbelow
        board: 
            Represents the current board state.
        """
        self._debug_mode = debug_mode
        self.go_engine = go_engine
        self.board = board
        signal.signal(signal.SIGALRM, self.handler)
        #self.flag = 0
        self.commands = {
            "protocol_version": self.protocol_version_cmd,
            "quit": self.quit_cmd,
            "name": self.name_cmd,
            "boardsize": self.boardsize_cmd,
            "showboard": self.showboard_cmd,
            "clear_board": self.clear_board_cmd,
            "komi": self.komi_cmd,
            "version": self.version_cmd,
            "known_command": self.known_command_cmd,
            "genmove": self.genmove_cmd,
            "list_commands": self.list_commands_cmd,
            "play": self.play_cmd,
            "legal_moves": self.legal_moves_cmd,
            "gogui-rules_game_id": self.gogui_rules_game_id_cmd,
            "gogui-rules_board_size": self.gogui_rules_board_size_cmd,
            "gogui-rules_legal_moves": self.gogui_rules_legal_moves_cmd,
            "gogui-rules_side_to_move": self.gogui_rules_side_to_move_cmd,
            "gogui-rules_board": self.gogui_rules_board_cmd,
            "gogui-rules_final_result": self.gogui_rules_final_result_cmd,
            "gogui-analyze_commands": self.gogui_analyze_cmd,
            "timelimit": self.timelimit_cmd,
            "solve": self.solve_cmd,
            "list_solve_point": self.list_solve_point_cmd, # below is added for Gomoku3
            "policy": self.set_playout_policy, 
            "policy_moves": self.display_pattern_moves
        }
        self.timelimit=60

        # used for argument checking
        # values: (required number of arguments, 
        #          error message on argnum failure)
        self.argmap = {
            "boardsize": (1, 'Usage: boardsize INT'),
            "komi": (1, 'Usage: komi FLOAT'),
            "known_command": (1, 'Usage: known_command CMD_NAME'),
            "genmove": (1, 'Usage: genmove {w,b}'),
            "play": (2, 'Usage: play {b,w} MOVE'),
            "legal_moves": (1, 'Usage: legal_moves {w,b}'),
            "policy":(1, 'Usage: set playout policy {random, rule_based}')
        }
    
    def set_playout_policy(self, args):
        playout_policy=args[0]
        self.go_engine.set_playout_policy(playout_policy)
        self.respond()

    def display_pattern_moves(self, args):
        game_end, winner = self.board.check_game_end_gomoku()
        color=self.board.current_player
        if game_end:
            if winner == color:
                self.respond("")
            else:
                self.respond("")
            return
        all_moves=self.board.get_empty_points()
        if len(all_moves) == 0:
            self.respond('')
            return
        moveType, moves=self.go_engine.policy_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(moveType+' '+sorted_moves)

    def write(self, data):
        stdout.write(data) 

    def flush(self):
        stdout.flush()

    def start_connection(self):
        """
        Start a GTP connection. 
        This function continuously monitors standard input for commands.
        """
        line = stdin.readline()
        while line:
            self.get_cmd(line)
            line = stdin.readline()

    def get_cmd(self, command):
        """
        Parse command string and execute it
        """
        if len(command.strip(' \r\t')) == 0:
            return
        if command[0] == '#':
            return
        # Strip leading numbers from regression tests
        if command[0].isdigit():
            command = re.sub("^\d+", "", command).lstrip()

        elements = command.split()
        if not elements:
            return
        command_name = elements[0]; args = elements[1:]
        if self.has_arg_error(command_name, len(args)):
            return
        if command_name in self.commands:
            try:
                self.commands[command_name](args)
            except Exception as e:
                self.debug_msg("Error executing command {}\n".format(str(e)))
                self.debug_msg("Stack Trace:\n{}\n".
                               format(traceback.format_exc()))
                raise e
        else:
            self.debug_msg("Unknown command: {}\n".format(command_name))
            self.error('Unknown command')
            stdout.flush()

    def has_arg_error(self, cmd, argnum):
        """
        Verify the number of arguments of cmd.
        argnum is the number of parsed arguments
        """
        if cmd in self.argmap and self.argmap[cmd][0] != argnum:
            self.error(self.argmap[cmd][1])
            return True
        return False

    def debug_msg(self, msg):
        """ Write msg to the debug stream """
        if self._debug_mode:
            stderr.write(msg)
            stderr.flush()

    def error(self, error_msg):
        """ Send error msg to stdout """
        stdout.write('? {}\n\n'.format(error_msg))
        stdout.flush()

    def respond(self, response=''):
        """ Send response to stdout """
        stdout.write('= {}\n\n'.format(response))
        stdout.flush()

    def reset(self, size):
        """
        Reset the board to empty board of given size
        """
        self.board.reset(size)

    def board2d(self):
        return str(GoBoardUtil.get_twoD_board(self.board))
        
    def protocol_version_cmd(self, args):
        """ Return the GTP protocol version being used (always 2) """
        self.respond('2')

    def quit_cmd(self, args):
        """ Quit game and exit the GTP interface """
        self.respond()
        exit()

    def name_cmd(self, args):
        """ Return the name of the Go engine """
        self.respond(self.go_engine.name)

    def version_cmd(self, args):
        """ Return the version of the  Go engine """
        self.respond(self.go_engine.version)

    def clear_board_cmd(self, args):
        """ clear the board """
        self.reset(self.board.size)
        self.respond()

    def boardsize_cmd(self, args):
        """
        Reset the game with new boardsize args[0]
        """
        self.reset(int(args[0]))
        self.respond()

    def showboard_cmd(self, args):
        self.respond('\n' + self.board2d())

    def komi_cmd(self, args):
        """
        Set the engine's komi to args[0]
        """
        self.go_engine.komi = float(args[0])
        self.respond()

    def known_command_cmd(self, args):
        """
        Check if command args[0] is known to the GTP interface
        """
        if args[0] in self.commands:
            self.respond("true")
        else:
            self.respond("false")

    def list_commands_cmd(self, args):
        """ list all supported GTP commands """
        self.respond(' '.join(list(self.commands.keys())))

    def legal_moves_cmd(self, args):
        """
        List legal moves for color args[0] in {'b','w'}
        """
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)

    def play_cmd(self, args):
        """
        play a move args[1] for given color args[0] in {'b','w'}
        """
        try:
            board_color = args[0].lower()
            board_move = args[1]
            if board_color != "b" and board_color !="w":
                self.respond("illegal move: \"{}\" wrong color".format(board_color))
                return
            color = color_to_int(board_color)
            if args[1].lower() == 'pass':
                self.board.play_move(PASS, color)
                self.board.current_player = GoBoardUtil.opponent(color)
                self.respond()
                return
            coord = move_to_coord(args[1], self.board.size)
            if coord:
                move = coord_to_point(coord[0],coord[1], self.board.size)
            else:
                self.error("Error executing move {} converted from {}"
                           .format(move, args[1]))
                return
            if not self.board.play_move_gomoku(move, color):
                self.respond("illegal move: \"{}\" occupied".format(board_move))
                return
            else:
                self.debug_msg("Move: {}\nBoard:\n{}\n".
                                format(board_move, self.board2d()))
            self.respond()
        except Exception as e:
            self.respond('{}'.format(str(e)))

    def timelimit_cmd(self, args):
        self.timelimit = args[0]
        self.respond('')

    def handler(self, signum, fram):
        self.board = self.sboard
        raise Exception("unknown")

    def solve_cmd(self, args):
        try:
            self.sboard = self.board.copy()
            signal.alarm(int(self.timelimit)-1)
            winner,move = self.board.solve()
            self.board = self.sboard
            signal.alarm(0)
            if move != "NoMove":
                if move == None:
                    self.respond('{} {}'.format(winner, self.board._point_to_coord(move)))
                    return 
                self.respond('{} {}'.format(winner, format_point(point_to_coord(move, self.board.size))))
                return 
            self.respond('{}'.format(winner))
        except Exception as e:
            self.respond('{}'.format(str(e)))
#==========================================================================================
    def genmove_cmd(self, args):
        board_color = args[0].lower()
        color = color_to_int(board_color)
        game_end, winner = self.board.check_game_end_gomoku()
        if game_end:
            if winner == color:
                self.respond("pass")
            else:
                self.respond("resign")
            return

        flag = self.oplessthanX(color,2)
        if flag == 0:#more than 2
            score_c = self.Score(color)
            score_p = self.Score(3-color)
            #self.respond(score_c)
            score_c = self.Sort(score_c,1)
            score_p = self.Sort(score_p,2)

            x_P, y_P, max_P = self.Evaluate(score_p)
            x_C, y_C, max_C = self.Evaluate(score_c)
            if max_P>max_C and max_C<1000000:
                self.respond("1")
                row = x_P
                col = y_P
            else:
                row = x_C
                col = y_C

            move = coord_to_point(row+1,col+1,7)
        else:
            move = self.good_start(color)

        self.board.play_move_gomoku(move,color)
        move_coord = point_to_coord(move, self.board.size)
        move_as_string = format_point(move_coord)
        self.respond(move_as_string)

    def oplessthanX(self,color,x):
        count_oppoent = 0
        board2D = GoBoardUtil.get_twoD_board(self.board)
        size = self.board.size
        op = 3 - color
        for i in range(size):
            for j in range(size):
                if board2D[i][j] == op:
                    count_oppoent = count_oppoent + 1
                if count_oppoent >= x:
                    return 0
        return 1

    def good_start(self,color):
        board2D = GoBoardUtil.get_twoD_board(self.board)
        move = None
        mid = board2D[3][3]
        op = 3 - color 
        if mid == 0:
            move = coord_to_point(4,4,7) 
        elif (board2D[2][3] == op or board2D[3][4]== op) and board2D[2][4] == 0:
            move = coord_to_point(3,5,7) 
        elif (board2D[4][3] == op or board2D[3][2]== op) and board2D[4][2] == 0:
            move = coord_to_point(5,3,7)
        elif (board2D[2][2] == op or board2D[4][4]== op) and board2D[4][2] == 0:
            move = coord_to_point(5,3,7)
        elif (board2D[2][4] == op or board2D[4][2]== op) and board2D[2][2] == 0: 
            move = coord_to_point(3,3,7)
        else:
            if board2D[2][4] == 0:
                move = coord_to_point(3,5,7)
            elif board2D[4][2] == 0:
                move = coord_to_point(5,3,7)
            elif board2D[2][2] == 0:
                move = coord_to_point(3,3,7)
            elif board2D[4][4] == 0:
                move = coord_to_point(5,5,7)

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
    	#str1 = str(row)+","+str(col)+" : "+str(cons)
    	#self.respond(str1)

    	return cons
    def count(self,color,row,col,board2D,score,orig_row,orig_col,row_step,col_step,pos,depth):
        if col+col_step>= 0 and col +col_step <=6 and row+row_step>=0 and row+row_step<= 6:
            if board2D[row+row_step][col+col_step] != color:
                if board2D[row+row_step][col+col_step] == 0:
                    cons = self.checkfive(row,col,board2D,row_step,col_step,depth,color,row,col)
                    if cons == 5:
                        score[orig_row][orig_col][pos] += 1
                    else:
                        score[orig_row][orig_col][pos] = 0

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
                    #for col
                    # while col - 1 >=0: and board2D[row][col-1] == color:
                    #     if board2D[row][col-1] == color:
                    #         col -= 1
                    #         score[i][j][0] += 10
                    #     if col - 1 >= 0 and board2D[row][col-1] == 0:
                    #         score[i][j][0] += 1
                    #         break
                    #     if col - 1 >= 0 and board2D[row][col-1] == 3-color:
                    #         score[i][j][0] -= 2
                    #         break
                    # row = i
                    # col = j

                    # while col + 1 <= 6:
                    #     if board2D[row][col+1] == color:
                    #         col += 1
                    #         score[i][j][0] += 10
                    #     if col + 1 <= 6 and board2D[row][col+1] == 0:
                    #         score[i][j][0] += 1
                    #         break
                    #     if col + 1 <= 6 and board2D[row][col+1] == 3-color:
                    #         score[i][j][0] -= 2
                    #         break
                    # row = i
                    # col = j
                    # #for row
                    # while row - 1 >=0:
                    #     if board2D[row-1][col] == color:
                    #         row -= 1
                    #         score[i][j][1] += 10
                    #     if row - 1 >= 0 and board2D[row-1][col] == 0:
                    #         score[i][j][1] += 1
                    #         break
                    #     if row - 1 >= 0 and board2D[row-1][col] == 3-color:
                    #         score[i][j][1] -= 2
                    #         break
                    # row = i
                    # col = j

                    # while row + 1 <=6:
                    #     if board2D[row+1][col] == color:
                    #         row += 1
                    #         score[i][j][1] += 10
                    #     if row + 1 <= 6 and board2D[row+1][col] == 0:
                    #         score[i][j][1] += 1
                    #         break
                    #     if row + 1 <= 6 and board2D[row+1][col] == 3-color:
                    #         score[i][j][1] -= 2
                    #         break
                    # row = i
                    # col = j

                    # #for diag 
                    # while row + 1 <= 6 and col - 1 >= 0:
                    #     if board2D[row+1][col-1] == color:
                    #         row += 1
                    #         col -= 1
                    #         score[i][j][2] += 10
                    #     if row + 1 <= 6 and col - 1 >= 0 and board2D[row+1][col-1] == 0:
                    #         score[i][j][2] += 1
                    #         break
                    #     if row + 1 <= 6 and col - 1 >= 0 and board2D[row+1][col-1] == 3-color:
                    #         score[i][j][2] -= 2
                    #         break
                    # row = i
                    # col = j

                    # while row - 1 >=0 and col +1 <= 6:
                    #     if board2D[row-1][col+1] == color:
                    #         row -= 1
                    #         col += 1
                    #         score[i][j][2] += 10
                    #     if row - 1 >=0 and col +1 <= 6 and board2D[row-1][col+1] == 0:
                    #         score[i][j][2] += 1
                    #         break
                    #     if row - 1 >=0 and col +1 <= 6 and board2D[row-1][col+1] == 3-color:
                    #         score[i][j][2] -= 2
                    #         break

                    # row = i
                    # col = j

                    # #for diag 
                    # while row + 1 <= 6 and col + 1 <= 6:
                    #     if board2D[row+1][col+1] == color:
                    #         row += 1
                    #         col += 1
                    #         score[i][j][3] += 10
                    #     if row + 1 <= 6 and col + 1 <= 6 and board2D[row+1][col+1] == 0:
                    #         score[i][j][3] += 1
                    #         break
                    #     if row + 1 <= 6 and col + 1 <= 6 and board2D[row+1][col+1] == 3-color:
                    #         break
                    #         score[i][j][3] -= 2

                    # row = i
                    # col = j

                    # while row - 1 >=0 and col -1 <= 6:
                    #     if board2D[row-1][col-1] == color:
                    #         row -= 1
                    #         col -= 1
                    #         score[i][j][3] += 10
                    #     if row - 1 >=0 and col -1 <= 6 and board2D[row-1][col-1] == 0:
                    #         score[i][j][3] += 1
                    #         break
                    #     if row - 1 >=0 and col -1 <= 6 and board2D[row-1][col-1] == 3-color:
                    #         score[i][j][3] -= 2
                    #         break
        return score
#++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++ 
    def gogui_rules_game_id_cmd(self, args):
        self.respond("Gomoku")
    
    def gogui_rules_board_size_cmd(self, args):
        self.respond(str(self.board.size))
    """
    def legal_moves_cmd(self, args):
        #List legal moves for color args[0] in {'b','w'}
        board_color = args[0].lower()
        color = color_to_int(board_color)
        moves = GoBoardUtil.generate_legal_moves(self.board, color)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)
    """

    def gogui_rules_legal_moves_cmd(self, args):
        game_end,_ = self.board.check_game_end_gomoku()
        if game_end:
            self.respond()
            return
        moves = GoBoardUtil.generate_legal_moves_gomoku(self.board)
        gtp_moves = []
        for move in moves:
            coords = point_to_coord(move, self.board.size)
            gtp_moves.append(format_point(coords))
        sorted_moves = ' '.join(sorted(gtp_moves))
        self.respond(sorted_moves)
    
    def gogui_rules_side_to_move_cmd(self, args):
        color = "black" if self.board.current_player == BLACK else "white"
        self.respond(color)
    
    def gogui_rules_board_cmd(self, args):
        size = self.board.size
        str = ''
        for row in range(size-1, -1, -1):
            start = self.board.row_start(row + 1)
            for i in range(size):
                point = self.board.board[start + i]
                if point == BLACK:
                    str += 'X'
                elif point == WHITE:
                    str += 'O'
                elif point == EMPTY:
                    str += '.'
                else:
                    assert False
            str += '\n'
        self.respond(str)
    
    def gogui_rules_final_result_cmd(self, args):
        game_end, winner = self.board.check_game_end_gomoku()
        moves = self.board.get_empty_points()
        board_full = (len(moves) == 0)
        if board_full and not game_end:
            self.respond("draw")
            return
        if game_end:
            color = "black" if winner == BLACK else "white"
            self.respond(color)
        else:
            self.respond("unknown")

    def gogui_analyze_cmd(self, args):
        self.respond("pstring/Legal Moves For ToPlay/gogui-rules_legal_moves\n"
                     "pstring/Side to Play/gogui-rules_side_to_move\n"
                     "pstring/Final Result/gogui-rules_final_result\n"
                     "pstring/Board Size/gogui-rules_board_size\n"
                     "pstring/Rules GameID/gogui-rules_game_id\n"
                     "pstring/Show Board/gogui-rules_board\n"
                     )

    def list_solve_point_cmd(self, args):
        self.respond(self.board.list_solve_point())

def point_to_coord(point, boardsize):
    """
    Transform point given as board array index 
    to (row, col) coordinate representation.
    Special case: PASS is not transformed
    """
    if point == PASS:
        return PASS
    else:
        NS = boardsize + 1
        return divmod(point, NS)

def format_point(move):
    """
    Return move coordinates as a string such as 'a1', or 'pass'.
    """
    column_letters = "ABCDEFGHJKLMNOPQRSTUVWXYZ"
    #column_letters = "abcdefghjklmnopqrstuvwxyz"
    if move == PASS:
        return "pass"
    row, col = move
    if not 0 <= row < MAXSIZE or not 0 <= col < MAXSIZE:
        raise ValueError
    return column_letters[col - 1]+ str(row) 
    
def move_to_coord(point_str, board_size):
    """
    Convert a string point_str representing a point, as specified by GTP,
    to a pair of coordinates (row, col) in range 1 .. board_size.
    Raises ValueError if point_str is invalid
    """
    if not 2 <= board_size <= MAXSIZE:
        raise ValueError("board_size out of range")
    s = point_str.lower()
    if s == "pass":
        return PASS
    try:
        col_c = s[0]
        if (not "a" <= col_c <= "z") or col_c == "i":
            raise ValueError
        col = ord(col_c) - ord("a")
        if col_c < "i":
            col += 1
        row = int(s[1:])
        if row < 1:
            raise ValueError
    except (IndexError, ValueError):
        raise ValueError("illegal move: \"{}\" wrong coordinate".format(s))
    if not (col <= board_size and row <= board_size):
        raise ValueError("illegal move: \"{}\" wrong coordinate".format(s))
    return row, col

def color_to_int(c):
    """convert character to the appropriate integer code"""
    color_to_int = {"b": BLACK , "w": WHITE, "e": EMPTY, 
                    "BORDER": BORDER}
    return color_to_int[c] 
