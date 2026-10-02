import io

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pypdf import PdfReader, PdfWriter

router = APIRouter(prefix="/documents", tags=["documents"])


def _validate_pdf(contents: bytes, filename: str) -> None:
    if not contents.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail=f"{filename} is not a valid PDF")

    try:
        PdfReader(io.BytesIO(contents))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"{filename} is not a readable PDF") from exc


@router.post("/merge-download")
async def merge_and_download_pdfs(files: list[UploadFile] = File(...)):
    """Merge submitted PDFs in memory without persisting uploads."""
    writer = PdfWriter()

    try:
        for file in files:
            filename = file.filename or "upload.pdf"
            if not filename.lower().endswith(".pdf"):
                raise HTTPException(status_code=400, detail=f"{filename} is not a PDF file")

            contents = await file.read()
            _validate_pdf(contents, filename)
            writer.append(io.BytesIO(contents))

        output = io.BytesIO()
        writer.write(output)
        output.seek(0)
    finally:
        writer.close()
        for file in files:
            await file.close()

    return StreamingResponse(
        output,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="merged-documents.pdf"'},
    )
