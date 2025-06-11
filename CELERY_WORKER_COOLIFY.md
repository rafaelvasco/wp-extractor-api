# Celery Worker Deployment in Coolify

## Important: Celery Workers Don't Need Ports

**Answer: Celery workers do NOT need any port configuration in Coolify.**

Celery workers are background processes that:

- Connect to Redis for receiving tasks
- Process tasks in the background
- Send results back to Redis
- Do NOT serve HTTP requests
- Do NOT need exposed ports

## Coolify Configuration for Celery Worker

### Step 3: Deploy Celery Worker

1. **Create another Application in Coolify**
2. **Source:** Same Git repository
3. **Build Pack:** Docker
4. **Port:** Leave empty or set to "none" (workers don't expose ports)
5. **Custom Start Command:** `celery -A celery_app worker --loglevel=info --concurrency=2`

### Environment Variables:

```
PYTHONUNBUFFERED=1
REDIS_URL=redis://wp-extractor-redis:6379/0
```

### Health Check:

Since Celery workers don't expose HTTP endpoints, you can either:

- Disable health checks in Coolify
- Or use a custom health check command: `celery -A celery_app inspect ping`

## Architecture Overview

```
[Client] → [Flask API:5000] → [Redis:6379] → [Celery Worker:no port]
                ↓                              ↓
         [Returns task_id]              [Processes task]
                ↓                              ↓
         [Client polls status]         [Stores result in Redis]
```

## Key Points:

1. **Flask API (Port 5000)** - Receives HTTP requests, returns task IDs
2. **Redis (Port 6379)** - Message broker, stores tasks and results
3. **Celery Worker (No port)** - Background processor, no HTTP interface
4. **Flower (Port 5555)** - Optional monitoring dashboard

## Verification

To verify your Celery worker is running correctly:

1. **Check worker logs** in Coolify dashboard
2. **Use Flower monitoring** (if deployed)
3. **Test async endpoint** and check if tasks are processed
4. **Redis CLI** to see if tasks are being consumed

The worker will show logs like:

```
[2024-01-01 12:00:00,000: INFO/MainProcess] Connected to redis://redis:6379/0
[2024-01-01 12:00:00,000: INFO/MainProcess] mingle: searching for neighbor nodes
[2024-01-01 12:00:00,000: INFO/MainProcess] mingle: all alone
[2024-01-01 12:00:00,000: INFO/MainProcess] celery@worker ready.
```
