from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings
from app.routers import analyze, generate, validate, phishlets

app = FastAPI(
    title="RTLPhishletGenerator API",
    version="2.0.0",
    description="Automated Evilginx v3 Phishlet Generator for Red Team Engagements - 2026+ Edition",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_credentials,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # CSP for frontend
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self' https://*; frame-ancestors 'none';"
        
        return response


app.add_middleware(SecurityHeadersMiddleware)

# Include routers
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analysis"])
app.include_router(generate.router, prefix="/api/v1/generate", tags=["Generation"])
app.include_router(validate.router, prefix="/api/v1/validate", tags=["Validation"])
app.include_router(phishlets.router, prefix="/api/v1/phishlets", tags=["Library"])


@app.get("/api/v1/health")
async def health():
    """Health check endpoint with AI provider status"""
    from app.services.ai_service import AIService
    
    ai_service = AIService()
    
    return {
        "status": "ok",
        "version": "2.0.0",
        "ai_enabled": settings.ai_enabled,
        "ai_available_providers": ai_service.get_available_providers(),
        "ai_status": ai_service.get_status(),
    }


@app.get("/")
async def root():
    """API root - provides documentation links"""
    return {
        "name": "RTLPhishletGenerator API",
        "version": "2.0.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "health": "/api/v1/health",
    }

