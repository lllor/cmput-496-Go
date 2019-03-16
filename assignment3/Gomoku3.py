from board_util import BLACK, WHITE, EMPTY
from simple_board import SimpleGoBoard

#using Flat Monte Carlo
class SimulationPlayer(object):
    def __init__(self, numSimulations):
        self.numSimulations = numSimulations

    def name(self):
        return "Simulation Player ({0} sim.)".format(self.numSimulations)

    def genmove(self, state):
        
        moves = state.get_empty_points()
        numMoves = len(moves)
        if numMoves == 0:
            return PASS
        score = [0] * numMoves
        for i in range(numMoves):
            move = moves[i]
            score[i] = self.simulate(state, move)
        #print(score)
        bestIndex = score.index(max(score))
        best = moves[bestIndex]
        #print("Best move:", best, "score", score[best])
        assert best in state.get_empty_points()
        return best

    def simulate(self, state, move):
        WinnerStats = [0] * 3

        state.play_move_gomoku(move,state.toPlay)
        moveNr = state.moveNumber()

        
        for _ in range(self.numSimulations):
            if self.policy == 1:
                winner, _ = state.simulate()
            else:
                winner, _ = state.rulesimulate()
            state[winner] += 1
            state.resetToMoveNumber(moveNr)

        assert sum(stats) == self.numSimulations
        assert moveNr == state.moveNumber()
        
        state.undoMove()
        eval = (WinnerStats[BLACK] + 0.5 * WinnerStats[EMPTY]) / self.numSimulations
        if state.toPlay == WHITE:
            eval = 1 - eval
        return eval

def run():
    """
    start the gtp connection and wait for commands.
    """
    board = SimpleGoBoard(7)
    con = GtpConnection(Gomoku3(10), board)
    con.start_connection()

if __name__=='__main__':
    run()
# def randomTTT(numSimulations):
#     print("Playing {} random TicTacToe games ...".format(numSimulations))
#     t = TicTacToe()
#     winnerStats = [0] * 3
#     gameLength = [0] * 10
#     for _ in range(numSimulations):
#         t.resetGame()
#         winner, length = t.simulate()
#         winnerStats[winner] += 1
#         gameLength[length] += 1
#     print("{} wins for X, {} wins for O, {} draws".format(
#         winnerStats[BLACK],  winnerStats[WHITE], winnerStats[EMPTY]))
#     print("Game length:")
#     for length in range(10):
#         if gameLength[length] > 0:
#             print("Length {} : {}".format(length, gameLength[length]))

# if __name__ == "__main__":
#     randomTTT(10000)