from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    LLM_PROVIDER: str = "openai"
    BLABLADOR_API_KEY: str = ""
    HELMHOLTZ_BLABLADOR_ENDPOINT: str = "https://api.helmholtz-blablador.fz-juelich.de/v1"
    MODEL_ALIAS_LARGE: str = "alias-large"
    MODEL_ALIAS_HUGE: str = "alias-huge"
    MAX_CONCURRENCY: int = 5
    PERSONA_POOL_REPO: str = "https://github.com/JsonLord/agent-notes.git"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
