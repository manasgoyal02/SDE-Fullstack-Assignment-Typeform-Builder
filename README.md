# Typeflow — Typeform-style Form Builder

Typeflow is a full-stack form builder with a drag-and-drop editor, public shareable forms, response results, CSV export, SQLite persistence, responsive layouts, and basic conditional branching.

## Live deployment

- Frontend: https://frontend-sigma-nine-79.vercel.app
- Backend API: https://sde-fullstack-assignment-typeform-builder-production.up.railway.app
- Health check: https://sde-fullstack-assignment-typeform-builder-production.up.railway.app/health

The health endpoint returns `{"ok": true}` when the backend is available. Published forms are accessible at:

```text
https://frontend-sigma-nine-79.vercel.app/to/<form-slug>
```

Public respondent links do not require a Vercel account.

## Architecture overview

```text
Browser
  │
  │ HTTPS
  ▼
Next.js frontend on Vercel
  │
  │ REST API requests using NEXT_PUBLIC_API_URL
  ▼
FastAPI backend on Railway
  │
  │ SQLite queries
  ▼
SQLite database on Railway persistent volume (/data/typeflow.db)
```

### Frontend

The `frontend/` directory contains the Next.js application. It provides the form list, form builder, settings, public respondent experience, response results, and CSV export link. The frontend reads the backend base URL from `NEXT_PUBLIC_API_URL`.

### Backend

The `backend/` directory contains the FastAPI application in `backend/main.py`. It handles form CRUD, publishing, public form access, response validation and storage, response summaries, response details, and CSV export. CORS allows the local frontend and Vercel deployments.

### Persistence

SQLite is used for local development. Railway stores the production database at `/data/typeflow.db` on its persistent volume, configured through `TYPEFLOW_DB_PATH`.

## Stack

- Frontend: Next.js 15, React 19, TypeScript, and dnd-kit
- Backend: FastAPI, Pydantic, and Uvicorn
- Database: SQLite
- Hosting: Vercel for the frontend and Railway for the backend

## Setup instructions

### Prerequisites

- Python 3.12 or compatible Python 3.x
- Node.js and npm
- Git

### Run the backend locally

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The local API runs at `http://localhost:8000`. The local SQLite database is created at `backend/typeflow.db` unless `TYPEFLOW_DB_PATH` is set.

### Run the frontend locally

Open a second terminal:

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Open http://localhost:3000.

To run a production-style local frontend:

```powershell
cd frontend
npm run build
npm run start
```

### Environment variables

Frontend local value:

```text
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Frontend production value:

```text
NEXT_PUBLIC_API_URL=https://sde-fullstack-assignment-typeform-builder-production.up.railway.app
```

Railway backend value:

```text
TYPEFLOW_DB_PATH=/data/typeflow.db
```

Do not commit tokens or other secrets to the repository.

## Database schema

The schema is initialized automatically at backend startup by `init_db()` in `backend/main.py`.

### `forms`

Stores form metadata and serialized settings.

| Column | Type | Description |
| --- | --- | --- |
| `id` | `TEXT PRIMARY KEY` | Internal form identifier |
| `title` | `TEXT NOT NULL` | Form title |
| `slug` | `TEXT UNIQUE NOT NULL` | Public URL identifier |
| `status` | `TEXT NOT NULL` | `draft` or `published` |
| `settings` | `TEXT NOT NULL` | JSON containing theme, thank-you text, and optional logic rule |
| `created_at` | `TEXT NOT NULL` | UTC creation timestamp |
| `updated_at` | `TEXT NOT NULL` | UTC modification timestamp |

### `questions`

Stores the ordered questions belonging to a form.

| Column | Type | Description |
| --- | --- | --- |
| `id` | `TEXT PRIMARY KEY` | Question identifier |
| `form_id` | `TEXT NOT NULL` | References `forms.id`; cascade deletes with the form |
| `position` | `INTEGER NOT NULL` | Display order within the form |
| `type` | `TEXT NOT NULL` | Question type, such as `short_text`, `email`, or `yes_no` |
| `title` | `TEXT NOT NULL` | Question text |
| `description` | `TEXT NOT NULL` | Optional help text |
| `required` | `INTEGER NOT NULL` | SQLite boolean flag |
| `options` | `TEXT NOT NULL` | JSON array for choice, dropdown, yes/no, or rating options |

### `responses`

Stores one submission for a published form.

| Column | Type | Description |
| --- | --- | --- |
| `id` | `TEXT PRIMARY KEY` | Response identifier |
| `form_id` | `TEXT NOT NULL` | References `forms.id`; cascade deletes with the form |
| `submitted_at` | `TEXT NOT NULL` | UTC submission timestamp |

### `answers`

Stores individual answers belonging to a response.

| Column | Type | Description |
| --- | --- | --- |
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Answer row identifier |
| `response_id` | `TEXT NOT NULL` | References `responses.id`; cascade deletes with the response |
| `question_id` | `TEXT NOT NULL` | ID of the question answered |
| `value` | `TEXT` | Submitted answer value |

Indexes are created for form slugs, question ordering, response listing, and answer lookups.

## API overview

The API returns JSON unless an endpoint explicitly returns CSV. Request bodies for form creation and updates use this shape:

```json
{
  "title": "Team check-in",
  "questions": [],
  "settings": {}
}
```

### System and form management

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Service health check |
| `GET` | `/forms` | List forms with metadata and response counts |
| `POST` | `/forms` | Create a draft form |
| `GET` | `/forms/{form_id}` | Get one form and its questions |
| `PUT` | `/forms/{form_id}` | Update title, questions, settings, and ordering |
| `DELETE` | `/forms/{form_id}` | Delete a form and dependent data |
| `POST` | `/forms/{form_id}/duplicate` | Duplicate a form as a new draft |
| `POST` | `/forms/{form_id}/publish?published=true` | Publish or unpublish a form |

### Responses and exports

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/forms/{form_id}/responses` | List responses and choice summaries |
| `GET` | `/forms/{form_id}/responses/{response_id}` | Get one response and its answers |
| `GET` | `/forms/{form_id}/export.csv` | Download responses as CSV |

### Public respondent API

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/public/forms/{slug}` | Get a published form for rendering |
| `POST` | `/public/forms/{slug}/responses` | Submit answers to a published form |

The submission endpoint validates required questions, email format, and numeric answers. Invalid submissions return HTTP `422` with validation details.

## Basic branching

Configure branching from **Settings → Logic jumps**:

1. Select a source question.
2. Select the answer that should trigger the rule.
3. Select a later question to jump to.

The target must be at least two positions after the source, so at least one question is skipped. Matching is case-insensitive, including for Yes/No questions. A non-matching answer continues to the next question. Invalid branching updates are rejected by the backend instead of replacing a valid rule.

## Automatic deployment

When the GitHub repository is connected to the hosting providers, pushes to `main` can trigger deployments:

- Vercel builds the `frontend/` project and deploys the frontend.
- Railway builds and deploys the backend service.

The Vercel project must use `frontend/` as its root directory, and its `NEXT_PUBLIC_API_URL` must point to the Railway API. Deployment commands and provider-specific configuration are documented in [DEPLOYMENT.md](DEPLOYMENT.md).

After deployment, verify `/health`, the frontend, public form submission, branching, response results, and CSV export.

## Security

Deployment tokens authenticate provider CLI commands only; they are not required by the application at runtime. Revoke and regenerate any token that is exposed. Keep secrets out of source files, README files, Git history, and client-side environment variables.
