# Async WordPress Extractor API - Deployment Guide

This guide covers deploying the WordPress Extractor API with asynchronous task processing capabilities to handle long-running requests (100+ seconds).

## Architecture Overview

The application now consists of multiple components:

1. **Flask Web API** - Handles HTTP requests and responses
2. **Redis** - Message broker and result backend for Celery
3. **Celery Worker** - Processes long-running extraction tasks
4. **Flower** (Optional) - Web-based monitoring for Celery tasks

## API Endpoints

### Synchronous Endpoints

- `GET /health` - Health check
- `POST /extract` - Synchronous extraction (use for small requests only)

### Asynchronous Endpoints

- `POST /extract/async` - Start async extraction task
- `GET /extract/status/<task_id>` - Check task progress and get results

## Deployment Options

### Option 1: Coolify with Docker Compose

#### Step 1: Deploy Redis Service

1. In Coolify, create a new **Database** resource
2. Choose **Redis**
3. Set name: `wp-extractor-redis`
4. Deploy and note the connection details

#### Step 2: Deploy Main Application

1. Create new **Application** in Coolify
2. **Source:** Your Git repository
3. **Build Pack:** Docker
4. **Port:** 5000

**Environment Variables:**

```
FLASK_ENV=production
PYTHONUNBUFFERED=1
LOG_LEVEL=info
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=300
REDIS_URL=redis://wp-extractor-redis:6379/0
```

#### Step 3: Deploy Celery Worker

1. Create another **Application** in Coolify
2. **Source:** Same Git repository
3. **Build Pack:** Docker
4. **Custom Start Command:** `celery -A celery_app worker --loglevel=info --concurrency=2`

**Environment Variables:**

```
PYTHONUNBUFFERED=1
REDIS_URL=redis://wp-extractor-redis:6379/0
```

#### Step 4: Deploy Flower (Optional)

1. Create another **Application** in Coolify
2. **Source:** Same Git repository
3. **Build Pack:** Docker
4. **Port:** 5555
5. **Custom Start Command:** `celery -A celery_app flower --port=5555`

**Environment Variables:**

```
PYTHONUNBUFFERED=1
REDIS_URL=redis://wp-extractor-redis:6379/0
```

### Option 2: Docker Compose (Local/VPS)

Use the provided `docker-compose.yml`:

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f

# Scale workers if needed
docker-compose up -d --scale celery-worker=3
```

**Services included:**

- `wp-extractor-api` - Main Flask app (port 5000)
- `redis` - Redis server (port 6379)
- `celery-worker` - Background task processor
- `celery-flower` - Task monitoring (port 5555)

## Usage Examples

### Synchronous Request (Small datasets)

```bash
curl -X POST http://your-domain.com/extract \
  -H "Content-Type: application/json" \
  -d '{
    "baseUrl": "https://small-blog.com",
    "postType": "posts",
    "afterDate": "2024-01-01"
  }'
```

### Asynchronous Request (Large datasets)

```bash
# Start async task
curl -X POST http://your-domain.com/extract/async \
  -H "Content-Type: application/json" \
  -d '{
    "baseUrl": "https://large-site.com",
    "postType": "posts"
  }'

# Response:
{
  "success": true,
  "task_id": "abc123-def456-ghi789",
  "status": "started",
  "check_url": "/extract/status/abc123-def456-ghi789"
}

# Check progress
curl http://your-domain.com/extract/status/abc123-def456-ghi789

# Progress response:
{
  "success": true,
  "task_id": "abc123-def456-ghi789",
  "state": "PROGRESS",
  "current_page": 5,
  "total_pages": 20,
  "processed_posts": 150,
  "status": "Processing page 5 of 20..."
}

# Completed response:
{
  "success": true,
  "task_id": "abc123-def456-ghi789",
  "state": "SUCCESS",
  "result": {
    "status": "completed",
    "total_posts": 500,
    "total_pages": 20,
    "data": [/* array of posts */]
  }
}
```

## Configuration

### Timeout Settings

**Gunicorn (Web Server):**

- `GUNICORN_TIMEOUT=300` (5 minutes)
- `GUNICORN_GRACEFUL_TIMEOUT=120` (2 minutes)

**Celery (Background Tasks):**

- `task_time_limit=600` (10 minutes hard limit)
- `task_soft_time_limit=540` (9 minutes soft limit)

### Scaling

**Horizontal Scaling:**

```bash
# Scale Celery workers
docker-compose up -d --scale celery-worker=5

# Or in Coolify, deploy multiple worker applications
```

**Vertical Scaling:**

```bash
# Increase worker concurrency
celery -A celery_app worker --concurrency=4

# Increase Gunicorn workers
GUNICORN_WORKERS=8
```

## Monitoring

### Flower Dashboard

Access Flower at `http://your-domain.com:5555` to monitor:

- Active tasks
- Worker status
- Task history
- Performance metrics

### Health Checks

- **API Health:** `GET /health`
- **Redis Health:** `redis-cli ping`
- **Celery Health:** `celery -A celery_app inspect ping`

## Troubleshooting

### Common Issues

1. **Tasks stuck in PENDING:**

   - Check Redis connection
   - Verify Celery worker is running
   - Check worker logs

2. **Timeout errors:**

   - Increase `GUNICORN_TIMEOUT`
   - Use async endpoint for large requests
   - Check network connectivity to WordPress sites

3. **Memory issues:**
   - Reduce `worker_concurrency`
   - Increase `max_requests` restart frequency
   - Monitor with Flower

### Debug Commands

```bash
# Check Celery worker status
celery -A celery_app inspect active

# Check Redis connection
redis-cli -h redis ping

# View task details
celery -A celery_app inspect registered

# Purge all tasks
celery -A celery_app purge
```

## Performance Recommendations

1. **Use async endpoints** for any extraction that might take >30 seconds
2. **Monitor memory usage** - WordPress sites can have large content
3. **Set appropriate timeouts** based on your typical extraction sizes
4. **Scale workers** based on concurrent request volume
5. **Use Redis persistence** for production deployments

## Security Considerations

- **Redis Security:** Use password authentication in production
- **Rate Limiting:** Implement API rate limiting
- **Input Validation:** Validate WordPress URLs
- **Resource Limits:** Set memory/CPU limits for containers
- **Network Security:** Use private networks between services

## Production Checklist

- [ ] Redis deployed with persistence
- [ ] Celery workers running and healthy
- [ ] Flower monitoring accessible
- [ ] Health checks configured
- [ ] Logging centralized
- [ ] Backup strategy for Redis data
- [ ] Monitoring and alerting setup
- [ ] SSL certificates configured
- [ ] Resource limits set
- [ ] Auto-scaling configured
