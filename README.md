# Automotive Requirement Intelligence Platform — Upload MVP

Upload PDF or DOCX files, then extract document text and identify preliminary requirement candidates for engineer review. Files are stored in Azure Blob Storage when configured, otherwise on local disk for development. This MVP does not use RAG or call AI agents.

## Run locally
Requires Python 3.11+ and Node.js 20+.

Runtime configuration is read from the repository-root `.env` file by both
the backend and Vite frontend. The file is ignored by Git. Set
`AZURE_STORAGE_CONNECTION_STRING` there to enable Azure Blob Storage; leave
it empty to use local development storage. The shared
`VITE_MAX_UPLOAD_SIZE_MB` setting controls the upload limit in both frontend
and backend.

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
Configure `AZURE_STORAGE_CONNECTION_STRING` and `AZURE_STORAGE_CONTAINER` in
the repository-root `.env` file (never put storage credentials in frontend
variables). The checked-out local `.env` starts with an empty connection
string, so the backend uses local storage until configured.

For production, prefer managed identity / Microsoft Entra ID, add authentication, malware scanning, and persist document metadata in Azure SQL. The current metadata list is in-memory and resets on API restart.

## Endpoints
- `GET /api/health`
- `GET /api/documents`
- `POST /api/documents` (multipart `file`; PDF/DOCX, max 25 MB)
- `POST /api/documents/{document_id}/extract` (extracts locally stored documents; Azure Blob extraction is not yet supported)

Extraction returns document text and rule-based candidate requirements. Scanned PDFs without selectable text are not supported. Candidates are preliminary suggestions and require engineer review.
