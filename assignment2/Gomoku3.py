from game_basics import BLACK, WHITE, EMPTY
from tic_tac_toe import TicTacToe
def randomTTT(numSimulations):
    print("Playing {} random TicTacToe games ...".format(numSimulations))
    t = TicTacToe()
    winnerStats = [0] * 3
    gameLength = [0] * 10
    for _ in range(numSimulations):
        t.resetGame()
        winner, length = t.simulate()
        winnerStats[winner] += 1
        gameLength[length] += 1
    print("{} wins for X, {} wins for O, {} draws".format(
        winnerStats[BLACK],  winnerStats[WHITE], winnerStats[EMPTY]))
    print("Game length:")
    for length in range(10):
        if gameLength[length] > 0:
            print("Length {} : {}".format(length, gameLength[length]))

if __name__ == "__main__":
    randomTTT(10000)
