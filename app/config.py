from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    deepseek_api_key: str = "sk-c2c39af1d60d451ca79845e658e920c5"
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_model: str = "deepseek-v4-pro"
    deepseek_vision_model: str = "deepseek-chat"

    app_host: str = "0.0.0.0"
    app_port: int = 8000


settings = Settings()
