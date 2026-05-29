# Projects 1-12 Stepwise Implementation Plan and Status

## Current Track Summary

- Overall: On the right track for most milestones.
- Completed or mostly complete: Projects 1, 2, 3, 4, 5, 6, 7, 8, 10, 12.
- Needs alignment/follow-up: Project 9 and Project 11.

## Milestone Status Matrix

| Project | Requirement Snapshot | Status | Notes |
|---|---|---|---|
| 1 | Basic chatbot with UI + Python backend + LLM | Complete | Chat UI + FastAPI + LangChain chain wired through LiteLLM/Gemini model config |
| 2 | PostgreSQL persistence + Amzur login + load chats after login | Complete | Thread/message persistence, Amzur domain validation, threads/messages loaded on login |
| 3 | Google login + thread CRUD + auto titles + load threads on login | Complete | Google OAuth implemented, thread create/update/delete, LLM auto title generation |
| 4 | Memory of 5 previous conversations | Complete | Last 10 messages (5 turns) for chat context; RAG history turns set to 5 |
| 5 | Image/video/table/formula/code attachments; Gemini 2.5 flash for video | Mostly complete | Multimodal attachments supported; video key-frame extraction implemented; model defaults to Gemini 2.5 Flash |
| 6 | Image generation with Gemini image model | Complete | Versioned image generation APIs + frontend gallery + persistence |
| 7 | PDF upload chat via RAG + ChromaDB + text-embedding-3-large | Complete | PDF ingestion/retrieval pipeline with Chroma and embedding model configured |
| 8 | NL to SQL + Excel/GSheet querying | Complete | SQL explorer + spreadsheet explorer with history and connections |
| 9 | Rule-based image extraction/compliance check | Not complete per requested scope | Current UI labels spreadsheet feature as Project 9, but image-rule compliance flow is missing |
| 10 | Basic LangChain agent | Complete | Research digest agent workflow implemented with streaming |
| 11 | Tic-tac-toe agent using LangChain | Partial | Tic-tac-toe exists, but current logic is Minimax class, not LangChain agent orchestration |
| 12 | Agent with MCP example | Complete | Research digest migrated to MCP-backed tool calls |

## Stepwise Implementation by Project

## Project 1 - Chatbot Foundation

### Objective
Create a simple chatbot that talks to an LLM and responds in a web UI.

### Implementation Steps
1. Keep frontend chat route and chat container as the primary interaction surface.
2. Keep backend SSE chat endpoint for streaming responses.
3. Keep LangChain chat chain with Gemini model via LiteLLM proxy.
4. Validate request/response contracts between frontend stream parser and backend events.

### Verification
- Start backend and frontend.
- Login and send a text message.
- Confirm streaming token response and final assistant message persistence.

## Project 2 - Database and Employee Auth

### Objective
Use PostgreSQL for chat persistence and allow only Amzur employee login.

### Implementation Steps
1. Keep PostgreSQL schema for users, threads, messages.
2. Keep register/login validation that enforces amzur.com email domain.
3. On login, load thread list and thread messages in UI.
4. Keep message persistence on each user and assistant turn.

### Verification
- Register/login with amzur.com account succeeds.
- Non-Amzur email blocked.
- Existing threads and chats load after login.

## Project 3 - Google OAuth and Thread Lifecycle

### Objective
Add Google sign-in and full thread lifecycle.

### Implementation Steps
1. Keep Google OAuth login and callback routes.
2. Keep domain restriction for Google account email.
3. Keep thread CRUD APIs and frontend operations.
4. Keep auto-title generation for new threads using first user message.

### Verification
- Google login works and sets session cookie.
- Create/rename/delete thread works.
- Thread title auto-generated when chat starts.

## Project 4 - Conversational Memory (5 turns)

### Objective
Remember previous 5 conversations before answering.

### Implementation Steps
1. Keep thread-level context fetch limit at 10 messages.
2. Keep history formatting fed into chat prompt context.
3. Preserve this behavior for both text and multimodal path.

### Verification
- In a single thread, ask a follow-up dependent on prior turns.
- Confirm assistant retains context from earlier 5 turns.

## Project 5 - Multimodal Attachments

### Objective
Allow image/video/table/formula/code attachments and multimodal reasoning.

### Implementation Steps
1. Keep upload endpoint handling image/video/excel/docx/txt.
2. Keep video key-frame extraction and frame injection into multimodal prompt.
3. Keep attachment draft flow in input menu for table/formula/code metadata.
4. Keep chat service multimodal message builder for image and video frame blocks.

### Verification
- Upload image/video and ask analysis question.
- Add table/formula/code draft attachment and confirm assistant references it.

### Gap to close
- If strict requirement is explicit Gemini 2.5 Flash endpoint for video-only pipeline, add a dedicated video analysis service toggle instead of shared chat path.

## Project 6 - AI Image Generation

### Objective
Generate images using Gemini image generation model.

### Implementation Steps
1. Keep versioned image APIs under /api/v1/images.
2. Keep Gemini image client wrapper and retries.
3. Keep generated image persistence and gallery/list/delete/regenerate flow.

### Verification
- Generate image from prompt.
- Regenerate variant.
- Delete image and verify history updates.

## Project 7 - PDF Chat with RAG

### Objective
Upload PDFs and chat with grounded responses via RAG.

### Implementation Steps
1. Keep PDF upload/indexing/chat/list/delete APIs.
2. Keep Chroma persistent vector storage.
3. Keep text-embedding-3-large for embeddings.
4. Keep citation-based response rendering in frontend.

### Verification
- Upload PDF.
- Wait for processed status.
- Ask document-grounded question and confirm citations.

## Project 8 - NL-to-SQL and Spreadsheet Q&A

### Objective
Query databases and spreadsheets in natural language.

### Implementation Steps
1. Keep DB connection management and test flow.
2. Keep SQL query streaming endpoint with generated SQL and explanation.
3. Keep spreadsheet upload and Google Sheet connection.
4. Keep spreadsheet query and history endpoints.

### Verification
- Add DB connection and run NL query.
- Upload sheet or connect GSheet and run NL question.
- Confirm results and history entries.

## Project 9 - Rule-Based Image Compliance Check

### Objective
Extract structured data from images and validate against rules.

### Current Status
Not implemented for this scope.

### Required Steps to implement
1. Define rule schema (for example field constraints, thresholds, required labels).
2. Add backend endpoint for image+rules submission.
3. Add extraction pipeline (vision extraction with structured JSON output).
4. Add rule engine evaluation and compliance result model.
5. Add frontend page to upload batch images and display pass/fail plus violations.
6. Persist audit results in DB table for traceability.

### Verification
- Submit sample rules and image set.
- Confirm extraction output and rule-by-rule pass/fail.

## Project 10 - Basic Agent with LangChain

### Objective
Create a basic LLM-powered agent.

### Implementation Steps
1. Keep research digest agent flow with iterative search and decisions.
2. Keep SSE event protocol for status, query, papers, decisions, sections.
3. Keep frontend real-time digest rendering.

### Verification
- Start digest run for a topic.
- Confirm multi-stage events and final structured response.

## Project 11 - Tic-Tac-Toe Agent with LangChain

### Objective
Build a Tic-tac-toe agent using LangChain.

### Current Status
Game endpoint exists, but decision engine is Minimax class.

### Steps to align with requirement
1. Wrap game state evaluator as LangChain tool(s).
2. Create LangChain agent that chooses move by invoking board-evaluation tool.
3. Keep deterministic fallback for invalid outputs.
4. Add tests for legal move generation and win/block behavior.

### Verification
- For known board states, confirm agent move validity and expected strategy.

## Project 12 - MCP Agent Example

### Objective
Integrate MCP tools into an agent workflow.

### Implementation Steps
1. Keep MCP server config and startup strategy.
2. Keep LangGraph React agent using MCP tools for arXiv search.
3. Keep fallback direct tool invocation when parse shape is irregular.

### Verification
- Run research digest.
- Confirm MCP search tool is invoked and results stream correctly.

## Recommended Next Sprint (Priority)

1. Implement Project 9 image-rule compliance pipeline (highest gap).
2. Refactor Project 11 tic-tac-toe logic into LangChain-agent form.
3. Add one consolidated end-to-end validation document with evidence screenshots and API traces.
4. Add automated tests for Projects 5, 8, 9, 11, and 12 edge cases.

## Existing Documentation Files Already Present

- README overview: README.md
- Project 6: PROJECT6_IMAGE_GENERATION.md
- Project 7: PROJECT7_PDF_CHAT_RAG.md
- Project 10: PROJECT10_RESEARCH_DIGEST_AGENT.md
- Project 12: PROJECT12_MCP_INTEGRATION.md
- Project 13 package: Project-13/README.md and supporting files
