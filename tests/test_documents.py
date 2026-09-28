import io

from pypdf import PdfReader, PdfWriter

from app.config import settings


def make_pdf(page_count: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_upload_and_download_merged_pdfs(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))

    response = client.post(
        "/documents/upload",
        files=[
            ("files", ("first.pdf", make_pdf(), "application/pdf")),
            ("files", ("second.pdf", make_pdf(2), "application/pdf")),
        ],
    )

    assert response.status_code == 200
    assert [item["filename"] for item in response.json()["uploaded"]] == [
        "first.pdf",
        "second.pdf",
    ]

    response = client.get("/documents/merged-download")

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=\"merged-documents.pdf\"" in response.headers[
        "content-disposition"
    ]
    assert len(PdfReader(io.BytesIO(response.content)).pages) == 3


def test_upload_rejects_non_pdf(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))

    response = client.post(
        "/documents/upload",
        files={"files": ("notes.txt", b"not a PDF", "text/plain")},
    )

    assert response.status_code == 400
    assert "not a PDF file" in response.json()["detail"]


def test_upload_rejects_corrupt_pdf(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))

    response = client.post(
        "/documents/upload",
        files={"files": ("broken.pdf", b"%PDF-not-a-real-document", "application/pdf")},
    )

    assert response.status_code == 400
    assert "not a readable PDF" in response.json()["detail"]


def test_merged_download_without_pdfs_returns_not_found(client, monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "uploads_dir", str(tmp_path / "uploads"))

    response = client.get("/documents/merged-download")

    assert response.status_code == 404
    assert response.json()["detail"] == "No uploaded PDF files found"


def test_documents_page_is_served(client):
    response = client.get("/index-documents")

    assert response.status_code == 200
    assert "/documents/upload" in response.text
    assert "/documents/merged-download" in response.text
