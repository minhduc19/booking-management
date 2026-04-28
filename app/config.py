from pydantic import ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = ConfigDict(env_file=".env")

    app_name: str = "FastAPI SQLite App"
    database_url: str = "sqlite:///./app.db"


settings = Settings()