# Fixing Redis Connection Error in Coolify

## Error Analysis

```
Error -3 connecting to wp-extractor-redis:6379. Temporary failure in name resolution.
```

This means your Flask app can't find the Redis service by the hostname `wp-extractor-redis`.

## Solution Options

### Option 1: Use Coolify's Internal Network Names

In Coolify, services have specific internal hostnames. You need to find the correct Redis hostname.

1. **Go to your Redis service in Coolify**
2. **Check the "Internal Hostname" or "Service Name"**
3. **It might be something like:**
   - `redis-[random-id]`
   - `wp-extractor-redis-[random-id]`
   - Just `redis`

### Option 2: Use Redis Service URL from Coolify

1. **In your Redis service dashboard**
2. **Look for "Connection Details" or "Internal URL"**
3. **Copy the internal Redis URL**
4. **Update your Flask app's environment variable**

### Option 3: Create Redis as Database Service

If you created Redis as an application instead of a database service:

1. **Delete the current Redis application**
2. **Create a new "Database" resource in Coolify**
3. **Choose "Redis"**
4. **Note the connection details provided**

## Environment Variable Updates

Update your Flask app's environment variables in Coolify:

### If Redis hostname is different:

```
REDIS_URL=redis://[actual-redis-hostname]:6379/0
```

### Common Coolify Redis hostnames:

```
REDIS_URL=redis://redis:6379/0
REDIS_URL=redis://redis-service:6379/0
REDIS_URL=redis://wp-extractor-redis-[id]:6379/0
```

### If using Coolify's database service:

```
REDIS_URL=redis://[provided-hostname]:[provided-port]/0
```

## How to Find the Correct Redis Hostname

### Method 1: Check Redis Service Details

1. Go to your Redis service in Coolify
2. Look for "Internal Hostname" or "Network" section
3. Copy the exact hostname

### Method 2: Check Network Tab

1. In your Redis service, go to "Network" tab
2. Look for internal network name
3. Use that as the hostname

### Method 3: Use Coolify's Service Discovery

Some Coolify versions use:

- Service name as hostname
- Service name + random suffix
- Internal IP addresses

## Testing the Connection

### Method 1: Add Debug Endpoint

Add this to your Flask app temporarily:

```python
@app.route('/debug/redis', methods=['GET'])
def debug_redis():
    import os
    redis_url = os.environ.get('REDIS_URL', 'Not set')
    try:
        from redis import Redis
        r = Redis.from_url(redis_url)
        r.ping()
        return jsonify({"status": "success", "redis_url": redis_url})
    except Exception as e:
        return jsonify({"status": "error", "redis_url": redis_url, "error": str(e)})
```

### Method 2: Check from Container

1. Access your Flask app container shell in Coolify
2. Run: `ping redis` or `ping wp-extractor-redis`
3. Try: `nslookup redis` or `nslookup wp-extractor-redis`

## Quick Fix Steps

1. **Go to your Redis service in Coolify dashboard**
2. **Copy the exact internal hostname/URL**
3. **Update your Flask app's REDIS_URL environment variable**
4. **Redeploy your Flask app**
5. **Test the /extract/async endpoint again**

## Alternative: Use IP Address

If hostname resolution fails, you can use the internal IP:

1. **Find Redis container IP in Coolify**
2. **Use:** `REDIS_URL=redis://[ip-address]:6379/0`

## Verification

After fixing, test with:

```bash
curl -X POST https://your-domain.com/extract/async \
  -H "Content-Type: application/json" \
  -d '{"baseUrl": "https://example.com", "postType": "posts"}'
```

Should return a task_id instead of the Redis connection error.
