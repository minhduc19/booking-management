from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["pages"])


@router.get("/index-checkout", response_class=HTMLResponse)
async def read_index():
    with open("frontend/checkout.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@router.get("/index-upload", response_class=HTMLResponse)
async def read_upload():
    with open("frontend/upload.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@router.get("/index-cleaner", response_class=HTMLResponse)
async def read_cleaner():
    with open("frontend/cleaner.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@router.get("/index-bookings", response_class=HTMLResponse)
async def read_bookings():
    with open("frontend/bookings.html", "r", encoding="utf-8") as f:
        html_content = f.read()
    return HTMLResponse(content=html_content)


@router.get("/")
def read_root():
    return {"message": "Changed to private repository"}
