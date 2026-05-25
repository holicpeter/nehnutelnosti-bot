from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    scrape_interval_hours: int = 1

    min_price: int = 0
    max_price: int = 500000
    min_area: int = 0
    location: str = "Bratislava"

    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: str = ""

    openai_api_key: str = ""


settings = Settings()
