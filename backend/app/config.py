from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from .env"""
    
    # Paths
    data_dir: str = "../current_code"
    
    # Gemini
    gemini_api_key: str = ""
    
    # Logging
    log_level: str = "info"
    
    # CORS
    allowed_origins: str = "http://localhost:3000"
    
    # Runtime
    max_job_runtime_seconds: int = 600
    poll_interval_seconds: int = 2
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def data_dir_path(self) -> Path:
        """Resolve data directory to absolute path"""
        base = Path(__file__).parent.parent
        return (base / self.data_dir).resolve()
    
    @property
    def shopping_list_path(self) -> Path:
        return self.data_dir_path / "shopping_list.json"
    
    @property
    def cart_jsons_dir(self) -> Path:
        return self.data_dir_path / "cart_jsons"
    
    @property
    def knot_api_jsons_dir(self) -> Path:
        return self.data_dir_path / "knot_api_jsons"
    
    @property
    def runtime_dir(self) -> Path:
        base = Path(__file__).parent.parent
        return (base / "runtime").resolve()
    
    @property
    def jobs_dir(self) -> Path:
        return self.runtime_dir / "jobs"
    
    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


settings = Settings()

