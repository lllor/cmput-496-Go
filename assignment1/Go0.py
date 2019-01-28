#!/usr/bin/python3
#/usr/local/bin/python3
# Set the path to your python3 above
# Set up relative path for util
# sys.path[0] is the directory of the current program

#
'''
Note: when demo for assignment1
in case of invalid python3 path in different machine
please call this with python3 when using gogui-regress
example: (on lab machine)
/cshome/jialin/gogui/bin/gogui-regress 'python3 Go0.py' assignment1-public-tests.gtp

This project is witen by:
Jialin Xie    | 1465931    | jialin
Lanfang Zhang | 1519206    | lanfang1
'''
import sys
utilpath = sys.path[0] + "/../util/"
sys.path.append(utilpath)

from gtp_connection import GtpConnection
from board_util import GoBoardUtil
from simple_board import SimpleGoBoard

class Go0():
    def __init__(self):
        """
        Go player that selects moves randomly from the set of legal moves.
        Does not use the fill-eye filter.
        Passes only if there is no other legal move.

        Parameters
        ----------
        name : str
            name of the player (used by the GTP interface).
        version : float
            version number (used by the GTP interface).
        """
        self.name = "Go0"
        self.version = 1.0
        
    def get_move(self, board, color):
        return GoBoardUtil.generate_random_move(board, color, False)
    
def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(Go0(), board)
    con.start_connection()

if __name__=='__main__':
    run()
