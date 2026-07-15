import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine

router = APIRouter(prefix="/database", tags=["database"])


def _resolve_sqlite_db_path(database_url: str) -> Path:
    sqlite_prefix = "sqlite:///"
    if not database_url.startswith(sqlite_prefix):
        raise HTTPException(status_code=400, detail="Database is not configured for SQLite")

    raw_path = database_url.removeprefix(sqlite_prefix)
    db_path = Path(raw_path)
    if not db_path.is_absolute():
        db_path = Path.cwd() / db_path
    return db_path.resolve()


@router.get("/download")
async def download_database_file():
    db_path = _resolve_sqlite_db_path(settings.database_url)

    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Database file not found")

    return FileResponse(
        path=db_path,
        filename=db_path.name,
        media_type="application/x-sqlite3",
    )


@router.post("/upload")
async def upload_database_file(file: UploadFile = File(...)):
    db_path = _resolve_sqlite_db_path(settings.database_url)

    if not file.filename or not file.filename.endswith(".db"):
        raise HTTPException(status_code=400, detail="Only .db files are supported")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    suffix = db_path.suffix if db_path.suffix else ".db"
    temp_file = tempfile.NamedTemporaryFile(delete=False, dir=db_path.parent, suffix=suffix)
    temp_path = Path(temp_file.name)

    try:
        contents = await file.read()
        if not contents:
            raise HTTPException(status_code=400, detail="Uploaded file is empty")

        temp_file.write(contents)
        temp_file.close()

        engine.dispose()
        os.replace(temp_path, db_path)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Failed to replace database file") from exc
    finally:
        await file.close()
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)

    return {"message": f"Database replaced successfully with {db_path.name}"}
