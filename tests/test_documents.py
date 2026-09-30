import io

from pypdf import PdfReader, PdfWriter

from .database import client, session


def make_pdf(page_count: int = 1) -> bytes:
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(width=72, height=72)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def test_merge_and_download_pdfs(client):
    response = client.post(
        "/documents/merge-download",
        files=[
            ("files", ("first.pdf", make_pdf(), "application/pdf")),
            ("files", ("second.pdf", make_pdf(2), "application/pdf")),
        ],
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment; filename=\"merged-documents.pdf\"" in response.headers[
        "content-disposition"
    ]
    assert len(PdfReader(io.BytesIO(response.content)).pages) == 3


def test_merge_rejects_non_pdf(client):
    response = client.post(
        "/documents/merge-download",
        files={"files": ("notes.txt", b"not a PDF", "text/plain")},
    )

    assert response.status_code == 400
    assert "not a PDF file" in response.json()["detail"]


def test_merge_rejects_corrupt_pdf(client):
    response = client.post(
        "/documents/merge-download",
        files={"files": ("broken.pdf", b"%PDF-not-a-real-document", "application/pdf")},
    )

    assert response.status_code == 400
    assert "not a readable PDF" in response.json()["detail"]


def test_documents_page_is_served(client):
    response = client.get("/index-documents")

    assert response.status_code == 200
    assert "/documents/merge-download" in response.text
