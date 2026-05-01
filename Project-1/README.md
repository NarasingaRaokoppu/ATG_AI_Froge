# Amzur AI Chat

Multi-user conversational AI platform with:
- Threaded persistent chat
- Email/password and Google OAuth authentication
- Conversational memory
- Multi-modal input (images, video, code, PDF)
- AI image generation
- RAG over uploaded documents
- Natural language querying of databases and spreadsheets

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # On Windows
pip install -r requirements.txt
cp ../.env.example ../.env  # Configure environment variables
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Visit `http://localhost:5173` and the backend will be at `http://localhost:8000`.

## Project Structure

See `.github/copilot-instructions.md` for full architecture and conventions.
