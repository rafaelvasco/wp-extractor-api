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

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    # Remove special characters but keep Portuguese accents and common punctuation
    # Updated regex to include em dash (–) and other common punctuation, quotes, symbols
    # Include Unicode smart quotes and apostrophes: \u2018-\u201F
    text = re.sub(r'[^\w\s\u00C0-\u00FF\u2018-\u201F.,!?\-–—"\'&$€<>:]', '', text)

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

    # Remove special characters but keep Portuguese accents, line breaks, and common punctuation
    # Updated regex to include em dash (–) and other common punctuation, quotes, symbols
    # Include Unicode smart quotes and apostrophes: \u2018-\u201F
    text = re.sub(r'[^\w\s\u00C0-\u00FF\u2018-\u201F.,!?\n\-–—"\'&$€<>:]', '', text)

    return text.strip()