# Gunicorn configuration file for production deployment

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes - auto-detect based on CPU cores in container
workers = int(os.environ.get("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = "sync"
worker_connections = 1000

# Extended timeouts for long-running requests (WordPress extraction can take 100+ seconds)
timeout = int(os.environ.get("GUNICORN_TIMEOUT", 300))  # 5 minutes default
keepalive = 5

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 500  # Reduced due to potentially memory-intensive operations
max_requests_jitter = 50

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.environ.get("LOG_LEVEL", "info")
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "wp_extractor_api"

# Server mechanics
daemon = False
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (handled by Coolify/Traefik reverse proxy)
# keyfile = None
# certfile = None

# Performance tuning
preload_app = True

# Extended graceful shutdown for long-running requests
graceful_timeout = int(os.environ.get("GUNICORN_GRACEFUL_TIMEOUT", 120))  # 2 minutes

# Worker memory management
worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance