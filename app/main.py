from fastapi import FastAPI
from app.core.config import settings
from app.routers import auth, registration, user, files


app = FastAPI(
    title="REWE Invoice API",
    version=settings.api_version,
)


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(registration.router, prefix=settings.api_prefix)
app.include_router(user.router, prefix=settings.api_prefix)
app.include_router(files.router, prefix=settings.api_prefix)
