import io
import tempfile
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.background import BackgroundTask
from fastapi.responses import FileResponse
from pypdf import PdfReader, PdfWriter
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.database import get_db

router = APIRouter(prefix="/documents", tags=["documents"])


def _uploads_dir() -> Path:
    path = Path(settings.uploads_dir)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _validate_pdf(contents: bytes, filename: str) -> None:
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail=f"{filename} is not a valid PDF")

    try:
        PdfReader(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{filename} is not a readable PDF") from exc


@router.post("/upload")
async def upload_pdfs(
    files: list[UploadFile] = File(...), db: Session = Depends(get_db)
):
    uploaded: list[models.UploadedPdf] = []
    stored_paths: list[Path] = []

    try:
        for file in files:
            filename = file.filename or "upload.pdf"
            if not filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"{filename} is not a PDF file")

            contents = await file.read()
            _validate_pdf(contents, filename)

            storage_name = f"{uuid4().hex}.pdf"
            storage_path = _uploads_dir() / storage_name
            storage_path.write_bytes(contents)
            stored_paths.append(storage_path)
            uploaded_pdf = models.UploadedPdf(
                original_filename=Path(filename).name,
                storage_name=storage_name,
                content_type="application/pdf",
            )
            db.add(uploaded_pdf)
            uploaded.append(uploaded_pdf)

        db.commit()
        for uploaded_pdf in uploaded:
            db.refresh(uploaded_pdf)
    except HTTPException:
        db.rollback()
        for path in stored_paths:
            path.unlink(missing_ok=True)
        raise
    except Exception as exc:
        db.rollback()
        for path in stored_paths:
            path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail="Failed to store PDF files") from exc
    finally:
        for file in files:
            await file.close()

    return {
        "uploaded": [
            {"id": uploaded_pdf.id, "filename": uploaded_pdf.original_filename}
            for uploaded_pdf in uploaded
        ]
    }


def _remove_file(path: Path) -> None:
    path.unlink(missing_ok=True)


@router.get("/merged-download")
def download_merged_pdfs(db: Session = Depends(get_db)):
    uploaded_pdfs = db.query(models.UploadedPdf).order_by(models.UploadedPdf.id).all()
    if not uploaded_pdfs:
        raise HTTPException(status_code=404, detail="No uploaded PDF files found")

    writer = PdfWriter()
    for uploaded_pdf in uploaded_pdfs:
        path = _uploads_dir() / uploaded_pdf.storage_name
        if not path.is_file():
            raise HTTPException(
                status_code=404,
                detail=f"Uploaded PDF {uploaded_pdf.original_filename} is no longer available",
            )
        try:
            writer.append(str(path))
        except Exception as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded PDF {uploaded_pdf.original_filename} could not be merged",
            ) from exc

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as output:
        writer.write(output)
        output_path = Path(output.name)
    writer.close()

    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename="merged-documents.pdf",
        background=BackgroundTask(_remove_file, output_path),
    )
