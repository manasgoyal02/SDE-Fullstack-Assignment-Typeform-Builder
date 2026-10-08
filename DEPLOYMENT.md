# Typeflow Deployment Notes

## Architecture

- Next.js frontend on Vercel (`frontend/`)
- FastAPI backend on Railway (`backend/`)
- SQLite on a Railway persistent volume mounted at `/data`

## Railway backend

```text
Project ID: 41efad63-b494-4e6f-926d-503f3788df85
Service: SDE-Fullstack-Assignment-Typeform-Builder
API: https://sde-fullstack-assignment-typeform-builder-production.up.railway.app
Health: https://sde-fullstack-assignment-typeform-builder-production.up.railway.app/health
```

Expected health response:

```json
{"ok": true}
```

Railway variable:

```text
TYPEFLOW_DB_PATH=/data/typeflow.db
```

The backend is built with the root `Dockerfile`, which copies `backend/main.py` and `backend/requirements.txt` and starts Uvicorn on Railway's `PORT`.

## Vercel frontend

Production URL:

```text
https://frontend-sigma-nine-79.vercel.app
```

Vercel production variable:

```text
NEXT_PUBLIC_API_URL=https://sde-fullstack-assignment-typeform-builder-production.up.railway.app
```

The production build completed successfully on Vercel.

## Pending final verification

The latest `backend/main.py` includes the Vercel production origin in CORS. Redeploy the Railway backend once after that change, then verify:

1. Open the Vercel URL.
2. Create or open a form.
3. Publish and copy the public link.
4. Submit a response through `/to/{slug}`.
5. Open Results and test individual response view and CSV export.

If the evaluator must access the site without signing into Vercel, disable Vercel Deployment Protection for the production deployment.

## Deployment commands

Railway:

```powershell
$env:RAILWAY_TOKEN="<project-token>"
npx.cmd --cache .railway-npm-cache @railway/cli up --project 41efad63-b494-4e6f-926d-503f3788df85 --environment production --service SDE-Fullstack-Assignment-Typeform-Builder --ci
```

Vercel:

```powershell
$env:VERCEL_TOKEN="<vercel-token>"
npx.cmd --cache ..\.vercel-npm-cache vercel --prod --yes --token $env:VERCEL_TOKEN
```

## Credential security

Revoke the Railway and Vercel tokens used during setup after deployment is confirmed. Never commit tokens to Git or this file.
