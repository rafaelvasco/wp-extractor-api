# WordPress Content Extractor API

Extracts all Posts of a type from a WordPress Website via REST API.

## Stack

- Flask
- BeautifulSoup
- Gunicorn (Production WSGI Server)

## Installation

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Development Mode

For development and testing:

```bash
python main.py
```

This runs the Flask development server on `http://localhost:5000`

### Production Mode

For production deployment, use Gunicorn WSGI server:

#### Option 1: Using the startup script

```bash
./start_production.sh
```

#### Option 2: Direct Gunicorn command

```bash
gunicorn --config gunicorn.conf.py main:app
```

#### Option 3: Custom Gunicorn configuration

```bash
gunicorn --bind 0.0.0.0:5000 --workers 4 main:app
```

### System Service (Linux)

To run as a system service:

1. Edit `wp-extractor-api.service` and update the paths:

   - `WorkingDirectory`: Path to your project directory
   - `Environment`: Path to your virtual environment
   - `ExecStart`: Path to gunicorn in your virtual environment

2. Copy the service file:

   ```bash
   sudo cp wp-extractor-api.service /etc/systemd/system/
   ```

3. Enable and start the service:

   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable wp-extractor-api
   sudo systemctl start wp-extractor-api
   ```

4. Check service status:
   ```bash
   sudo systemctl status wp-extractor-api
   ```

## API Endpoints

### POST /extract

Extracts WordPress content based on the specified post type.

**Request Body:**

```json
{
  "baseUrl": "https://example.com",
  "postType": "posts",
  "afterDate": "2024-01-01T00:00:00" // Optional
}
```

**Response:**

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

## Configuration

### Gunicorn Configuration

The `gunicorn.conf.py` file contains production-ready settings:

- 4 worker processes
- Timeout settings
- Logging configuration
- Performance optimizations

You can modify these settings based on your server resources and requirements.

## Deployment on Coolify

Coolify is a self-hosted platform that simplifies application deployment. Here's how to deploy this API on Coolify:

### Prerequisites

- A running Coolify instance
- Git repository with your code
- Domain name (optional, but recommended)

### Deployment Steps

1. **Push your code to a Git repository** (GitHub, GitLab, etc.)

2. **In Coolify Dashboard:**

   - Click "New Resource" → "Application"
   - Select your Git repository
   - Choose the branch to deploy
   - Set the application name (e.g., "wp-extractor-api")

3. **Configure Build Settings:**

   - Build Pack: Docker
   - Dockerfile: `Dockerfile` (default)
   - Port: `5000`

4. **Environment Variables (Optional):**

   - `FLASK_ENV=production`
   - `PYTHONUNBUFFERED=1`

5. **Domain Configuration:**

   - Add your domain in the "Domains" section
   - Coolify will automatically handle SSL certificates

6. **Deploy:**
   - Click "Deploy" to start the deployment
   - Monitor the build logs in real-time

### Coolify Features Used

- **Automatic SSL**: Coolify handles Let's Encrypt certificates
- **Health Checks**: Uses the `/health` endpoint for monitoring
- **Auto-deployment**: Redeploys on Git push (if configured)
- **Load Balancing**: Built-in Traefik reverse proxy

### Local Testing with Docker

Before deploying to Coolify, test locally:

```bash
# Build the Docker image
docker build -t wp-extractor-api .

# Run the container
docker run -p 5000:5000 wp-extractor-api

# Or use docker-compose
docker-compose up
```

### Troubleshooting Coolify Deployment

- Check build logs in Coolify dashboard
- Ensure port 5000 is correctly configured
- Verify the health check endpoint: `https://your-domain.com/health`
- Check application logs in Coolify for runtime issues

## Security Notes

- The development server (`python main.py`) should never be used in production
- Coolify provides automatic HTTPS via Let's Encrypt
- Consider implementing rate limiting for the API endpoints
- Use environment variables for sensitive configuration
- Regularly update dependencies for security patches
