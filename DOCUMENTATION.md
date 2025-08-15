# Video Subtitle Extractor

A comprehensive Python system for extracting subtitles from video URLs using yt-dlp, with CLI and REST API interfaces.

## Overview

This project provides three ways to extract subtitles from videos:

1. **Core Module** (`subtitle_extractor.py`): Python function for direct integration
2. **Command Line Interface** (`cli.py`): Terminal-based tool
3. **REST API Server** (`api.py`): Web API for applications

## Quick Start

### Prerequisites
- Python 3.13+
- `uv` package manager
- Internet connectivity

### Installation
```bash
# Install dependencies using uv virtual environment
uv sync
```

## Usage

### 1. Command Line Interface

```bash
# Basic usage
uv run python cli.py "https://www.youtube.com/watch?v=VIDEO_ID"

# With language specification
uv run python cli.py "https://example.com/video" --language es

# With verbose output
uv run python cli.py "https://example.com/video" --verbose

# Pipe to file
uv run python cli.py "https://example.com/video" > subtitles.txt

# Show help
uv run python cli.py --help
```

**Exit Codes:**
- `0`: Success
- `1`: General error (invalid URL, extraction failure)
- `2`: Invalid arguments

### 2. Python Module

```python
from subtitle_extractor import extract_subtitles

# Extract English subtitles
subtitles = extract_subtitles("https://www.youtube.com/watch?v=VIDEO_ID", "en")

# Extract subtitles in other languages
subtitles = extract_subtitles("https://example.com/video", "es")
```

### 3. REST API

#### Start the API Server

```bash
# Development server
uv run python api.py

# Production server
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

#### API Endpoints

- **Health Check**: `GET /health`
- **Subtitle Extraction**: `POST /extract-subtitles`
- **API Documentation**: `GET /docs`

#### API Usage Example

```bash
curl -X POST "http://localhost:8000/extract-subtitles" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "language": "en"
  }'
```

**Response Format:**
```json
{
  "success": true,
  "subtitles": "extracted subtitle text...",
  "language": "en"
}
```

## Production Deployment

### Local Development Setup

1. **Navigate to Project Directory**
   ```bash
   cd /path/to/downloader
   ```

2. **Install Dependencies**
   ```bash
   uv sync
   ```

3. **Run Development Server**
   ```bash
   # Direct Python execution
   uv run python api.py
   
   # Using uvicorn
   uv run uvicorn api:app --host 0.0.0.0 --port 8000 --reload
   ```

4. **Verify Installation**
   ```bash
   # Health check
   curl http://localhost:8000/health
   
   # API documentation
   open http://localhost:8000/docs
   ```

### Production Deployment Options

#### Option 1: Direct uvicorn

```bash
# Install production dependencies
uv sync --no-dev

# Start production server
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4

# Background execution
nohup uv run uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4 > api.log 2>&1 &
```

#### Option 2: systemd Service (Linux)

Create service file (`/etc/systemd/system/subtitle-api.service`):
```ini
[Unit]
Description=Subtitle Extraction API
After=network.target

[Service]
Type=exec
User=your-user
Group=your-group
WorkingDirectory=/path/to/downloader
ExecStart=/path/to/uv run uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl daemon-reload
sudo systemctl enable subtitle-api
sudo systemctl start subtitle-api
sudo systemctl status subtitle-api
```

#### Option 3: PM2 Process Manager

```bash
# Install PM2
npm install -g pm2

# Create ecosystem.config.js
cat > ecosystem.config.js << EOF
module.exports = {
  apps: [{
    name: 'subtitle-api',
    script: 'uv',
    args: 'run uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4',
    cwd: '/path/to/downloader',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G'
  }]
};
EOF

# Start with PM2
pm2 start ecosystem.config.js
pm2 startup
pm2 save
```

### Configuration Options

#### Environment Variables
```bash
export HOST=0.0.0.0
export PORT=8000
export WORKERS=4
export LOG_LEVEL=info
export ALLOWED_ORIGINS="https://yourdomain.com"
```

#### uvicorn Options
```bash
--host 0.0.0.0              # Bind to all interfaces
--port 8000                 # Port number
--workers 4                 # Number of worker processes
--log-level info           # Logging level
--ssl-keyfile /path/to/key.pem    # SSL key (optional)
--ssl-certfile /path/to/cert.pem  # SSL cert (optional)
```

### Reverse Proxy (Nginx)

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long subtitle extraction
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

## Features

### Core Features
- Extract subtitles from any video URL supported by yt-dlp
- Support for multiple languages
- Automatic fallback to auto-generated subtitles
- Clean subtitle text output (no timestamps or formatting)
- Comprehensive error handling

### CLI Features
- Simple command-line interface
- Output piping support
- Verbose logging mode
- Helpful error messages and exit codes

### API Features
- Async REST API with FastAPI
- CORS support for web applications
- Auto-generated API documentation
- Proper HTTP status codes
- Thread pool execution for performance

## Error Handling

The system handles various error conditions gracefully:

- **Invalid URLs**: Validation and clear error messages
- **No subtitles available**: Informative responses
- **Network issues**: Proper timeout handling
- **Processing errors**: Fallback mechanisms

## Monitoring and Troubleshooting

### Health Monitoring
```bash
# Simple health check
curl -f http://localhost:8000/health
```

### Common Issues

1. **Port Already in Use**
   ```bash
   lsof -i :8000  # Find process using port
   kill -9 <PID>  # Kill process
   ```

2. **Permission Denied**
   ```bash
   chown -R user:group /path/to/downloader
   ```

3. **yt-dlp Issues**
   ```bash
   uv add yt-dlp --upgrade
   ```

### Logs and Debugging
```bash
# Check application logs
tail -f api.log

# Check system service logs (systemd)
journalctl -u subtitle-api -f

# Test core functionality
uv run python -c "from subtitle_extractor import extract_subtitles; print(extract_subtitles('https://www.youtube.com/watch?v=dQw4w9WgXcQ'))"
```

## Performance Considerations

1. **Worker Processes**: Use `--workers` based on CPU cores (typically 2x cores)
2. **Memory**: Monitor memory usage during subtitle extraction
3. **Timeouts**: Adjust timeouts for slow video URLs
4. **Rate Limiting**: Consider implementing rate limiting for production use

## Security Considerations

1. **CORS**: Configure allowed origins for production
2. **Input Validation**: URL validation included
3. **Rate Limiting**: Implement to prevent abuse
4. **SSL/TLS**: Use HTTPS in production
5. **Firewall**: Restrict access to necessary ports

## Dependencies

The project uses the following key dependencies:
- `yt-dlp`: Video information and subtitle extraction
- `fastapi`: Web API framework
- `uvicorn`: ASGI server
- `pydantic`: Data validation

All dependencies are managed through `pyproject.toml` and installed via `uv`.

## File Structure

```
downloader/
├── subtitle_extractor.py    # Core extraction module
├── cli.py                  # Command-line interface
├── api.py                  # REST API server
├── main.py                 # Entry point
├── pyproject.toml          # Dependencies and project config
├── uv.lock                 # Dependency lock file
└── DOCUMENTATION.md        # This file
```

## Support

For issues and questions:
1. Check the API documentation at `/docs` (when running the API)
2. Review logs for error messages
3. Verify URL accessibility and subtitle availability
4. Test with known working URLs (YouTube videos with subtitles)
