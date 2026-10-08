# SDE-Fullstack-Assignment-Typeform-Builder

# Typeflow — Typeform-style Form Builder

Full-stack Typeform clone with a drag-and-drop builder, shareable public forms, SQLite persistence, and response results.

## Stack

- Frontend: Next.js 15, TypeScript, React, and dnd-kit
- Backend: FastAPI and SQLite
- Database: SQLite

## Run Locally

### Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000