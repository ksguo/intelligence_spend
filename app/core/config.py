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

    class Config:
        case_sensitive = True
        env_file = ".env"


settings = Settings()
