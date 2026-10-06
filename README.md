# Automotive Requirement Intelligence Platform — Upload MVP

First slice: upload PDF or DOCX files. Files are stored in Azure Blob Storage when configured, otherwise in local disk for development. This slice does not yet extract requirements, use RAG, or call AI agents.

## Run locally
Requires Python 3.11+ and Node.js 20+.

### Backend
```bash
cd backend
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend
In a second terminal:
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

## Azure Blob Storage
Set these variables in the backend environment (never in the frontend):
- `AZURE_STORAGE_CONNECTION_STRING`
- `AZURE_STORAGE_CONTAINER` (defaults to `requirement-source-files`)
- `FRONTEND_ORIGINS` (defaults to `http://localhost:5173`)

For production, prefer managed identity / Microsoft Entra ID, add authentication, malware scanning, and persist document metadata in Azure SQL. The current metadata list is in-memory and resets on API restart.

## Endpoints
- `GET /api/health`
- `GET /api/documents`
- `POST /api/documents` (multipart `file`; PDF/DOCX, max 25 MB)
