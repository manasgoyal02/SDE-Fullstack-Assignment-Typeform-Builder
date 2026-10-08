# Typeflow — Typeform-style Form Builder

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
```

## Live deployment

- Frontend: https://frontend-sigma-nine-79.vercel.app
- Backend API: https://sde-fullstack-assignment-typeform-builder-production.up.railway.app
- Health check: https://sde-fullstack-assignment-typeform-builder-production.up.railway.app/health

The health endpoint should return `{"ok": true}`. Public forms are available at `https://frontend-sigma-nine-79.vercel.app/to/<form-slug>` and do not require a Vercel account.

## Features

- Create, edit, reorder, duplicate, publish, and delete forms
- Short text, long text, multiple choice, dropdown, email, number, yes/no, and rating questions
- Public respondent links, response viewing, and CSV export
- Fluid responsive layout for desktop, tablet, and mobile widths
- Basic logic jumps / conditional branching
- Response notifications, integrations/webhooks, and advanced collaboration features are marked Coming Soon

### Basic branching

Configure branching from **Settings → Logic jumps**:

1. Select a source question.
2. Select the triggering answer.
3. Select a later question to jump to.

The target must be at least two positions after the source, so at least one question is skipped. Matching is case-insensitive, including for Yes/No questions. A non-matching answer continues to the next question normally. Invalid branching updates are rejected by the backend instead of silently replacing a valid rule.

## Frontend local setup

In a second terminal:

```powershell
cd frontend
npm install
$env:NEXT_PUBLIC_API_URL="http://localhost:8000"
npm run dev
```

Open http://localhost:3000. For a production-style local build, run `npm run build` followed by `npm run start` from `frontend/`.

## Environment variables

Frontend production value:

```text
NEXT_PUBLIC_API_URL=https://sde-fullstack-assignment-typeform-builder-production.up.railway.app
```

Railway value:

```text
TYPEFLOW_DB_PATH=/data/typeflow.db
```

Never commit API tokens, database credentials, or deployment secrets.

## Automatic deployment

When the GitHub repository is connected to the hosting providers, pushes to `main` trigger a Vercel frontend deployment and a Railway backend redeployment when Railway detects the change. The Vercel project must use `frontend/` as its root directory, and `NEXT_PUBLIC_API_URL` must point to Railway.

Manual deployment commands and provider configuration are documented in [DEPLOYMENT.md](DEPLOYMENT.md).

After deployment, verify the frontend, backend health endpoint, public form submission, branching, response results, and CSV export.

## Security

Deployment tokens are only used to authenticate deployment commands; they are not required by the application at runtime. Revoke and regenerate any token that is exposed. Keep secrets out of source files, README files, Git history, and client-side environment variables.
