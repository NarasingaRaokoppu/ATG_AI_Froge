from app.services.rag.rag_service import RagService


def test_sanitize_filename_keeps_safe_chars() -> None:
    assert RagService._sanitize_filename("Q2 Report (final).pdf") == "Q2_Report_final_.pdf"
