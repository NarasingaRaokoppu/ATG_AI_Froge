import { useState } from 'react';
import './TicTacToePage.css';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

interface BoardState {
  board: (string | null)[];
  isXNext: boolean;
  winner: string | null;
  isBoardFull: boolean;
  isThinking: boolean;
}

const TicTacToePage = () => {
  const [gameState, setGameState] = useState<BoardState>({
    board: Array(9).fill(null),
    isXNext: true,
    winner: null,
    isBoardFull: false,
    isThinking: false,
  });

  const calculateWinner = (squares: (string | null)[]): string | null => {
    const lines = [
      [0, 1, 2], [3, 4, 5], [6, 7, 8],
      [0, 3, 6], [1, 4, 7], [2, 5, 8],
      [0, 4, 8], [2, 4, 6]
    ];
    for (const line of lines) {
      const [a, b, c] = line;
      if (squares[a] && squares[a] === squares[b] && squares[a] === squares[c]) {
        return squares[a];
      }
    }
    return null;
  };

  const isBoardFull = (squares: (string | null)[]): boolean => {
    return squares.every(cell => cell !== null);
  };

  const fallbackAIMove = (board: (string | null)[]): (string | null)[] => {
    const nextBoard = [...board];
    const emptyIndex = nextBoard.findIndex((cell) => cell === null);
    if (emptyIndex !== -1) {
      nextBoard[emptyIndex] = 'O';
    }
    return nextBoard;
  };

  const fetchAIMove = async (currentBoard: (string | null)[]): Promise<(string | null)[]> => {
    try {
      const response = await fetch(`${API_BASE_URL}/tic-tac-toe/move`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ board: currentBoard }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      return Array.isArray(data?.board) ? data.board : fallbackAIMove(currentBoard);
    } catch (error) {
      console.error('Error fetching AI move:', error);
      return fallbackAIMove(currentBoard);
    }
  };

  const handleClick = async (index: number) => {
    if (gameState.board[index] || gameState.winner || gameState.isThinking || !gameState.isXNext) {
      return;
    }

    // Player makes their move (X)
    const newBoard = gameState.board.slice();
    newBoard[index] = 'X';

    const winner = calculateWinner(newBoard);
    const full = isBoardFull(newBoard);

    if (winner || full) {
      setGameState({
        ...gameState,
        board: newBoard,
        isXNext: false,
        winner: winner,
        isBoardFull: full,
      });
      return;
    }

    // AI's turn (O)
    setGameState(prev => ({ ...prev, board: newBoard, isThinking: true }));

    const aiBoard = await fetchAIMove(newBoard);
    
    const aiWinner = calculateWinner(aiBoard);
    const aiFull = isBoardFull(aiBoard);

    setGameState({
      board: aiBoard,
      isXNext: true,
      winner: aiWinner,
      isBoardFull: aiFull,
      isThinking: false,
    });
  };

  const resetGame = () => {
    setGameState({
      board: Array(9).fill(null),
      isXNext: true,
      winner: null,
      isBoardFull: false,
      isThinking: false,
    });
  };

  const getStatusMessage = (): string => {
    if (gameState.winner) {
      if (gameState.winner === 'X') {
        return '🎉 You won!';
      } else {
        return '🤖 AI won!';
      }
    }
    if (gameState.isBoardFull) {
      return "It's a draw!";
    }
    if (gameState.isThinking) {
      return '🤔 AI is thinking...';
    }
    return gameState.isXNext ? 'Your turn (X)' : 'AI is playing (O)';
  };

  return (
    <div className="tic-tac-toe">
      <h1 className="title">Tic Tac Toe</h1>
      <div className="subtitle">Play against the AI Agent</div>
      <div className={`status ${gameState.winner ? 'status-winner' : gameState.isBoardFull ? 'status-draw' : ''}`}>
        {getStatusMessage()}
      </div>
      <div className="board">
        {gameState.board.map((cell, index) => (
          <button
            key={index}
            className={`cell ${cell === 'X' ? 'cell-x' : cell === 'O' ? 'cell-o' : ''}`}
            onClick={() => handleClick(index)}
            disabled={gameState.isThinking || !gameState.isXNext || gameState.winner !== null}
          >
            {cell}
          </button>
        ))}
      </div>
      <button 
        className="reset-button" 
        onClick={resetGame}
        disabled={gameState.isThinking}
      >
        {gameState.winner || gameState.isBoardFull ? 'Play Again' : 'Reset Game'}
      </button>
    </div>
  );
};

export default TicTacToePage;