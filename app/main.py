from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import models
from app.database import engine
from app.routers import bookings, cleaners, cleaning_sessions, database, pages

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(database.router)
app.include_router(pages.router)
app.include_router(cleaners.router)
app.include_router(bookings.router)
app.include_router(cleaning_sessions.router)
