#!/usr/bin/env python3
"""
HTML content cleaning utilities for WordPress content extraction.

This module provides centralized functions for cleaning and processing HTML content,
including proper handling of HTML entities and text formatting.
"""

import re
import html
from bs4 import BeautifulSoup


def clean_html_content(html_content):
    """Remove HTML tags and clean the content"""
    
    # First decode HTML entities (like &#8211; -> –)
    decoded_content = html.unescape(html_content)

    # Create BS object
    soup = BeautifulSoup(decoded_content, 'html.parser')

    # Get text content
    text = soup.get_text(separator=' ', strip=True)

    # Remove control characters and problematic Unicode characters first
    # Control characters (0x00-0x1F, 0x7F)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Remove invisible/problematic Unicode characters that can cause display issues
    # Zero-width spaces, joiners, marks, BOM, soft hyphens, etc.
    text = re.sub(r'[\u200b-\u200f\u2028\u2029\ufeff\u00ad]', '', text)

    # Remove extra whitespace (after removing invisible characters)
    text = re.sub(r'\s+', ' ', text)

    return text.strip()


def clean_html_content_with_linebreaks(html_content):
    """Remove HTML tags and clean the content while preserving line breaks."""
    
    # First decode HTML entities (like &#8211; -> –)
    decoded_content = html.unescape(html_content)
    
    # Replace <br> and </p> tags with newline characters before creating BeautifulSoup
    decoded_content = decoded_content.replace('<br>', '\n').replace('</p>', '\n')

    # Create BeautifulSoup object
    soup = BeautifulSoup(decoded_content, 'html.parser')

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

    # Remove control characters and problematic Unicode characters
    # Control characters (0x00-0x1F, 0x7F)
    text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
    
    # Remove invisible/problematic Unicode characters that can cause display issues
    # Zero-width spaces, joiners, marks, BOM, soft hyphens, etc.
    text = re.sub(r'[\u200b-\u200f\u2028\u2029\ufeff\u00ad]', '', text)

    return text.strip()