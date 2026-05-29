from __future__ import annotations

import json
import re
from typing import Any

from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from app.ai.llm import llm


@tool
def list_available_moves(board_json: str) -> str:
    """Return all legal move indexes for the current tic-tac-toe board JSON list."""
    board = json.loads(board_json)
    moves = [idx for idx, cell in enumerate(board) if cell is None]
    return json.dumps(moves)


@tool
def evaluate_position(board_json: str) -> str:
    """Evaluate the board and return winner/draw/in_progress status."""
    board = json.loads(board_json)
    winner = _check_winner(board)
    if winner:
        return json.dumps({"status": "won", "winner": winner})
    if all(cell is not None for cell in board):
        return json.dumps({"status": "draw"})
    return json.dumps({"status": "in_progress"})


def _check_winner(board: list[str | None]) -> str | None:
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6],
    ]
    for a, b, c in lines:
        if board[a] and board[a] == board[b] == board[c]:
            return board[a]
    return None


class TicTacToeAgent:
    """LangChain-backed tic-tac-toe agent with deterministic fallback."""

    def __init__(self):
        self.agent_player = "O"
        self.human_player = "X"
        self._agent = create_react_agent(
            model=llm,
            tools=[list_available_moves, evaluate_position],
        )

    async def make_move(self, board: list[str | None]) -> list[str | None]:
        """Choose a move using LangChain agent and fallback to minimax when needed."""
        move = await self._choose_move_with_langchain(board)
        if move is None or move < 0 or move >= len(board) or board[move] is not None:
            move = self._best_move(board)

        if move != -1:
            board[move] = self.agent_player
        return board

    async def _choose_move_with_langchain(self, board: list[str | None]) -> int | None:
        try:
            board_json = json.dumps(board)
            response = await self._agent.ainvoke(
                {
                    "messages": [
                        (
                            "system",
                            "You are a tic-tac-toe strategist playing as O. "
                            "Call tools if needed and return only the move index 0-8.",
                        ),
                        (
                            "human",
                            f"Board JSON: {board_json}. Return best legal move index for O.",
                        ),
                    ]
                }
            )
            messages = response.get("messages", []) if isinstance(response, dict) else []
            if not messages:
                return None

            content: Any = getattr(messages[-1], "content", "")
            text = content if isinstance(content, str) else str(content)
            match = re.search(r"\b([0-8])\b", text)
            if not match:
                return None
            return int(match.group(1))
        except Exception:
            return None

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
        winner = _check_winner(board)

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

    def _is_board_full(self, board):
        """Check if the board is full."""
        return all(cell is not None for cell in board)