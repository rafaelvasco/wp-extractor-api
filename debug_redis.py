#!/usr/bin/env python3
"""
Debug script to test Redis connection.
Add this endpoint to your main.py file.
"""

# Add this route to your main.py file after the health check endpoint:

"""
@app.route('/debug/redis', methods=['GET'])
def debug_redis():
    \"\"\"Debug endpoint to test Redis connection.\"\"\"
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
"""

# Standalone test script
if __name__ == '__main__':
    import os
    from redis import Redis
    
    redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
    print(f"Testing Redis connection to: {redis_url}")
    
    try:
        r = Redis.from_url(redis_url)
        r.ping()
        print("✅ Redis connection successful!")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")