# Coolify Deployment Guide

This guide will help you deploy the WordPress Extractor API on Coolify.

## Prerequisites

1. A running Coolify instance
2. Git repository with your code (GitHub, GitLab, Gitea, etc.)
3. Domain name (optional but recommended)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Ensure your repository contains these files:

- `Dockerfile` ✓
- `requirements.txt` ✓
- `main.py` ✓
- `gunicorn.conf.py` ✓
- `.dockerignore` ✓

### 2. Create Application in Coolify

1. **Login to Coolify Dashboard**
2. **Click "New Resource" → "Application"**
3. **Select Source:**
   - Choose your Git provider
   - Select the repository
   - Choose the branch (usually `main` or `master`)

### 3. Configure Application Settings

**Basic Settings:**

- **Name:** `wp-extractor-api`
- **Description:** `WordPress content extraction API`

**Build Settings:**

- **Build Pack:** Docker
- **Dockerfile:** `Dockerfile` (default)
- **Build Context:** `.` (root directory)

**Network Settings:**

- **Port:** `5000`
- **Health Check Path:** `/health`

### 4. Environment Variables (Optional)

Add these environment variables in Coolify:

```
FLASK_ENV=production
PYTHONUNBUFFERED=1
LOG_LEVEL=info
GUNICORN_WORKERS=4
```

### 5. Domain Configuration

1. **Go to "Domains" section**
2. **Add your domain:** `api.yourdomain.com`
3. **Enable SSL:** Coolify will automatically provision Let's Encrypt certificates

### 6. Deploy

1. **Click "Deploy"**
2. **Monitor build logs** in real-time
3. **Wait for deployment to complete**

## Post-Deployment

### Verify Deployment

1. **Health Check:** Visit `https://your-domain.com/health`

   - Should return: `{"status": "healthy", ...}`

2. **API Test:** Send a POST request to `https://your-domain.com/extract`
   ```bash
   curl -X POST https://your-domain.com/extract \
     -H "Content-Type: application/json" \
     -d '{
       "baseUrl": "https://example.com",
       "postType": "posts"
     }'
   ```

### Monitor Application

- **Logs:** Check application logs in Coolify dashboard
- **Metrics:** Monitor CPU, memory usage
- **Health:** Automatic health checks via `/health` endpoint

## Coolify Features

### Automatic Features

- **SSL Certificates:** Let's Encrypt integration
- **Load Balancing:** Traefik reverse proxy
- **Health Monitoring:** Automatic container restart on failure
- **Zero-Downtime Deployments:** Rolling updates

### Manual Features

- **Scaling:** Adjust container resources
- **Environment Variables:** Runtime configuration
- **Custom Domains:** Multiple domain support
- **Backup/Restore:** Application state management

## Troubleshooting

### Common Issues

1. **Build Fails:**

   - Check Dockerfile syntax
   - Verify all dependencies in requirements.txt
   - Check build logs for specific errors

2. **Health Check Fails:**

   - Ensure `/health` endpoint is accessible
   - Check if port 5000 is correctly exposed
   - Verify Gunicorn is starting properly

3. **Application Won't Start:**
   - Check environment variables
   - Review application logs
   - Verify Python dependencies

### Debug Commands

```bash
# Check container status
docker ps

# View container logs
docker logs <container_id>

# Execute into container
docker exec -it <container_id> /bin/bash

# Test health endpoint locally
curl http://localhost:5000/health
```

## Auto-Deployment

To enable automatic deployment on Git push:

1. **Go to "Git" section in Coolify**
2. **Enable "Auto Deploy"**
3. **Configure webhook** (if needed)

Now every push to your main branch will trigger a new deployment.

## Security Considerations

- **HTTPS:** Automatically handled by Coolify
- **Firewall:** Configure server firewall rules
- **Rate Limiting:** Consider implementing API rate limiting
- **Environment Variables:** Use for sensitive configuration
- **Updates:** Regularly update dependencies

## Support

- **Coolify Documentation:** https://coolify.io/docs
- **Community:** Discord/GitHub discussions
- **Logs:** Always check Coolify logs for deployment issues
