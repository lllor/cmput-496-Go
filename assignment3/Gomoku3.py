from board_util import BLACK, WHITE, EMPTY
from simple_board import SimpleGoBoard

#using Flat Monte Carlo
class SimulationPlayer(object):
    def __init__(self, numSimulations):
        self.numSimulations = numSimulations

    def name(self):
        return "Simulation Player ({0} sim.)".format(self.numSimulations)

    def genmove(self, state):
        assert not state.endOfGame()
        moves = state.legalMoves()
        numMoves = len(moves)
        score = [0] * numMoves
        for i in range(numMoves):
            move = moves[i]
            score[i] = self.simulate(state, move)
        #print(score)
        bestIndex = score.index(max(score))
        best = moves[bestIndex]
        #print("Best move:", best, "score", score[best])
        assert best in state.legalMoves()
        return best

    def simulate(self, board, move):
        WinnerStats = [0] * 3
        gameLength = [0] * 10
        #board.play_move_gomoku()
        board.play(move)
        #moveNr = state.moveNumber()
        cboard = board.copy();
        for _ in range(self.numSimulations):
            board = cboard.copy()
            winner, length = board.simulate()
            stats[winner] += 1
            gameLength[length] += 1
        assert sum(stats) == self.numSimulations
        #assert moveNr == state.moveNumber()
        board.undoMove()
        eval = (WinnerStats[BLACK] + 0.5 * WinnerStats[EMPTY]) / self.numSimulations
        if board.toPlay == WHITE:
            eval = 1 - eval
        return eval

s = SimulationPlayer(10)

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