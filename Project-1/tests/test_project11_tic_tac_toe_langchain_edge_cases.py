import pytest

from tic_tac_toe.agent import TicTacToeAgent


@pytest.mark.asyncio
async def test_project11_fallback_uses_minimax_when_langchain_returns_invalid_move(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = TicTacToeAgent()

    async def fake_choose_move(_: list[str | None]) -> int | None:
        return 99

    monkeypatch.setattr(agent, "_choose_move_with_langchain", fake_choose_move)

    board = ["X", "X", None, "O", None, None, None, None, "O"]
    updated = await agent.make_move(board)

    # Minimax should block X from winning at index 2.
    assert updated[2] == "O"


@pytest.mark.asyncio
async def test_project11_does_not_overwrite_filled_cells(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    agent = TicTacToeAgent()

    async def fake_choose_move(_: list[str | None]) -> int | None:
        return 0

    monkeypatch.setattr(agent, "_choose_move_with_langchain", fake_choose_move)

    board = ["X", None, None, None, None, None, None, None, None]
    updated = await agent.make_move(board)

    assert updated[0] == "X"
    assert updated.count("O") == 1
