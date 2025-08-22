"""
FastAPI Subtitle Extraction API

An async REST API server for extracting subtitles from video URLs.
Built with FastAPI for high-performance async request handling.
"""

import logging
import os
from contextlib import asynccontextmanager
from typing import Optional
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, field_validator

from subtitle_extractor import extract_subtitles

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Security configuration
API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable is required")

# API Key security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=True)


async def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Verify the provided API key matches the configured key.

    Args:
        api_key: The API key from the X-API-Key header

    Returns:
        The verified API key

    Raises:
        HTTPException: If the API key is invalid
    """
    if api_key != API_KEY:
        logger.warning(f"Invalid API key attempt: {api_key[:8]}...")
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "X-API-Key"},
        )
    return api_key


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    logger.info("Starting up Subtitle Extraction API")
    yield
    logger.info("Shutting down Subtitle Extraction API")


# Create FastAPI application with lifespan
app = FastAPI(
    title="Subtitle Extraction API",
    description="Extract subtitles from video URLs with async processing",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS for mobile/web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


# Pydantic models for request/response validation
class SubtitleRequest(BaseModel):
    """Request model for subtitle extraction."""
    url: str
    language: Optional[str] = "en"

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate URL format."""
        if not v or not v.strip():
            raise ValueError("URL cannot be empty")

        # Basic URL validation
        try:
            result = urlparse(v.strip())
            if not all([result.scheme, result.netloc]):
                raise ValueError("Invalid URL format")
        except Exception:
            raise ValueError("Invalid URL format")

        return v.strip()

    @field_validator('language')
    @classmethod
    def validate_language(cls, v: Optional[str]) -> str:
        """Validate language code."""
        if v is None:
            return "en"

        v = v.strip().lower()
        if not v:
            return "en"

        # Basic language code validation (2-5 characters, alphanumeric and hyphens)
        if not v.replace('-', '').isalnum() or len(v) < 2 or len(v) > 5:
            raise ValueError("Invalid language code format")

        return v


class SubtitleResponse(BaseModel):
    """Response model for successful subtitle extraction."""
    success: bool = True
    subtitles: str
    language: str


class ErrorResponse(BaseModel):
    """Response model for errors."""
    success: bool = False
    error: str


def run_subtitle_extraction(url: str, language: str) -> str:
    """
    Wrapper function to run subtitle extraction.

    Args:
        url: Video URL
        language: Language code

    Returns:
        Extracted subtitle text
    """
    try:
        return extract_subtitles(url, language)
    except Exception as e:
        logger.error(f"Error in subtitle extraction: {str(e)}")
        raise


@app.get("/", summary="Health Check")
async def root():
    """Health check endpoint."""
    return {
        "message": "Subtitle Extraction API is running",
        "status": "healthy",
        "version": "1.0.0"
    }


@app.get("/health", summary="Detailed Health Check")
async def health_check():
    """Detailed health check endpoint."""
    return {
        "status": "healthy",
        "service": "Subtitle Extraction API",
        "version": "1.0.0",
        "endpoints": {
            "extract": "/extract-subtitles",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.post("/extract-subtitles",
          response_model=SubtitleResponse,
          responses={
              400: {"model": ErrorResponse, "description": "Bad request"},
              401: {"model": ErrorResponse, "description": "Unauthorized - Invalid API key"},
              404: {"model": ErrorResponse, "description": "Subtitles not found"},
              500: {"model": ErrorResponse, "description": "Internal server error"}
          },
          summary="Extract Subtitles",
          description="Extract subtitles from a video URL with optional language specification")
async def extract_subtitles_endpoint(
    request: SubtitleRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Extract subtitles from a video URL.

    - **url**: Video URL from any supported platform (YouTube, Vimeo, etc.)
    - **language**: Language code (optional, defaults to 'en')

    Returns the extracted subtitle text or an error message.
    """
    try:
        logger.info(
            f"Extracting subtitles from URL: {request.url}, Language: {request.language}")

        # Use FastAPI's built-in run_in_threadpool instead of manual ThreadPoolExecutor
        subtitles = await run_in_threadpool(
            run_subtitle_extraction,
            request.url,
            request.language
        )

        # Check if subtitles were successfully extracted
        if not subtitles or subtitles.strip() == "":
            logger.warning(f"No subtitles found for URL: {request.url}")
            raise HTTPException(
                status_code=404,
                detail=f"No subtitles found for the provided URL in language '{request.language}'"
            )

        logger.info(
            f"Successfully extracted {len(subtitles)} characters of subtitles")

        return SubtitleResponse(
            subtitles=subtitles,
            language=request.language
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except ValueError as e:
        # Handle validation errors
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid request: {str(e)}"
        )

    except ConnectionError as e:
        # Handle network-related errors
        logger.error(f"Connection error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Network error occurred while processing the request"
        )

    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred while processing the request"
        )


if __name__ == "__main__":
    import uvicorn

    # Development server configuration
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
