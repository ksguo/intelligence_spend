from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API
    api_prefix: str
    api_version: str

    # CORS
    cors_origins: str = "*"  # 默认允许所有源，但应在生产环境中限制
    cors_headers: str = "*"
    cors_methods: str = "*"

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

    # 将逗号分隔的字符串转换为列表
    @property
    def cors_origins_list(self):
        if self.cors_origins == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",")]

    @property
    def cors_headers_list(self):
        if self.cors_headers == "*":
            return ["*"]
        return [header.strip() for header in self.cors_headers.split(",")]

    @property
    def cors_methods_list(self):
        if self.cors_methods == "*":
            return ["*"]
        return [method.strip() for method in self.cors_methods.split(",")]


settings = Settings()
