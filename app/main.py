from fastapi import FastAPI
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, registration, user, files, ai_analysis, invitation, admin


app = FastAPI(
    title="REWE Invoice API",
    version=settings.api_version,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Add your Next.js URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(registration.router, prefix=settings.api_prefix)
app.include_router(user.router, prefix=settings.api_prefix)
app.include_router(files.router, prefix=settings.api_prefix)
app.include_router(ai_analysis.router, prefix=settings.api_prefix)
app.include_router(invitation.router, prefix=settings.api_prefix)

app.include_router(admin.router, prefix=settings.api_prefix)
