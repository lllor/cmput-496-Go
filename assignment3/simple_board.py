"""
simple_board.py

Implements a basic Go board with functions to:
- initialize to a given board size
- check if a move is legal
- play a move

The board uses a 1-dimensional representation with padding
"""
import random
import numpy as np
from board_util import GoBoardUtil, BLACK, WHITE, EMPTY, BORDER, \
                       PASS, is_black_white, coord_to_point, where1d, \
                       MAXSIZE, NULLPOINT

class SimpleGoBoard(object):
#=====================================================================================
#=====================================================================================

    def simulate(self):                                                     #the random simulation
        if not self.check_game_end_gomoku()[0]:                                #if the game is not end
            allMoves = self.get_empty_points()                              #get all empty point(legal move)
            random.shuffle(allMoves)                                            
            for i in range(len(allMoves)):                                  #play each legal move
                self.play_move_gomoku(allMoves[i],self.current_player)
                Rs,Winner = self.check_game_end_gomoku()                    #after each move, check the board state --> Win,Draw
                if Rs:
                    return Winner, "Random"
                else:
                    if(len(self.get_empty_points))==0:
                        return self.drawWinner, "Random"
                
    def rulesimulate(self):                                                 #the rule_based simulation
        #return BLACK, 0
        RS,Winner = self.check_game_end_gomoku()
        if not RS:                             
            while True:
                movetype,moves = self.GetMoveList()
                random.shuffle(moves)
                if(movetype == "Random"):
                    allMoves = self.get_empty_points()                              #get all empty point(legal move)
                    random.shuffle(allMoves)
                    move = allMoves[0]
                else:
                    move = moves[0]
                self.play_move_gomoku(move,self.current_player)
                RS,Winner = self.check_game_end_gomoku()                    #after each move, check the board state --> Win,Draw
                if RS:
                    return Winner, None
                else:
                    if(len(self.get_empty_points()))==0:
                        return self.drawWinner, None
        else:
            return self.current_player, None    


############################################################
    def immediateWin(self, color, moves):
        
        moveList = []
        for move in moves:
            self.play_move_gomoku(move, color)
            game_end, winner = self.check_game_end_gomoku()
            self.movelist.pop() 
            self.undoMove(move)
            if game_end:
                moveList.append(move) 

        return moveList

    def get_twoD_board(self):
        size = self.size
        board2d = np.zeros((size, size), dtype = np.int32)
        for row in range(size):
            start = self.row_start(row + 1)
            board2d[row, :] = self.board[start : start + size]
        return board2d

    def fourInRow(self, color):
        size = self.size
        board = self.get_twoD_board()
        for i in range(size):
            count = 0
            empty = 0
            for j in range(size):
                currentColor = board[i][j]
                if currentColor == 0:
                    if count == 4 and empty == 1:
                        return True
                    else:
                        count = 0
                        empty = 1
                elif currentColor == color:
                    count+= 1
                else:
                    count = 0
                    empty = 0
        return False

    def fourInCol(self, color):
        size = self.size
        board = self.get_twoD_board()
        for j in range(size):
            count = 0
            empty = 0
            for i in range(size):
                currentColor = board[i][j]
                if currentColor == 0:
                    if count == 4 and empty == 1:
                        #print(i,j)
                        return True
                    else:
                        count = 0
                        empty = 1
                elif currentColor == color:
                    count+= 1
                else:
                    count = 0
                    empty = 0
        return False

    def checkDia(self, board, i, j, color, count, empty,flag):
        currentColor = board[i][j]
        if currentColor == 0:
            if count == 4 and empty == 1:
                return True
            else:
                count = 0
                empty = 1
        elif currentColor == color:
            count += 1
        else:
            count = 0
            empty = 0

        try:
            if (flag == "/"):
                if (j==0):
                    return False
                return self.checkDia(board, i+1, j-1, black, white,"/")
            else:
                return self.checkDia(board, i+1, j+1, black, white,"\\")
        except:                  
            return False    

    def fourIndia(self, color):
        board = self.get_twoD_board()
        for i in range(self.size):
            for j in range(self.size):
                if self.checkDia(board, i, j, color, 0, 0, '/') or self.checkDia(board, i, j, color, 0, 0, '\\'):
                    return True
        return False

    def isOpenFour(self, color, move):
        #print()
        return self.fourInRow(color) or self.fourInCol(color) or self.fourIndia(color)

    
    def openFour(self, color, moves):
        # print(self.board)
        # print(moves)
        moveList = []
        moves = self.get_empty_points()
        #print(moves)
        for move in moves:
            self.play_move_gomoku(move, color)
            if self.isOpenFour(color, move):
                moveList.append(move)
            self.movelist.pop() 
            self.undoMove(move)

        return moveList

    def blockOpenFour(self, color, op_color, moves):
        movelist = []
        #print(moves)
        #print(self.movelist)
        #print("\n")
        if self.openFour(op_color, moves):
            for move in moves:
                self.play_move_gomoku(move, color)
                
                if not self.openFour(op_color, moves):
                    movelist.append(move)
        #        print(self.movelist)
                self.movelist.pop()
        #        print(self.movelist) 
                self.undoMove(move)

        return movelist

    def GetMoveList(self):
        #generate moves based on pattern
        moves = self.get_empty_points()
        color = self.current_player
        op_color = GoBoardUtil.opponent(self.current_player)
        #rule1: Win
        moveList = self.immediateWin(color, moves)
        if moveList:
            return "Win",moveList

        #rule2: BlockWin
        moveList = self.immediateWin(op_color, moves)
        if moveList:
            return "BlockWin",moveList
        
        #rule3: OpenFour
        moveList = self.openFour(color, moves)
        if moveList:
            return "OpenFour",moveList
        #rule4: BlockOpenFour
        moveList = self.blockOpenFour(color, op_color, moves)
        if moveList:
            return "BlockOpenFour",moveList
        #rule5: Random
        return "Random",moves
#############################################################
    def moveNumber(self):                                                   #get the step num, use to undo
        return (len(self.movelist))

    def undoMove(self,location):                                            #set the point back to empty, and switch the player
        self.board[location] = EMPTY
        self.current_player = GoBoardUtil.opponent(self.current_player)

    def resetToMoveNumber(self,num):                                        #the move want to undo is between the current step and the prev one 
        gap = (len(self.movelist) - num)
        if gap >= 0:
            for i in range(gap):
                location = self.movelist.pop()                                 #also remove it from the movelist
                self.undoMove(location)
    
    def staticallyEvaluateForToPlay(self):
        winColor = self.winner()
        if (winColor == EMPTY) and (self.drawWinner != EMPTY):
            winColor = self.drawWinner
        if winColor == self.toPlay:
            return True
        assert winColor == opponent(self.toPlay)
        return False


#=====================================================================================
#=====================================================================================    	
    def get_color(self, point):
        return self.board[point]

    def pt(self, row, col):
        return coord_to_point(row, col, self.size)

    def is_legal(self, point, color):
        """
        Check whether it is legal for color to play on point
        """
        assert is_black_white(color)
        # Special cases
        if point == PASS:
            return True
        elif self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False
            
        # General case: detect captures, suicide
        opp_color = GoBoardUtil.opponent(color)
        self.board[point] = color
        legal = True
        has_capture = self._detect_captures(point, opp_color)
        if not has_capture and not self._stone_has_liberty(point):
            block = self._block_of(point)
            if not self._has_liberty(block): # suicide
                legal = False
        self.board[point] = EMPTY
        return legal

    def _detect_captures(self, point, opp_color):
        """
        Did move on point capture something?
        """
        for nb in self.neighbors_of_color(point, opp_color):
            if self._detect_capture(nb):
                return True
        return False

    def get_empty_points(self):
        """
        Return:
            The empty points on the board
        """
        return where1d(self.board == EMPTY)

    def __init__(self, size):
        """
        Creates a Go board of given size
        """
        assert 2 <= size <= MAXSIZE
        self.reset(size)

    def reset(self, size):
        """
        Creates a start state, an empty board with the given size
        The board is stored as a one-dimensional array
        See GoBoardUtil.coord_to_point for explanations of the array encoding
        """
        self.movelist=[]
        self.drawWinner = EMPTY
        self.size = size
        self.NS = size + 1
        self.WE = 1
        self.ko_recapture = None
        self.current_player = BLACK
        self.maxpoint = size * size + 3 * (size + 1)
        self.board = np.full(self.maxpoint, BORDER, dtype = np.int32)
        self.liberty_of = np.full(self.maxpoint, NULLPOINT, dtype = np.int32)
        self._initialize_empty_points(self.board)
        self._initialize_neighbors()

    def copy(self):
        b = SimpleGoBoard(self.size)
        assert b.NS == self.NS
        assert b.WE == self.WE
        b.ko_recapture = self.ko_recapture
        b.current_player = self.current_player
        assert b.maxpoint == self.maxpoint
        b.board = np.copy(self.board)
        return b

    def row_start(self, row):
        assert row >= 1
        assert row <= self.size
        return row * self.NS + 1
        
    def _initialize_empty_points(self, board):
        """
        Fills points on the board with EMPTY
        Argument
        ---------
        board: numpy array, filled with BORDER
        """
        for row in range(1, self.size + 1):
            start = self.row_start(row)
            board[start : start + self.size] = EMPTY

    def _on_board_neighbors(self, point):
        nbs = []
        for nb in self._neighbors(point):
            if self.board[nb] != BORDER:
                nbs.append(nb)
        return nbs
            
    def _initialize_neighbors(self):
        """
        precompute neighbor array.
        For each point on the board, store its list of on-the-board neighbors
        """
        self.neighbors = []
        for point in range(self.maxpoint):
            if self.board[point] == BORDER:
                self.neighbors.append([])
            else:
                self.neighbors.append(self._on_board_neighbors(point))
        
    def is_eye(self, point, color):
        """
        Check if point is a simple eye for color
        """
        if not self._is_surrounded(point, color):
            return False
        # Eye-like shape. Check diagonals to detect false eye
        opp_color = GoBoardUtil.opponent(color)
        false_count = 0
        at_edge = 0
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = 1
            elif self.board[d] == opp_color:
                false_count += 1
        return false_count <= 1 - at_edge # 0 at edge, 1 in center
    
    def _is_surrounded(self, point, color):
        """
        check whether empty point is surrounded by stones of color.
        """
        for nb in self.neighbors[point]:
            nb_color = self.board[nb]
            if nb_color != color:
                return False
        return True

    def _stone_has_liberty(self, stone):
        lib = self.find_neighbor_of_color(stone, EMPTY)
        return lib != None

    def _get_liberty(self, block):
        """
        Find any liberty of the given block.
        Returns None in case there is no liberty.
        block is a numpy boolean array
        """
        for stone in where1d(block):
            lib = self.find_neighbor_of_color(stone, EMPTY)
            if lib != None:
                return lib
        return None

    def _has_liberty(self, block):
        """
        Check if the given block has any liberty.
        Also updates the liberty_of array.
        block is a numpy boolean array
        """
        lib = self._get_liberty(block)
        if lib != None:
            assert self.get_color(lib) == EMPTY
            for stone in where1d(block):
                self.liberty_of[stone] = lib
            return True
        return False

    def _block_of(self, stone):
        """
        Find the block of given stone
        Returns a board of boolean markers which are set for
        all the points in the block 
        """
        marker = np.full(self.maxpoint, False, dtype = bool)
        pointstack = [stone]
        color = self.get_color(stone)
        assert is_black_white(color)
        marker[stone] = True
        while pointstack:
            p = pointstack.pop()
            neighbors = self.neighbors_of_color(p, color)
            for nb in neighbors:
                if not marker[nb]:
                    marker[nb] = True
                    pointstack.append(nb)
        return marker

    def _fast_liberty_check(self, nb_point):
        lib = self.liberty_of[nb_point]
        if lib != NULLPOINT and self.get_color(lib) == EMPTY:
            return True # quick exit, block has a liberty  
        if self._stone_has_liberty(nb_point):
            return True # quick exit, no need to look at whole block
        return False
        
    def _detect_capture(self, nb_point):
        """
        Check whether opponent block on nb_point is captured.
        Returns boolean.
        """
        if self._fast_liberty_check(nb_point):
            return False
        opp_block = self._block_of(nb_point)
        return not self._has_liberty(opp_block)
    
    def _detect_and_process_capture(self, nb_point):
        """
        Check whether opponent block on nb_point is captured.
        If yes, remove the stones.
        Returns the stone if only a single stone was captured,
            and returns None otherwise.
        This result is used in play_move to check for possible ko
        """
        if self._fast_liberty_check(nb_point):
            return None
        opp_block = self._block_of(nb_point)
        if self._has_liberty(opp_block):
            return None
        captures = list(where1d(opp_block))
        self.board[captures] = EMPTY
        self.liberty_of[captures] = NULLPOINT
        single_capture = None 
        if len(captures) == 1:
            single_capture = nb_point
        return single_capture

    def play_move(self, point, color):
        """
        Play a move of color on point
        Returns boolean: whether move was legal
        """
        assert is_black_white(color)
        # Special cases
        if point == PASS:
            self.ko_recapture = None
            self.current_player = GoBoardUtil.opponent(color)
            return True
        elif self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False
            
        # General case: deal with captures, suicide, and next ko point
        opp_color = GoBoardUtil.opponent(color)
        in_enemy_eye = self._is_surrounded(point, opp_color)
        self.board[point] = color
        single_captures = []
        neighbors = self.neighbors[point]
        for nb in neighbors:
            if self.board[nb] == opp_color:
                single_capture = self._detect_and_process_capture(nb)
                if single_capture != None:
                    single_captures.append(single_capture)
        if not self._stone_has_liberty(point):
            # check suicide of whole block
            block = self._block_of(point)
            if not self._has_liberty(block): # undo suicide move
                self.board[point] = EMPTY
                return False
        self.ko_recapture = None
        if in_enemy_eye and len(single_captures) == 1:
            self.ko_recapture = single_captures[0]
        self.current_player = GoBoardUtil.opponent(color)
        return True

    def neighbors_of_color(self, point, color):
        """ List of neighbors of point of given color """
        nbc = []
        for nb in self.neighbors[point]:
            if self.get_color(nb) == color:
                nbc.append(nb)
        return nbc
        
    def find_neighbor_of_color(self, point, color):
        """ Return one neighbor of point of given color, or None """
        for nb in self.neighbors[point]:
            if self.get_color(nb) == color:
                return nb
        return None
        
    def _neighbors(self, point):
        """ List of all four neighbors of the point """
        return [point - 1, point + 1, point - self.NS, point + self.NS]

    def _diag_neighbors(self, point):
        """ List of all four diagonal neighbors of point """
        return [point - self.NS - 1, 
                point - self.NS + 1, 
                point + self.NS - 1, 
                point + self.NS + 1]
    
    def _point_to_coord(self, point):
        """
        Transform point index to row, col.
        
        Arguments
        ---------
        point
        
        Returns
        -------
        x , y : int
        coordination of the board  1<= x <=size, 1<= y <=size .
        """
        if point is None:
            return 'pass'
        row, col = divmod(point, self.NS)
        return row, col

    def is_legal_gomoku(self, point, color):
        """
            Check whether it is legal for color to play on point, for the game of gomoku
            """
        return self.board[point] == EMPTY
    
    def play_move_gomoku(self, point, color):
        """
            Play a move of color on point, for the game of gomoku
            Returns boolean: whether move was legal
            """
        assert is_black_white(color)
        assert point != PASS
        if self.board[point] != EMPTY:
            return False
        self.board[point] = color
        self.current_player = GoBoardUtil.opponent(color)
        self.movelist.append(point)

        #print(self.movelist)
        return True
        
    def _point_direction_check_connect_gomoko(self, point, shift):
        """
        Check if the point has connect5 condition in a direction
        for the game of Gomoko.
        """
        color = self.board[point]
        count = 1
        d = shift
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == 5:
                    break
            else:
                break
        d = -d
        p = point
        while True:
            p = p + d
            if self.board[p] == color:
                count = count + 1
                if count == 5:
                    break
            else:
                break
        assert count <= 5
        return count == 5
    
    def point_check_game_end_gomoku(self, point):
        """
            Check if the point causes the game end for the game of Gomoko.
            """
        # check horizontal
        if self._point_direction_check_connect_gomoko(point, 1):
            return True
        
        # check vertical
        if self._point_direction_check_connect_gomoko(point, self.NS):
            return True
        
        # check y=x
        if self._point_direction_check_connect_gomoko(point, self.NS + 1):
            return True
        
        # check y=-x
        if self._point_direction_check_connect_gomoko(point, self.NS - 1):
            return True
        
        return False
    
    def check_game_end_gomoku(self):
        """
            Check if the game ends for the game of Gomoku.
            """
        white_points = where1d(self.board == WHITE)
        black_points = where1d(self.board == BLACK)
        
        for point in white_points:
            if self.point_check_game_end_gomoku(point):
                return True, WHITE
    
        for point in black_points:
            if self.point_check_game_end_gomoku(point):
                return True, BLACK

        return False, None
