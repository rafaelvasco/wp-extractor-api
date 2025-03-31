#!/usr/bin/env python3
"""
Flask-based API for WordPress content extraction.

This module provides a REST API interface to the extraction functionality
defined in extractor.py, allowing clients to request WordPress content
extraction via HTTP requests.
"""

import requests
import re
from bs4 import BeautifulSoup

from flask import Flask, request, jsonify
from flask_cors import CORS


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


def fetch_wordpress_posts(base_url, post_type, per_page=100, page=1):
  """Fetch posts with WordPress API"""

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


def extract_all_posts(base_url, post_type):
  """Extracts all posts content from all pages"""

  all_posts_content = []
  page = 1

  while True:
    posts, total_pages = fetch_wordpress_posts(base_url, post_type, page=page)

    if not posts:
      break;

    for post in posts:
      post_data = {
        'id': post['id'],
        'date': post['date'],
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


@app.route('/extract', methods=['POST'])
def extract():
    """
    Extract WordPress content based on the specified post type.
    
    Expects a JSON payload with a 'postType' and a 'baseUrl'
    Returns a JSON response with extracted content or error message.
    
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
        
        # Extract posts
        posts = extract_all_posts(base_url=base_url, post_type=post_type)
        
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

if __name__ == '__main__':
    # Run the Flask application in debug mode when executed directly
    app.run(debug=True, host='0.0.0.0', port=5000)

