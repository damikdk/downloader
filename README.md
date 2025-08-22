# Downloader

A Python application for downloading and extracting subtitles from YouTube videos.

```bash
uv sync
```

## How to Run

This project provides both a command-line interface (CLI) and a web API server.

### Command Line Interface (CLI)

Extract subtitles directly from the command line:

```bash
# Basic usage
uv run python cli.py "https://www.youtube.com/watch?v=VIDEO_ID"

# Specify language
uv run python cli.py "https://www.youtube.com/watch?v=VIDEO_ID" --language es

# Save to file
uv run python cli.py "https://www.youtube.com/watch?v=VIDEO_ID" > subtitles.txt

# Verbose output
uv run python cli.py "https://www.youtube.com/watch?v=VIDEO_ID" --verbose
```

### Web API Server

Start the FastAPI server using uvicorn:

```bash
# Development server with auto-reload
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload

# Production server
uv run uvicorn api:app --host 0.0.0.0 --port 8000
```

Once the server is running, you can:
- View API documentation at: `http://localhost:8000/docs`
- Access ReDoc documentation at: `http://localhost:8000/redoc`
- Check health status at: `http://localhost:8000/health`

#### API Usage Examples

```bash
# Extract subtitles via API
curl -X POST "http://localhost:8000/extract-subtitles" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://www.youtube.com/watch?v=VIDEO_ID", "language": "en"}'

# Health check
curl "http://localhost:8000/health"
```

## Running Tests

To run the test suite, use the following command:

```bash
# Run all tests
uv run python -m pytest

# Run tests with verbose output
uv run python -m pytest -v

# Run specific test file
uv run python -m pytest tests/test_subtitle_extractor.py -v

# Run tests without warnings
uv run python -m pytest --disable-warnings

# Run tests with coverage
uv run python -m pytest --cov
```

- Tests use pytest framework with parametrized test cases

### Important Notes

- Some tests may fail due to YouTube rate limiting (HTTP 429 errors) - this is expected behavior

## Quick Deployment

### Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc
```

### Clone and Setup
```bash
git clone <your-repo-url> ~/downloader
cd ~/downloader
uv sync
```

### Start the API
```bash
# Production (4 workers)
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### Check

- API docs: `http://your-server-ip:8000/docs`
- Health check: `http://your-server-ip:8000/health`

## Development

For development dependencies (like pytest), they are included in the `dev` dependency group and will be installed automatically with `uv sync`.
