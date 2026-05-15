class TicTacToeAgent:
    def __init__(self):
        pass

    def best_move(self, board):
        for i in range(len(board)):
            if board[i] is None:
                return i
        return -1

    def make_move(self, board):
        move = self.best_move(board)
        if move != -1:
            board[move] = 'O'
        return board