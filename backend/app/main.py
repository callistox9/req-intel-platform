import os, re, uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
UPLOADS = ROOT / "uploads"
UPLOADS.mkdir(parents=True, exist_ok=True)
MAX_BYTES = 25 * 1024 * 1024
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
app = FastAPI(title="Requirement Intelligence Platform API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("FRONTEND_ORIGINS", "http://localhost:5173").split(","),
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
documents: list[dict[str, Any]] = []


def clean_name(value: str) -> str:
    return (
        re.sub(r"[^A-Za-z0-9._ -]", "_", Path(value).name).strip(" .")[:180]
        or "document"
    )


async def store(name: str, data: bytes, mime: str) -> str:
    connection = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
    container_name = os.getenv("AZURE_STORAGE_CONTAINER", "requirement-source-files")
    if connection:
        from azure.storage.blob import BlobServiceClient, ContentSettings

        try:
            service = BlobServiceClient.from_connection_string(connection)
            container = service.get_container_client(container_name)
            try:
                container.create_container()
            except Exception:
                pass
            container.get_blob_client(name).upload_blob(
                data,
                overwrite=False,
                content_settings=ContentSettings(content_type=mime),
            )
            return f"azure-blob:{container_name}/{name}"
        except Exception as exc:
            raise HTTPException(
                502, f"Azure Blob Storage upload failed: {exc}"
            ) from exc
    (UPLOADS / name).write_bytes(data)
    return f"local:{name}"


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "storage_mode": (
            "azure-blob" if os.getenv("AZURE_STORAGE_CONNECTION_STRING") else "local"
        ),
    }


@app.get("/api/documents")
def list_documents():
    return sorted(documents, key=lambda d: d["uploaded_at"], reverse=True)


@app.post("/api/documents", status_code=201)
async def upload_document(file: UploadFile = File(...)):
    filename = clean_name(file.filename or "document")
    ext = Path(filename).suffix.lower()
    if ext not in (".pdf", ".docx"):
        raise HTTPException(415, "Unsupported file type. Upload PDF or DOCX.")
    mime = "application/pdf" if ext == ".pdf" else DOCX_MIME
    if file.content_type not in (mime, "application/octet-stream", None, ""):
        raise HTTPException(415, "File content type does not match PDF or DOCX.")
    data = await file.read(MAX_BYTES + 1)
    if not data:
        raise HTTPException(400, "The uploaded file is empty.")
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Maximum file size is 25 MB.")
    if ext == ".pdf" and not data.startswith(b"%PDF-"):
        raise HTTPException(415, "The file does not appear to be a valid PDF.")
    if ext == ".docx" and not data.startswith(b"PK"):
        raise HTTPException(415, "The file does not appear to be a valid DOCX.")
    doc_id = str(uuid.uuid4())
    ref = await store(doc_id + ext, data, mime)
    record = {
        "id": doc_id,
        "filename": filename,
        "content_type": mime,
        "size_bytes": len(data),
        "uploaded_at": datetime.now(timezone.utc).isoformat(),
        "storage": ref,
        "status": "uploaded",
    }
    documents.append(record)
    return record
