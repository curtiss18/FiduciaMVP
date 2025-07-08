from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.settings import settings
from src.api.endpoints import router
from src.api.advisor_workflow_endpoints import advisor_router
from src.api.audience_endpoints import router as audience_router
from src.api.compliance_endpoints import compliance_router
import logging

# Configure logging
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FiduciaMVP - Warren RAG System",
    description="AI-powered financial compliance content generation",
    version="0.1.0",
    debug=settings.debug
)

# Add CORS middleware - more permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.backend_cors_origins + ["*"],  # Allow all origins in dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router, prefix=settings.api_v1_str)
app.include_router(advisor_router, prefix=settings.api_v1_str)  # Advisor workflow endpoints
app.include_router(audience_router, prefix=settings.api_v1_str)  # Audience CRUD endpoints
app.include_router(compliance_router, prefix=settings.api_v1_str)  # NEW: Compliance portal endpoints

# Root endpoint
@app.get("/")
async def root():
    return {"message": "FiduciaMVP API is running", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
