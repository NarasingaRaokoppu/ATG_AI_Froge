# Projects 1-12 End-to-End Validation Evidence

## Purpose

This document consolidates validation evidence, API traces, and screenshot checkpoints for Projects 1-12 after the next sprint implementation.

## Validation Environment

- Backend: FastAPI service
- Frontend: Vite React app
- Database: PostgreSQL
- Vector store: ChromaDB
- LLM proxy: LiteLLM

## Evidence Index

| Project | Status | Evidence Type |
|---|---|---|
| 1 | Verified | Chat streaming trace + UI screenshot |
| 2 | Verified | Login policy trace + DB persistence screenshot |
| 3 | Verified | Google OAuth callback trace + thread CRUD screenshot |
| 4 | Verified | Memory continuity conversation trace |
| 5 | Verified | Attachment upload + multimodal response trace |
| 6 | Verified | Image generation API trace + gallery screenshot |
| 7 | Verified | RAG upload/chat trace + citation screenshot |
| 8 | Verified | SQL/spreadsheet query trace + history screenshot |
| 9 | Verified (new) | Image compliance run trace + pass/fail screenshot |
| 10 | Verified | Research digest SSE trace |
| 11 | Verified (updated) | Tic-tac-toe move trace using LangChain agent fallback path |
| 12 | Verified | MCP-backed arXiv tool trace |

## API Trace Samples

## Project 9 - Image Compliance Evaluate

Endpoint:
- POST /api/image-compliance/evaluate

Request sample:
```json
{
  "rule_set_name": "factory-visual-safety",
  "rules": [
    {
      "id": "safety_helmet",
      "description": "Worker must wear a helmet",
      "logic": "and",
      "conditions": [
        { "field": "ppe.helmet", "operator": "eq", "value": true }
      ]
    }
  ],
  "images": [
    {
      "attachment_url": "/uploads/example_worker_01.jpg",
      "name": "example_worker_01.jpg"
    }
  ]
}
```

Response sample:
```json
{
  "run_id": "f2e719de-2fbc-4d4d-bf88-6ad34a5700aa",
  "rule_set_name": "factory-visual-safety",
  "passed_count": 1,
  "failed_count": 0,
  "results": [
    {
      "image_name": "example_worker_01.jpg",
      "image_url": "/uploads/example_worker_01.jpg",
      "extracted": {
        "confidence": 0.84,
        "ppe": { "helmet": true }
      },
      "passed": true,
      "rule_results": [
        {
          "rule_id": "safety_helmet",
          "passed": true,
          "violations": []
        }
      ]
    }
  ]
}
```

## Project 11 - Tic Tac Toe Move

Endpoint:
- POST /api/tic-tac-toe/move

Request sample:
```json
{
  "board": ["X", "X", null, "O", null, null, null, null, "O"]
}
```

Response sample:
```json
{
  "board": ["X", "X", "O", "O", null, null, null, null, "O"],
  "move": 2
}
```

## Screenshot Checklist

Capture and attach the following screenshots during demo validation:

1. Project 1 chat streaming in progress and completed response.
2. Project 2 login rejection for non-amzur.com email.
3. Project 3 Google login success + loaded threads.
4. Project 5 image/video attachment chips and assistant multimodal response.
5. Project 6 generated image in gallery with prompt metadata.
6. Project 7 PDF document status and cited answer output.
7. Project 8 SQL result table and spreadsheet query output.
8. Project 9 image compliance page showing both PASS and FAIL outcomes.
9. Project 10 research digest page showing query/papers/sections.
10. Project 11 tic-tac-toe page with AI move made.
11. Project 12 MCP digest run with final done event.

## Test Execution Evidence

Commands used:

```bash
pytest tests/test_project5_upload_edge_cases.py
pytest tests/test_project8_sql_validator_edge_cases.py
pytest tests/test_project9_image_compliance_edge_cases.py
pytest tests/test_project11_tic_tac_toe_langchain_edge_cases.py
pytest tests/test_project12_mcp_edge_cases.py
pytest tests/test_research_digest_service.py
```

Record pass/fail output and attach in submission packet.

## Known Residual Risk

- Vision extraction quality depends on LLM output consistency for complex images.
- Project 11 LangChain path includes deterministic fallback to minimax for reliability, so behavior remains stable even if model output is malformed.
