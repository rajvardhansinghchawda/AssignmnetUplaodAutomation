from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List


class Settings(BaseSettings):
    fernet_key: str = ""
    host: str = "0.0.0.0"
    port: int = 8000
    reload: bool = True
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    upload_dir: str = "./uploads"
    max_upload_mb: int = 10
    database_url: str = "postgresql://user:pass@localhost:5432/dbname"
    script_path: str = "./piemr_assignment_upload.py"
    python_exec: str = "python"
    headless: bool = True
    chromedriver_path: str = ""
    scheduler_timezone: str = "Asia/Kolkata"
    log_level: str = "INFO"
    secret_key: str = "your-very-secret-key-change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440 # 24 hours
    google_client_id: str = ""
    google_client_secret: str = ""

    @property
    def cors_origins_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
