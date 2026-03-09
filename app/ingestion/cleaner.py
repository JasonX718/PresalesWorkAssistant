"""
Content cleaning and normalization utilities.

Handles cleaning of raw text from files and URLs before chunking.
"""

import re
import logging

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Clean and normalize text content.

    Steps:
    1. Remove excessive whitespace
    2. Normalize line endings
    3. Remove control characters
    4. Strip leading/trailing whitespace
    """
    if not text:
        return ""

    # Remove null bytes and control characters (keep newlines and tabs)
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)

    # Normalize line endings
    text = text.replace('\r\n', '\n').replace('\r', '\n')

    # Remove excessive blank lines (more than 2 consecutive)
    text = re.sub(r'\n{3,}', '\n\n', text)

    # Remove excessive spaces (more than 2 consecutive, not at line start)
    text = re.sub(r'[^\S\n]{3,}', '  ', text)

    # Strip each line
    lines = [line.rstrip() for line in text.split('\n')]
    text = '\n'.join(lines)

    return text.strip()


def clean_html_content(html: str) -> str:
    """
    Extract and clean main content from HTML.

    Uses trafilatura for main content extraction,
    falls back to BeautifulSoup if needed.
    """
    if not html:
        return ""

    # Try trafilatura first (best at extracting main content)
    try:
        import trafilatura
        result = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=True,
            no_fallback=False,
            favor_precision=False,
            favor_recall=True,
        )
        if result and len(result) > 100:
            return clean_text(result)
    except ImportError:
        logger.warning("trafilatura not installed, falling back to BeautifulSoup")
    except Exception as e:
        logger.warning(f"trafilatura extraction failed: {e}")

    # Fallback to BeautifulSoup
    try:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, 'html.parser')

        # Remove script, style, nav, footer, header elements
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header',
                                   'aside', 'iframe', 'noscript']):
            tag.decompose()

        # Get text content
        text = soup.get_text(separator='\n')
        return clean_text(text)
    except Exception as e:
        logger.error(f"HTML cleaning failed: {e}")
        return clean_text(html)


def clean_markdown(text: str) -> str:
    """Clean markdown content while preserving structure."""
    if not text:
        return ""

    # Remove HTML tags that might be in markdown
    text = re.sub(r'<[^>]+>', '', text)

    return clean_text(text)


def extract_title_from_html(html: str) -> str:
    """Extract title from HTML content."""
    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        # Try h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
    except Exception:
        pass

    # Regex fallback
    match = re.search(r'<title[^>]*>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()

    return ""
