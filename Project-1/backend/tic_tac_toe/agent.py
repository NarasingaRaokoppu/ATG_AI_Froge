class TicTacToeAgent:
    """
    AI agent for Tic Tac Toe using Minimax algorithm.
    The agent plays as 'O' and the human plays as 'X'.
    """

    def __init__(self):
        self.agent_player = 'O'
        self.human_player = 'X'

    def make_move(self, board):
        """
        Calculate the best move for the agent using minimax algorithm.
        
        Args:
            board: List of 9 elements representing the game board
            
        Returns:
            Updated board with the agent's move
        """
        move = self._best_move(board)
        if move != -1:
            board[move] = self.agent_player
        return board

    def _best_move(self, board):
        """Find the best move using minimax algorithm."""
        best_score = float('-inf')
        best_move = -1

        for i in range(len(board)):
            if board[i] is None:
                board[i] = self.agent_player
                score = self._minimax(board, 0, False)
                board[i] = None

                if score > best_score:
                    best_score = score
                    best_move = i

        return best_move

    def _minimax(self, board, depth, is_maximizing):
        """
        Minimax algorithm implementation.
        
        Args:
            board: Current board state
            depth: Current depth in the game tree
            is_maximizing: True if maximizing player (agent), False if minimizing (human)
            
        Returns:
            Score for the board position
        """
        winner = self._check_winner(board)

        # Terminal states
        if winner == self.agent_player:
            return 10 - depth  # Agent wins (prefer quicker wins)
        elif winner == self.human_player:
            return depth - 10  # Human wins (prefer longer games)
        elif self._is_board_full(board):
            return 0  # Draw

        if is_maximizing:
            # Agent's turn - maximize score
            max_score = float('-inf')
            for i in range(len(board)):
                if board[i] is None:
                    board[i] = self.agent_player
                    score = self._minimax(board, depth + 1, False)
                    board[i] = None
                    max_score = max(score, max_score)
            return max_score
        else:
            # Human's turn - minimize score
            min_score = float('inf')
            for i in range(len(board)):
                if board[i] is None:
                    board[i] = self.human_player
                    score = self._minimax(board, depth + 1, True)
                    board[i] = None
                    min_score = min(score, min_score)
            return min_score

    def _check_winner(self, board):
        """
        Check if there's a winner.
        
        Returns:
            'X' if X wins, 'O' if O wins, None if no winner
        """
        lines = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # Rows
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # Columns
            [0, 4, 8], [2, 4, 6]  # Diagonals
        ]

        for line in lines:
            a, b, c = line
            if board[a] and board[a] == board[b] == board[c]:
                return board[a]

        return None

    def _is_board_full(self, board):
        """Check if the board is full."""
        return all(cell is not None for cell in board)