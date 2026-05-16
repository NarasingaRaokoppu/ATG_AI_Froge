"""Tic Tac Toe game routes."""

from fastapi import APIRouter
from pydantic import BaseModel

from tic_tac_toe.agent import TicTacToeAgent

router = APIRouter(prefix="/tic-tac-toe", tags=["tic-tac-toe"])


class BoardRequest(BaseModel):
    """Request body for tic-tac-toe move."""
    board: list[str | None]


class BoardResponse(BaseModel):
    """Response body for tic-tac-toe move."""
    board: list[str | None]
    move: int | None


@router.post("/move")
async def make_ai_move(
    payload: BoardRequest,
) -> BoardResponse:
    """
    Calculate and make the AI's move in tic-tac-toe.
    
    Args:
        payload: Current board state (list of 9 elements, None for empty)
    Returns:
        Updated board with AI's move and the move index
    """
    agent = TicTacToeAgent()
    
    # Convert board to mutable list for the agent
    board = list(payload.board)
    
    # Find the position before the move
    old_positions = set(i for i, cell in enumerate(board) if cell is not None)
    
    # Make the agent's move
    updated_board = agent.make_move(board)
    
    # Find which position was filled
    new_positions = set(i for i, cell in enumerate(updated_board) if cell is not None)
    move = list(new_positions - old_positions)[0] if new_positions - old_positions else None
    
    return BoardResponse(board=updated_board, move=move)
