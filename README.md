# WordPress Content Extractor API

Extracts all Posts of a type from a WordPress Website via REST API with support for long-running requests through asynchronous processing.

## Stack

- Flask
- BeautifulSoup
- Gunicorn (Production WSGI Server)
- Celery (Async Task Processing)
- Redis (Message Broker)

## Quick Start

### Development Mode

```bash
python main.py
```

### Production Mode with Async Support

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Or using the startup script
./start_async_dev.sh
```

## API Endpoints

### Synchronous (for small extractions)

- `POST /extract` - Extract content synchronously

### Asynchronous (for large extractions, 100+ seconds)

- `POST /extract/async` - Start async extraction task
- `GET /extract/status/<task_id>` - Check task progress

### Health & Debug

- `GET /health` - Health check
- `GET /debug/redis` - Test Redis connection
- `GET /debug/celery` - Check worker status

## Example Usage

### Async Extraction (Recommended for large sites)

```bash
# Start extraction
curl -X POST https://your-domain.com/extract/async \
  -H "Content-Type: application/json" \
  -d '{
    "baseUrl": "https://large-wordpress-site.com",
    "postType": "posts"
  }'

# Check progress
curl https://your-domain.com/extract/status/[task-id]
```

## Deployment

For complete deployment instructions including Coolify setup, troubleshooting, and configuration, see:

**📖 [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)**

The deployment guide covers:

- Coolify deployment steps
- Environment variable configuration
- Redis and Celery worker setup
- Troubleshooting common issues
- Performance optimization
- Monitoring and debugging

## Key Features

- ✅ **No timeout issues** - Handles extractions taking 100+ seconds
- ✅ **Real-time progress** tracking for async tasks
- ✅ **Scalable** worker processes
- ✅ **Production-ready** with monitoring
- ✅ **Backward compatible** - sync endpoint still available
- ✅ **Containerized** deployment with Docker
- ✅ **Coolify ready** with comprehensive setup guide

## Architecture

```
[Client] → [Flask API] → [Redis] → [Celery Worker]
              ↓                        ↓
       [Returns task_id]        [Processes task]
              ↓                        ↓
       [Client polls status]    [Stores results]
```

## Request Format

```json
{
  "baseUrl": "https://example.com",
  "postType": "posts",
  "afterDate": "2024-01-01T00:00:00"
}
```

## Response Format

```json
{
  "success": true,
  "data": [
    {
      "id": 123,
      "date": "2024-01-15T10:30:00",
      "title": "Post Title",
      "content": "Post content..."
    }
  ],
  "error": null
}
```

For detailed deployment instructions, troubleshooting, and advanced configuration, please refer to the [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md).
