"""
Subtitle Extractor Module

A Python module for extracting subtitles from video URLs using yt-dlp.
Supports any video platform that yt-dlp can handle.
"""

import logging
import re
import tempfile
import os
from typing import Optional
from urllib.parse import urlparse

try:
    import yt_dlp
except ImportError:
    raise ImportError("yt-dlp is required. Install with: pip install yt-dlp")


# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def extract_subtitles(url: str, language: str = 'en') -> str:
    """
    Extract subtitles from a video URL.

    Args:
        url (str): Video URL from any supported platform
        language (str): Language code (default: 'en'). If the requested language
                       is not available, the first available subtitle language will be used.

    Returns:
        str: Raw subtitle text or empty string on error

    Raises:
        ValueError: For invalid URLs
        ConnectionError: For network issues
    """
    if not _validate_url(url):
        logger.error(f"Invalid URL provided: {url}")
        return ""

    try:
        subtitle_content = _extract_subtitle_content(url, language)
        if subtitle_content:
            return _clean_subtitle_text(subtitle_content)
        else:
            logger.info(
                f"No subtitles found for URL: {url} in language: {language}")
            return ""

    except Exception as e:
        logger.error(f"Error extracting subtitles from {url}: {str(e)}")
        return ""


def _validate_url(url: str) -> bool:
    """
    Validate if the provided URL is properly formatted.

    Args:
        url (str): URL to validate

    Returns:
        bool: True if URL is valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def _get_ydl_options(language: str, temp_dir: str) -> dict:
    """
    Get yt-dlp configuration options for subtitle extraction.

    Args:
        language (str): Target language code
        temp_dir (str): Temporary directory path

    Returns:
        dict: yt-dlp configuration options
    """
    return {
        'writesubtitles': True,
        'writeautomaticsub': True,  # Fallback to auto-generated
        'subtitleslangs': [language, f"{language}-*"],  # Include variants
        'skip_download': True,  # Only extract metadata/subtitles
        'quiet': True,  # Suppress output
        'no_warnings': True,
        'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
        'subtitlesformat': 'vtt/srt/best',  # Prefer VTT or SRT
        'sleep_interval_requests': 0.05,
    }


def _resolve_subtitle_priority(subtitles: dict, automatic_captions: dict, language: str) -> Optional[str]:
    """
    Resolve subtitle content using priority fallback logic.

    Priority order:
    1. Manual subtitles in requested language
    2. Automatic captions in requested language
    3. Any available manual subtitle
    4. Any available automatic caption

    Args:
        subtitles (dict): Manual subtitles from yt-dlp
        automatic_captions (dict): Automatic captions from yt-dlp
        language (str): Requested language code

    Returns:
        Optional[str]: Subtitle content or None if not found
    """
    # Try manual subtitles first in requested language
    subtitle_content = _get_subtitle_from_info(subtitles, language)
    if subtitle_content:
        return subtitle_content

    # Fall back to automatic captions in requested language
    subtitle_content = _get_subtitle_from_info(automatic_captions, language)
    if subtitle_content:
        return subtitle_content

    # If no subtitles for the requested language, try any available manual subtitle
    if subtitles:
        first_lang = next(iter(subtitles.keys()))
        logger.info(f"Requested language '{language}' not found. Using first available manual subtitle: '{first_lang}'")
        subtitle_content = _get_subtitle_from_info(subtitles, first_lang)
        if subtitle_content:
            return subtitle_content

    # Finally, try any available automatic caption
    if automatic_captions:
        first_lang = next(iter(automatic_captions.keys()))
        logger.info(f"No manual subtitles found. Using first available automatic caption: '{first_lang}'")
        subtitle_content = _get_subtitle_from_info(automatic_captions, first_lang)
        if subtitle_content:
            return subtitle_content

    return None


def _extract_subtitle_content(url: str, language: str) -> Optional[str]:
    """
    Extract subtitle content using yt-dlp.

    Args:
        url (str): Video URL
        language (str): Language code

    Returns:
        Optional[str]: Subtitle content or None if not found
    """
    # Create temporary directory for subtitle files
    with tempfile.TemporaryDirectory() as temp_dir:
        ydl_opts = _get_ydl_options(language, temp_dir)

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video info
                info = ydl.extract_info(url, download=False)

                # Get subtitle dictionaries
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})

                # Resolve subtitle content using priority fallback
                return _resolve_subtitle_priority(subtitles, automatic_captions, language)

        except yt_dlp.DownloadError as e:
            logger.error(f"yt-dlp download error: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during extraction: {str(e)}")
            return None


def _get_subtitle_from_info(subtitle_dict: dict, language: str) -> Optional[str]:
    """
    Extract subtitle content from yt-dlp subtitle information.

    Args:
        subtitle_dict (dict): Subtitle dictionary from yt-dlp
        language (str): Target language code

    Returns:
        Optional[str]: Subtitle content or None
    """
    # Try exact language match first
    if language in subtitle_dict:
        return _download_subtitle_content(subtitle_dict[language])

    # Try language variants (e.g., en-US, en-GB for 'en')
    for lang_code in subtitle_dict.keys():
        if lang_code.startswith(f"{language}-"):
            return _download_subtitle_content(subtitle_dict[lang_code])

    # If no match found and subtitles are available, use the first available language
    if subtitle_dict:
        first_lang = next(iter(subtitle_dict.keys()))
        logger.info(
            f"Requested language '{language}' not found. Using first available language: '{first_lang}'")
        return _download_subtitle_content(subtitle_dict[first_lang])

    return None


def _download_subtitle_content(subtitle_formats: list) -> Optional[str]:
    """
    Download subtitle content from available formats.

    Args:
        subtitle_formats (list): List of subtitle format dictionaries

    Returns:
        Optional[str]: Downloaded subtitle content or None
    """
    import urllib.request

    for format_info in subtitle_formats:
        try:
            url = format_info.get('url')
            if url:
                with urllib.request.urlopen(url) as response:
                    content = response.read().decode('utf-8')
                    return content
        except Exception as e:
            logger.warning(f"Failed to download subtitle format: {str(e)}")
            continue

    return None


def _clean_subtitle_text(subtitle_content: str) -> str:
    """
    Clean subtitle content by removing timestamps and formatting.

    Args:
        subtitle_content (str): Raw subtitle content

    Returns:
        str: Cleaned subtitle text
    """
    if not subtitle_content:
        return ""

    # Check if content is JSON format (some YouTube subtitles)
    if subtitle_content.strip().startswith('{') or '"events"' in subtitle_content:
        try:
            import json
            data = json.loads(subtitle_content)
            # Extract text from YouTube's JSON subtitle format
            if 'events' in data:
                text_parts = []
                for event in data['events']:
                    if 'segs' in event:
                        for seg in event['segs']:
                            if 'utf8' in seg:
                                text_parts.append(seg['utf8'])

                # Join all text parts and apply thorough cleaning
                raw_text = ' '.join(text_parts)

                # Apply the same cleaning logic as below for consistency
                # Remove HTML tags and VTT styling
                raw_text = re.sub(r'<[^>]+>', '', raw_text)
                raw_text = re.sub(r'{[^}]+}', '', raw_text)

                # Clean up whitespace and remove all newlines
                lines = []
                for line in raw_text.split('\n'):
                    line = line.strip()
                    # Skip empty lines and lines with only special characters
                    if line and not line.isspace() and not re.match(r'^[\s\[\]{},"\':]+$', line):
                        lines.append(line)

                # Join lines with single spaces and normalize all whitespace
                text = ' '.join(lines)

                # Remove all remaining newlines and normalize whitespace
                # Replace newlines with spaces
                text = re.sub(r'[\r\n]+', ' ', text)
                # Multiple spaces/tabs to single space
                text = re.sub(r'\s+', ' ', text)

                # Normalize punctuation spacing (remove space before, add space after if needed)
                # Remove space before punctuation
                text = re.sub(r'\s+([.!?])', r'\1', text)
                # Add space after punctuation if missing
                text = re.sub(r'([.!?])([^\s])', r'\1 \2', text)
                # Remove space before comma
                text = re.sub(r'\s+([,])', r'\1', text)
                # Add space after comma if missing
                text = re.sub(r'([,])([^\s])', r'\1 \2', text)

                # Clean up any trailing spaces before end of text and double spaces that might remain
                # Final cleanup of multiple spaces
                text = re.sub(r'\s+', ' ', text)

                return text.strip()
        except (json.JSONDecodeError, KeyError):
            # If JSON parsing fails, continue with regular cleaning
            pass

    # Remove VTT headers and metadata
    content = re.sub(r'^WEBVTT.*?\n\n', '', subtitle_content,
                     flags=re.MULTILINE | re.DOTALL)

    # Remove SRT timestamps (e.g., "00:01:23,456 --> 00:01:26,789")
    content = re.sub(
        r'\d{2}:\d{2}:\d{2}[,\.]\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}', '', content)

    # Remove VTT timestamps (e.g., "00:01:23.456 --> 00:01:26.789")
    content = re.sub(
        r'\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}', '', content)

    # Remove subtitle sequence numbers
    content = re.sub(r'^\d+\s*$', '', content, flags=re.MULTILINE)

    # Remove HTML tags and VTT styling
    content = re.sub(r'<[^>]+>', '', content)
    content = re.sub(r'{[^}]+}', '', content)

    # Remove positioning and styling cues
    content = re.sub(r'position:\d+%', '', content)
    content = re.sub(r'align:[a-zA-Z]+', '', content)
    content = re.sub(r'size:\d+%', '', content)

    # Remove JSON-like artifacts that might remain
    content = re.sub(r'[\[\]{},"\']', '', content)
    content = re.sub(r'wsWinStyles|wpWinPositions|events', '', content)

    # Clean up whitespace and remove all newlines
    lines = []
    for line in content.split('\n'):
        line = line.strip()
        # Skip empty lines and lines with only special characters
        if line and not line.isspace() and not re.match(r'^[\s\[\]{},"\':]+$', line):
            lines.append(line)

    # Join lines with single spaces and normalize all whitespace
    text = ' '.join(lines)

    # Remove all remaining newlines and normalize whitespace
    text = re.sub(r'[\r\n]+', ' ', text)  # Replace newlines with spaces
    text = re.sub(r'\s+', ' ', text)  # Multiple spaces/tabs to single space

    # Normalize punctuation spacing (remove space before, add space after if needed)
    # Remove space before punctuation
    text = re.sub(r'\s+([.!?])', r'\1', text)
    # Add space after punctuation if missing
    text = re.sub(r'([.!?])([^\s])', r'\1 \2', text)
    text = re.sub(r'\s+([,])', r'\1', text)  # Remove space before comma
    # Add space after comma if missing
    text = re.sub(r'([,])([^\s])', r'\1 \2', text)

    # Clean up any trailing spaces before end of text and double spaces that might remain
    text = re.sub(r'\s+', ' ', text)  # Final cleanup of multiple spaces

    return text.strip()


if __name__ == "__main__":
    # Example usage
    print("Subtitle Extractor Module")
    print("Use the extract_subtitles() function to extract subtitles from video URLs.")
    print("Run tests with: uv run pytest")
