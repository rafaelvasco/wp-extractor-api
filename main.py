#!/usr/bin/env python3
"""
Flask-based API for WordPress content extraction.

This module provides a REST API interface to the extraction functionality
with both synchronous and asynchronous endpoints for handling long-running requests.
"""

import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime

from flask import Flask, request, jsonify
from flask_cors import CORS
from celery_app import celery_app
from tasks import extract_wordpress_content


# Extraction Methods ===================================================================

def clean_html_content(html_content):
  """Remove HTML tags and clean the content"""

  # Create BS object
  soup = BeautifulSoup(html_content, 'html.parser')

  # Get text content
  text = soup.get_text(separator=' ', strip=True)

  # Remove extra whitespace
  text = re.sub(r'\s+', ' ', text)

  # Remove special characters but keep Portuguese accents
  text = re.sub(r'[^\w\s\u00C0-\u00FF.,!?-]', '', text)

  return text.strip()


def clean_html_content_with_linebreaks(html_content):
    """Remove HTML tags and clean the content while preserving line breaks."""
    # Replace <br> and </p> tags with newline characters before creating BeautifulSoup
    html_content = html_content.replace('<br>', '\n').replace('</p>', '\n')

    # Create BeautifulSoup object
    soup = BeautifulSoup(html_content, 'html.parser')

    # Get text content, using '\n' as separator for block elements
    text = ''
    for element in soup.descendants:
        if isinstance(element, str):
            text += element.strip() + ' '
        elif element.name in ['p', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li']:
            text += '\n'

    # Clean up the text
    # Remove extra whitespace within lines
    text = re.sub(r' +', ' ', text)

    # Remove extra blank lines (more than 2 consecutive newlines)
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)

    # Remove special characters but keep Portuguese accents and line breaks
    text = re.sub(r'[^\w\s\u00C0-\u00FF.,!?\n-]', '', text)

    return text.strip()


def fetch_wordpress_posts(base_url, post_type, per_page=100, page=1, after=None):
  """Fetch posts with WordPress API
  
  Args:
      base_url (str): Base URL of the WordPress site
      post_type (str): Type of post to fetch (e.g., 'posts', 'pages')
      per_page (int, optional): Number of posts per page. Defaults to 100.
      page (int, optional): Page number to fetch. Defaults to 1.
      after (str, optional): Fetch posts after this date. Format: YYYY-MM-DDT00:00:00 or ISO 8601 (e.g., 2025-04-26T21:32:52.043Z). Defaults to None.
  """

  # Construct the API URL
  api_url = f"{base_url}/wp-json/wp/v2/{post_type}"

  # Parameters for the request
  params = {
    'per_page': per_page,
    'page': page,
    'status': 'publish',
    'orderby': 'date',
    'order': 'desc',
  }
  
  # Add after parameter if provided
  if after:
    params['after'] = after  # Using YYYY-MM-DDT00:00:00 format

  try:

    # Make the request
    response = requests.get(api_url, params=params)
    response.raise_for_status() # Raise exception for bad status codes

    # Get total pages from headers
    total_pages = int(response.headers.get('X-WP-TotalPages', 1))

    return response.json(), total_pages

  except requests.exceptions.RequestException as e:
    print(f"Error fetching posts: {e}")
    return None, 0


def extract_all_posts(base_url, post_type, after_date=None):
  """Extracts all posts content from all pages
  
  Args:
      base_url (str): Base URL of the WordPress site
      post_type (str): Type of post to fetch (e.g., 'posts', 'pages')
      after_date (str, optional): Fetch posts after this date. Format: YYYY-MM-DDT00:00:00 or ISO 8601 (e.g., 2025-04-26T21:32:52.043Z). Defaults to None.
  """

  all_posts_content = []
  page = 1

  while True:
    posts, total_pages = fetch_wordpress_posts(base_url, post_type, page=page, after=after_date)

    if not posts:
      break;

    for post in posts:
      post_data = {
        'id': post['id'],
        'date': datetime.fromisoformat(post['date'].replace('Z', '+00:00')).strftime('%Y-%m-%dT%H:%M:%S'),
        'title': clean_html_content(post['title']['rendered']),
        'content': clean_html_content_with_linebreaks(post['content']['rendered'])
      }
      all_posts_content.append(post_data)

    print(f"Processed page {page} of {total_pages}")

    if page >= total_pages:
      break;

    page += 1

  return all_posts_content

# =======================================================================================


# API ===================================================================================

# Initialize Flask application
app = Flask(__name__)

# Configure Cross-Origin Resource Sharing
CORS(app, resources={r"/*": {"origins": "*"}})


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring and load balancers."""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "WordPress Extractor API"
    }), 200


@app.route('/extract', methods=['POST'])
def extract():
    """
    Extract WordPress content synchronously (for small requests).
    
    Expects a JSON payload with a 'postType' and a 'baseUrl'
    Returns a JSON response with extracted content or error message.
    
    Note: This endpoint has a timeout limit. For large extractions,
    use /extract/async instead.
    
    Returns:
        JSON: A response with the following structure:
            {
                "success": boolean,
                "data": [array of post objects] or null,
                "error": string or null
            }
    """
    try:
        # Get request data
        request_data = request.get_json()
               
        
        # Validate request data
        
        if not request_data:
            return jsonify({
                "success": False,
                "data": None,
                "error": "Request is Empty"
            })
        
        if 'postType' not in request_data:
            return jsonify({
                "success": False,
                "data": None,
                "error": "Missing 'postType' parameter"
            }), 400
            
        if 'baseUrl' not in request_data:
            return jsonify({
                "success": False,
                "data": None,
                "error": "Missing 'baseUrl' parameter"
            }), 400
        
        post_type = request_data['postType']
        base_url = request_data['baseUrl']
        after_date = None
        
        # Check if afterDate parameter is provided
        if 'afterDate' in request_data:
            try:
                # Parse the date to ensure it's valid
                after_date_str = request_data['afterDate']
                
                try:
                    # Handle various date formats
                    if 'T' in after_date_str:
                        # Handle ISO 8601 format with Z (UTC) timezone indicator and possibly milliseconds
                        if 'Z' in after_date_str:
                            # Remove the Z and convert to datetime
                            clean_date_str = after_date_str.replace('Z', '+00:00')
                            if '.' in clean_date_str:
                                # Format with milliseconds: 2025-04-26T21:32:52.043+00:00
                                date_obj = datetime.fromisoformat(clean_date_str)
                            else:
                                # Format without milliseconds: 2025-04-26T21:32:52+00:00
                                date_obj = datetime.fromisoformat(clean_date_str)
                        else:
                            try:
                                # Try standard format with seconds
                                date_obj = datetime.strptime(after_date_str, '%Y-%m-%dT%H:%M:%S')
                            except ValueError:
                                try:
                                    # Try without seconds
                                    date_obj = datetime.strptime(after_date_str, '%Y-%m-%dT%H:%M')
                                except ValueError:
                                    # Last attempt - try with milliseconds
                                    if '.' in after_date_str:
                                        date_parts = after_date_str.split('.')
                                        base_date = datetime.strptime(date_parts[0], '%Y-%m-%dT%H:%M:%S')
                                        date_obj = base_date
                                    else:
                                        # If all fails, raise to be caught by outer try-except
                                        raise ValueError("Invalid date format")
                    else:
                        # If only date is provided, add the time part
                        date_obj = datetime.strptime(after_date_str, '%Y-%m-%d')
                    
                    # Always format in YYYY-MM-DDT00:00:00 format for WordPress API
                    after_date = date_obj.strftime('%Y-%m-%dT00:00:00')
                except ValueError:
                    # If parsing fails, raise exception to be caught by outer try-except
                    raise ValueError("Invalid date format")
            except ValueError:
                return jsonify({
                    "success": False,
                    "data": None,
                    "error": "Invalid date format for 'afterDate'. Expected format: YYYY-MM-DD, YYYY-MM-DDT00:00:00, or ISO 8601 format like 2025-04-26T21:32:52.043Z"
                }), 400
        
        # Extract posts
        posts = extract_all_posts(base_url=base_url, post_type=post_type, after_date=after_date)
        
        # Return successful response
        return jsonify({
            "success": True,
            "data": posts,
            "error": None
        })
        
    except Exception as e:
        # Handle unexpected errors
        return jsonify({
            "success": False,
            "data": None,
            "error": str(e)
        }), 500


@app.route('/extract/async', methods=['POST'])
def extract_async():
    """
    Start asynchronous WordPress content extraction for long-running requests.
    
    Expects a JSON payload with a 'postType' and a 'baseUrl'
    Returns a task ID that can be used to check progress and get results.
    
    Returns:
        JSON: A response with the following structure:
            {
                "success": boolean,
                "task_id": string,
                "status": "started",
                "message": string,
                "check_url": string
            }
    """
    try:
        # Get request data
        request_data = request.get_json()
        
        # Validate request data
        if not request_data:
            return jsonify({
                "success": False,
                "error": "Request is Empty"
            }), 400
        
        if 'postType' not in request_data:
            return jsonify({
                "success": False,
                "error": "Missing 'postType' parameter"
            }), 400
            
        if 'baseUrl' not in request_data:
            return jsonify({
                "success": False,
                "error": "Missing 'baseUrl' parameter"
            }), 400
        
        post_type = request_data['postType']
        base_url = request_data['baseUrl']
        after_date = None
        
        # Handle afterDate parameter (same logic as sync endpoint)
        if 'afterDate' in request_data:
            try:
                after_date_str = request_data['afterDate']
                
                if 'T' in after_date_str:
                    if 'Z' in after_date_str:
                        clean_date_str = after_date_str.replace('Z', '+00:00')
                        date_obj = datetime.fromisoformat(clean_date_str)
                    else:
                        try:
                            date_obj = datetime.strptime(after_date_str, '%Y-%m-%dT%H:%M:%S')
                        except ValueError:
                            try:
                                date_obj = datetime.strptime(after_date_str, '%Y-%m-%dT%H:%M')
                            except ValueError:
                                if '.' in after_date_str:
                                    date_parts = after_date_str.split('.')
                                    date_obj = datetime.strptime(date_parts[0], '%Y-%m-%dT%H:%M:%S')
                                else:
                                    raise ValueError("Invalid date format")
                else:
                    date_obj = datetime.strptime(after_date_str, '%Y-%m-%d')
                
                after_date = date_obj.strftime('%Y-%m-%dT00:00:00')
            except ValueError:
                return jsonify({
                    "success": False,
                    "error": "Invalid date format for 'afterDate'. Expected format: YYYY-MM-DD, YYYY-MM-DDT00:00:00, or ISO 8601 format like 2025-04-26T21:32:52.043Z"
                }), 400
        
        # Start async task
        task = extract_wordpress_content.delay(base_url, post_type, after_date)
        
        # Return task information
        return jsonify({
            "success": True,
            "task_id": task.id,
            "status": "started",
            "message": "Extraction task started. Use the task_id to check progress.",
            "check_url": f"/extract/status/{task.id}"
        }), 202
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/extract/status/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Check the status of an asynchronous extraction task.
    
    Args:
        task_id (str): The task ID returned by /extract/async
    
    Returns:
        JSON: Task status and progress information
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                "success": True,
                "task_id": task_id,
                "state": task.state,
                "status": "Task is waiting to be processed"
            }
        elif task.state == 'PROGRESS':
            response = {
                "success": True,
                "task_id": task_id,
                "state": task.state,
                "current_page": task.info.get('current_page', 0),
                "total_pages": task.info.get('total_pages', 'unknown'),
                "processed_posts": task.info.get('processed_posts', 0),
                "status": task.info.get('status', 'Processing...')
            }
        elif task.state == 'SUCCESS':
            response = {
                "success": True,
                "task_id": task_id,
                "state": task.state,
                "result": task.result,
                "status": "Task completed successfully"
            }
        else:  # FAILURE
            response = {
                "success": False,
                "task_id": task_id,
                "state": task.state,
                "error": str(task.info),
                "status": "Task failed"
            }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


def create_app():
    """Application factory function for production deployment."""
    return app

if __name__ == '__main__':
    # Run the Flask application in debug mode when executed directly
    # This is only for development - use Gunicorn for production
    app.run(debug=True, host='0.0.0.0', port=5000)
