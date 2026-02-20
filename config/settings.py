"""
weAID Configuration Settings
생활지능파트너 설정
"""
from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Anthropic API
    anthropic_api_key: str = ""
    claude_model: str = "claude-sonnet-4-6"

    # App Settings
    app_name: str = "weAID"
    app_subtitle: str = "생활지능파트너"
    app_version: str = "1.0.0"
    debug: bool = False

    # Voice Settings
    voice_language: str = "ko-KR"
    tts_engine: str = "gtts"  # gtts or pyttsx3
    stt_timeout: int = 5
    stt_phrase_limit: int = 30

    # Ontology Paths
    ontology_path: str = str(BASE_DIR / "ontology" / "weaid_ontology.owl")
    knowledge_base_path: str = str(BASE_DIR / "ontology" / "knowledge_base.ttl")

    # API Settings
    host: str = "0.0.0.0"
    port: int = 8001
    cors_origins: list = ["*"]

    # Session
    max_history: int = 20

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
