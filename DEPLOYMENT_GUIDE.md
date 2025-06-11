# WordPress Extractor API - Complete Deployment Guide

This comprehensive guide covers deploying the WordPress Extractor API with asynchronous task processing capabilities to handle long-running requests (100+ seconds) on Coolify.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [API Endpoints](#api-endpoints)
3. [Coolify Deployment](#coolify-deployment)
4. [Environment Variable Setup](#environment-variable-setup)
5. [Celery Worker Configuration](#celery-worker-configuration)
6. [Redis Connection Troubleshooting](#redis-connection-troubleshooting)
7. [Celery Troubleshooting](#celery-troubleshooting)
8. [Usage Examples](#usage-examples)
9. [Monitoring and Debug](#monitoring-and-debug)
10. [Performance Recommendations](#performance-recommendations)

---

## Architecture Overview

The application consists of multiple components:

1. **Flask Web API** - Handles HTTP requests and responses
2. **Redis** - Message broker and result backend for Celery
3. **Celery Worker** - Processes long-running extraction tasks
4. **Flower** (Optional) - Web-based monitoring for Celery tasks

### Architecture Flow:

```
[Client] → [Flask API:5000] → [Redis:6379] → [Celery Worker:no port]
                ↓                              ↓
         [Returns task_id]              [Processes task]
                ↓                              ↓
         [Client polls status]         [Stores result in Redis]
```

---

## API Endpoints

### Synchronous Endpoints

- `GET /health` - Health check
- `POST /extract` - Synchronous extraction (use for small requests only)

### Asynchronous Endpoints

- `POST /extract/async` - Start async extraction task
- `GET /extract/status/<task_id>` - Check task progress and get results

### Debug Endpoints

- `GET /debug/redis` - Test Redis connection
- `GET /debug/celery` - Check Celery worker status

---

## Coolify Deployment

### Prerequisites

- A running Coolify instance
- Git repository with your code
- Domain name (optional, but recommended)

### Step-by-Step Deployment

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

#### Step 3: Deploy Celery Worker

1. Create another **Application** in Coolify
2. **Source:** Same Git repository
3. **Build Pack:** Docker
4. **Port:** Leave empty (workers don't expose ports)

#### Step 4: Deploy Flower (Optional)

1. Create another **Application** in Coolify
2. **Source:** Same Git repository
3. **Build Pack:** Docker
4. **Port:** 5555
5. **Environment Variable:** `SERVICE_TYPE=flower`

---

## Environment Variable Setup

### Flask API Application (Main App)

**Environment Variables:**

```
FLASK_ENV=production
PYTHONUNBUFFERED=1
LOG_LEVEL=info
GUNICORN_WORKERS=4
GUNICORN_TIMEOUT=300
REDIS_URL=redis://[your-redis-hostname]:6379/0
```

**Note:** Do NOT set `SERVICE_TYPE` for the main API

### Celery Worker Application

**Environment Variables:**

```
SERVICE_TYPE=worker
PYTHONUNBUFFERED=1
REDIS_URL=redis://[your-redis-hostname]:6379/0
```

**Important:** Use the EXACT same `REDIS_URL` in both applications!

### Flower Monitoring (Optional)

**Environment Variables:**

```
SERVICE_TYPE=flower
PYTHONUNBUFFERED=1
REDIS_URL=redis://[your-redis-hostname]:6379/0
```

---

## Celery Worker Configuration

### Important: Celery Workers Don't Need Ports

**Celery workers do NOT need any port configuration in Coolify.**

Celery workers are background processes that:

- Connect to Redis for receiving tasks
- Process tasks in the background
- Send results back to Redis
- Do NOT serve HTTP requests
- Do NOT need exposed ports

### Coolify Configuration for Celery Worker

1. **Create Application in Coolify**
2. **Source:** Same Git repository
3. **Build Pack:** Docker
4. **Port:** Leave empty or set to "none"
5. **Environment Variables:** Set `SERVICE_TYPE=worker`

### Verification

To verify your Celery worker is running correctly, check the logs for:

**Correct Celery Worker Logs:**

```
[INFO/MainProcess] Connected to redis://redis:6379/0
[INFO/MainProcess] mingle: searching for neighbor nodes
[INFO/MainProcess] mingle: all alone
[INFO/MainProcess] celery@worker ready.
```

**Incorrect Logs (Gunicorn running instead):**

```
[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:5000
GET /health HTTP/1.1" 200
```

If you see Gunicorn logs, the `SERVICE_TYPE=worker` environment variable is not set correctly.

---

## Redis Connection Troubleshooting

### Error: "Temporary failure in name resolution"

```
Error -3 connecting to wp-extractor-redis:6379. Temporary failure in name resolution.
```

This means your Flask app can't find the Redis service by the hostname `wp-extractor-redis`.

### Solution Steps

#### 1. Find the Correct Redis Hostname

In Coolify, services have specific internal hostnames:

1. **Go to your Redis service in Coolify**
2. **Check the "Internal Hostname" or "Service Name"**
3. **It might be something like:**
   - `redis-[random-id]`
   - `wp-extractor-redis-[random-id]`
   - Just `redis`

#### 2. Update Environment Variables

Update your Flask app's environment variables in Coolify:

**Common Coolify Redis hostnames:**

```
REDIS_URL=redis://redis:6379/0
REDIS_URL=redis://redis-service:6379/0
REDIS_URL=redis://wp-extractor-redis-[id]:6379/0
```

#### 3. Alternative Solutions

**Option A: Use Coolify Database Service**

- Delete current Redis app
- Create new "Database" → "Redis"
- Use the provided connection details

**Option B: Check Redis service name**

- In Coolify, services often have auto-generated names
- Check the exact service name in your Redis dashboard

### Testing Redis Connection

Add this debug endpoint to test Redis connection:

```python
@app.route('/debug/redis', methods=['GET'])
def debug_redis():
    """Debug endpoint to test Redis connection."""
    import os
    redis_url = os.environ.get('REDIS_URL', 'Not set')
    try:
        from redis import Redis
        r = Redis.from_url(redis_url)
        r.ping()
        return jsonify({
            "status": "success",
            "redis_url": redis_url,
            "message": "Redis connection successful"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "redis_url": redis_url,
            "error": str(e),
            "message": "Redis connection failed"
        }), 500
```

---

## Celery Troubleshooting

### Problem: Tasks Stay in PENDING State

When `/extract/async` creates a task but it never progresses from PENDING to PROGRESS, it means:

1. **Celery worker is not running**
2. **Celery worker can't connect to Redis**
3. **Worker is running but not processing the queue**

### Diagnostic Steps

#### Step 1: Check if Celery Worker is Running

**In Coolify:**

1. Go to your Celery Worker application
2. Check the "Logs" tab
3. Look for these startup messages:
   ```
   [INFO/MainProcess] Connected to redis://...
   [INFO/MainProcess] mingle: searching for neighbor nodes
   [INFO/MainProcess] celery@worker ready.
   ```

**If you see errors like:**

- `Error -3 connecting to redis` → Redis connection issue
- `Connection refused` → Redis not accessible
- `No module named 'celery_app'` → Import issue

#### Step 2: Verify Celery Worker Configuration

**Check your Celery Worker app in Coolify:**

1. **Build Pack:** Docker ✓
2. **Port:** None/Empty ✓
3. **Environment Variables:**
   ```
   SERVICE_TYPE=worker
   PYTHONUNBUFFERED=1
   REDIS_URL=redis://[correct-redis-hostname]:6379/0
   ```

#### Step 3: Common Error Patterns

**Redis Connection Error:**

```
[ERROR/MainProcess] consumer: Cannot connect to redis://...
```

**Fix:** Update REDIS_URL environment variable

**Import Error:**

```
[ERROR/MainProcess] Received unregistered task of type 'tasks.extract_wordpress_content'
```

**Fix:** Check if tasks.py is in the same directory

**Wrong Service Type:**

```
[INFO] Starting gunicorn 21.2.0
```

**Fix:** Set `SERVICE_TYPE=worker` environment variable

### Quick Fixes

#### Fix 1: Restart Celery Worker

1. In Coolify, go to your Celery Worker app
2. Click "Restart" or "Redeploy"
3. Check logs for startup messages

#### Fix 2: Update Redis URL

1. Get the correct Redis hostname from your Redis service
2. Update REDIS_URL in both Flask app AND Celery worker
3. Redeploy both services

#### Fix 3: Verify Environment Variables

Ensure `SERVICE_TYPE=worker` is set in the Celery worker application.

---

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

---

## Monitoring and Debug

### Debug Endpoints

Add these endpoints to your Flask app for debugging:

#### Redis Connection Test

```python
@app.route('/debug/redis', methods=['GET'])
def debug_redis():
    """Debug endpoint to test Redis connection."""
    import os
    redis_url = os.environ.get('REDIS_URL', 'Not set')
    try:
        from redis import Redis
        r = Redis.from_url(redis_url)
        r.ping()
        return jsonify({
            "status": "success",
            "redis_url": redis_url,
            "message": "Redis connection successful"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "redis_url": redis_url,
            "error": str(e),
            "message": "Redis connection failed"
        }), 500
```

#### Celery Worker Status

```python
@app.route('/debug/celery', methods=['GET'])
def debug_celery():
    """Debug Celery worker status."""
    try:
        from celery_app import celery_app

        # Check if workers are active
        inspect = celery_app.control.inspect()
        active_workers = inspect.active()
        registered_tasks = inspect.registered()
        stats = inspect.stats()

        return jsonify({
            "status": "success",
            "broker_url": str(celery_app.conf.broker_url),
            "active_workers": active_workers or {},
            "registered_tasks": registered_tasks or {},
            "worker_stats": stats or {},
            "message": "Celery inspection successful"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": str(e),
            "message": "Celery inspection failed"
        }), 500
```

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

---

## Performance Recommendations

### Configuration

#### Timeout Settings

**Gunicorn (Web Server):**

- `GUNICORN_TIMEOUT=300` (5 minutes)
- `GUNICORN_GRACEFUL_TIMEOUT=120` (2 minutes)

**Celery (Background Tasks):**

- `task_time_limit=600` (10 minutes hard limit)
- `task_soft_time_limit=540` (9 minutes soft limit)

#### Scaling

**Horizontal Scaling:**

```bash
# Scale Celery workers in Coolify by deploying multiple worker applications
# Or use Docker Compose:
docker-compose up -d --scale celery-worker=5
```

**Vertical Scaling:**

```bash
# Increase worker concurrency
celery -A celery_app worker --concurrency=4

# Increase Gunicorn workers
GUNICORN_WORKERS=8
```

### Best Practices

1. **Use async endpoints** for any extraction that might take >30 seconds
2. **Monitor memory usage** - WordPress sites can have large content
3. **Set appropriate timeouts** based on your typical extraction sizes
4. **Scale workers** based on concurrent request volume
5. **Use Redis persistence** for production deployments

### Security Considerations

- **Redis Security:** Use password authentication in production
- **Rate Limiting:** Implement API rate limiting
- **Input Validation:** Validate WordPress URLs
- **Resource Limits:** Set memory/CPU limits for containers
- **Network Security:** Use private networks between services

### Production Checklist

- [ ] Redis deployed with persistence
- [ ] Celery workers running and healthy
- [ ] Flower monitoring accessible (optional)
- [ ] Health checks configured
- [ ] Logging centralized
- [ ] Backup strategy for Redis data
- [ ] Monitoring and alerting setup
- [ ] SSL certificates configured
- [ ] Resource limits set
- [ ] Auto-scaling configured

---

## Troubleshooting Quick Reference

### Common Issues and Solutions

| Issue                      | Symptoms                               | Solution                                             |
| -------------------------- | -------------------------------------- | ---------------------------------------------------- |
| Redis connection failed    | `Error -3 connecting to redis`         | Update REDIS_URL with correct hostname               |
| Tasks stay PENDING         | Async tasks never progress             | Check Celery worker logs, ensure SERVICE_TYPE=worker |
| Worker shows Gunicorn logs | Worker running Flask instead of Celery | Set SERVICE_TYPE=worker environment variable         |
| Import errors              | `No module named 'celery_app'`         | Check file structure and imports                     |
| Timeout errors             | Requests timeout after 30s             | Use async endpoints for large extractions            |

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

### Expected Working Flow

1. **POST /extract/async** → Creates task in Redis (PENDING)
2. **Celery worker** → Picks up task from Redis (PROGRESS)
3. **Task processing** → Updates progress in Redis
4. **GET /extract/status/<task_id>** → Shows progress updates
5. **Task completion** → Results stored in Redis (SUCCESS)

---

This guide should help you successfully deploy and troubleshoot your WordPress Extractor API with async capabilities on Coolify. The key is ensuring proper Redis connectivity and correct Celery worker configuration using environment variables.
