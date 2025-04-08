from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    api_prefix: str
    api_version: str

    # Database
    database_hostname: str
    database_port: str
    database_password: str
    database_name: str
    database_username: str

    # JWT
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    # openai
    openai_api_key: str

    class Config:
        case_sensitive = False
        env_file = ".env"
        # Environment variables are case-sensitive
        env_file_encoding = "utf-8"


settings = Settings()
