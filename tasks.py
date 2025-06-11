#!/usr/bin/env python3
"""
Celery tasks for WordPress content extraction.
Handles long-running extraction operations asynchronously.
"""

import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime
from celery import current_task
from celery_app import celery_app


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
    
    # Add after parameter if provided
    if after:
        params['after'] = after
    
    try:
        # Make the request
        response = requests.get(api_url, params=params, timeout=30)
        response.raise_for_status()
        
        # Get total pages from headers
        total_pages = int(response.headers.get('X-WP-TotalPages', 1))
        
        return response.json(), total_pages
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching posts: {e}")
        return None, 0


@celery_app.task(bind=True, name='tasks.extract_wordpress_content')
def extract_wordpress_content(self, base_url, post_type, after_date=None):
    """
    Celery task to extract all WordPress posts content asynchronously.
    
    Args:
        base_url (str): Base URL of the WordPress site
        post_type (str): Type of post to fetch (e.g., 'posts', 'pages')
        after_date (str, optional): Fetch posts after this date
    
    Returns:
        dict: Task result with extracted posts or error information
    """
    try:
        all_posts_content = []
        page = 1
        total_pages = 1
        processed_posts = 0
        
        # Update task state
        self.update_state(
            state='PROGRESS',
            meta={
                'current_page': 0,
                'total_pages': 'unknown',
                'processed_posts': 0,
                'status': 'Starting extraction...'
            }
        )
        
        while page <= total_pages:
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={
                    'current_page': page,
                    'total_pages': total_pages,
                    'processed_posts': processed_posts,
                    'status': f'Processing page {page} of {total_pages}...'
                }
            )
            
            posts, total_pages = fetch_wordpress_posts(
                base_url, post_type, page=page, after=after_date
            )
            
            if not posts:
                break
            
            for post in posts:
                try:
                    post_data = {
                        'id': post['id'],
                        'date': datetime.fromisoformat(
                            post['date'].replace('Z', '+00:00')
                        ).strftime('%Y-%m-%dT%H:%M:%S'),
                        'title': clean_html_content(post['title']['rendered']),
                        'content': clean_html_content_with_linebreaks(
                            post['content']['rendered']
                        )
                    }
                    all_posts_content.append(post_data)
                    processed_posts += 1
                    
                    # Update progress every 10 posts
                    if processed_posts % 10 == 0:
                        self.update_state(
                            state='PROGRESS',
                            meta={
                                'current_page': page,
                                'total_pages': total_pages,
                                'processed_posts': processed_posts,
                                'status': f'Processed {processed_posts} posts...'
                            }
                        )
                
                except Exception as post_error:
                    print(f"Error processing post {post.get('id', 'unknown')}: {post_error}")
                    continue
            
            if page >= total_pages:
                break
            
            page += 1
        
        # Final success state
        return {
            'status': 'completed',
            'total_posts': len(all_posts_content),
            'total_pages': total_pages,
            'data': all_posts_content
        }
    
    except Exception as e:
        # Update task state with error
        self.update_state(
            state='FAILURE',
            meta={
                'error': str(e),
                'status': 'Task failed'
            }
        )
        raise e