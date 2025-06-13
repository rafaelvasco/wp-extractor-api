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
from html_utils import clean_html_content, clean_html_content_with_linebreaks


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