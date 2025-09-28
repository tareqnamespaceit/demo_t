import os
import re
import logging
import yt_dlp
from typing import List, Dict, Tuple, Optional

# Configure logger to reduce noise
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Suppress yt-dlp verbose output
class QuietLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): logger.error(msg)

def get_youtube_video_id(url: str) -> Optional[str]:
    """
    Extract YouTube video ID from various YouTube URL formats

    Args:
        url: YouTube URL

    Returns:
        Video ID string or None if not found
    """
    if not url:
        return None

    # YouTube video ID patterns
    patterns = [
        r'(?:v=|youtu\.be/|youtube\.com/shorts/)([0-9A-Za-z_-]{11})',
        r'youtube\.com/embed/([0-9A-Za-z_-]{11})',
        r'youtube\.com/v/([0-9A-Za-z_-]{11})',
        r'youtube\.com/watch\?.*v=([0-9A-Za-z_-]{11})'
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)

    return None

def get_advanced_ydl_opts() -> Dict:
    """
    Get advanced yt-dlp options for better YouTube compatibility

    Returns:
        Dictionary of yt-dlp options
    """
    # Get cookies file path
    cookies_file = os.path.join(os.path.dirname(__file__), 'cookies', 'youtube_cookies.txt')

    opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB'],
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'retries': 2,  # Reduced retries for speed
        'fragment_retries': 2,
        'sleep_interval': 0.5,  # Faster intervals
        'max_sleep_interval': 2,
        'socket_timeout': 30,  # Add timeout
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'logger': QuietLogger(),  # Use quiet logger
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web'],
                'skip': ['dash', 'hls']
            }
        }
    }

    # Add cookies if file exists
    if os.path.exists(cookies_file):
        opts['cookiefile'] = cookies_file
        logger.info(f"Using cookies file: {cookies_file}")

    # Production environment optimizations
    if os.getenv('PRODUCTION') == 'true' or os.getenv('SERVER_ENVIRONMENT') == 'production':
        opts.update({
            'sleep_interval': 1,  # Balanced for production
            'max_sleep_interval': 5,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 45,  # Longer timeout for production
        })
        logger.warning("Using production-optimized yt-dlp settings")

    return opts

def extract_transcript_youtube(url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Extract transcript from YouTube video using yt-dlp

    Args:
        url: YouTube video URL

    Returns:
        Tuple of (transcript_segments, video_title)
    """
    try:
        logger.info(f"Extracting transcript from: {url}")

        # Get video ID for validation
        video_id = get_youtube_video_id(url)
        if not video_id:
            logger.error("Could not extract video ID from URL")
            return None, None

        # Get yt-dlp options
        ydl_opts = get_advanced_ydl_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Extract video info
                info = ydl.extract_info(url, download=False)

                if not info:
                    logger.error("Could not extract video information")
                    return None, None

                video_title = info.get('title', 'Unknown Title')
                logger.info(f"Video title: {video_title}")

                # Look for subtitles
                subtitles = info.get('subtitles', {})
                automatic_captions = info.get('automatic_captions', {})

                # Try to get English subtitles first
                transcript_data = None
                subtitle_source = None

                # Priority order for subtitle languages
                lang_priority = ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU']

                # First try manual subtitles
                for lang in lang_priority:
                    if lang in subtitles:
                        transcript_data = subtitles[lang]
                        subtitle_source = f"manual_{lang}"
                        logger.info(f"Found manual subtitles in {lang}")
                        break

                # If no manual subtitles, try automatic captions
                if not transcript_data:
                    for lang in lang_priority:
                        if lang in automatic_captions:
                            transcript_data = automatic_captions[lang]
                            subtitle_source = f"auto_{lang}"
                            logger.info(f"Found automatic captions in {lang}")
                            break

                if not transcript_data:
                    logger.warning("No subtitles or captions found")
                    return None, video_title

                # Download subtitle content
                subtitle_content = None
                for subtitle_format in transcript_data:
                    if subtitle_format.get('ext') in ['vtt', 'srv3', 'srv2', 'srv1']:
                        try:
                            subtitle_url = subtitle_format.get('url')
                            if subtitle_url:
                                import requests
                                response = requests.get(subtitle_url, timeout=30)
                                if response.status_code == 200:
                                    subtitle_content = response.text
                                    logger.info(f"Downloaded subtitle content ({len(subtitle_content)} chars)")
                                    break
                        except Exception as e:
                            logger.warning(f"Failed to download subtitle format {subtitle_format.get('ext')}: {e}")
                            continue

                if not subtitle_content:
                    logger.error("Could not download subtitle content")
                    return None, video_title

                # Parse subtitle content
                transcript_segments = parse_subtitle_content(subtitle_content)

                if transcript_segments:
                    logger.info(f"Successfully extracted {len(transcript_segments)} transcript segments")
                    return transcript_segments, video_title
                else:
                    logger.error("Failed to parse subtitle content")
                    return None, video_title

            except Exception as e:
                logger.error(f"yt-dlp extraction failed: {e}")
                return None, None

    except Exception as e:
        logger.error(f"Transcript extraction error: {e}")
        return None, None

def parse_subtitle_content(content: str) -> List[Dict]:
    """
    Parse subtitle content (VTT or SRV format) into transcript segments

    Args:
        content: Raw subtitle content

    Returns:
        List of transcript segments with timestamp and text
    """
    segments = []

    try:
        if 'WEBVTT' in content or '-->' in content:
            # Parse VTT format
            segments = parse_vtt_content(content)
        elif '<text' in content and 'start=' in content:
            # Parse SRV/XML format
            segments = parse_srv_content(content)
        else:
            logger.warning("Unknown subtitle format")
            return []

        # Clean and validate segments
        cleaned_segments = []
        for segment in segments:
            if segment.get('text', '').strip():
                cleaned_segments.append(segment)

        return cleaned_segments

    except Exception as e:
        logger.error(f"Error parsing subtitle content: {e}")
        return []

def parse_vtt_content(content: str) -> List[Dict]:
    """Parse WebVTT subtitle content"""
    segments = []
    lines = content.split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Look for timestamp line
        if '-->' in line:
            try:
                # Parse timestamp
                time_parts = line.split(' --> ')
                start_time = time_parts[0].strip()
                end_time = time_parts[1].split()[0].strip()  # Remove any additional info

                # Get text content (next non-empty lines)
                text_lines = []
                i += 1
                while i < len(lines) and lines[i].strip():
                    text_line = lines[i].strip()
                    # Remove VTT formatting tags
                    text_line = re.sub(r'<[^>]+>', '', text_line)
                    if text_line:
                        text_lines.append(text_line)
                    i += 1

                if text_lines:
                    text = ' '.join(text_lines)
                    segments.append({
                        'timestamp': start_time,
                        'text': text
                    })

            except Exception as e:
                logger.warning(f"Error parsing VTT line: {line}, error: {e}")

        i += 1

    return segments

def parse_srv_content(content: str) -> List[Dict]:
    """Parse SRV/XML subtitle content"""
    segments = []

    try:
        import xml.etree.ElementTree as ET

        # Parse XML content
        root = ET.fromstring(content)

        # Find all text elements
        for text_elem in root.findall('.//text'):
            start_time = text_elem.get('start', '0')
            duration = text_elem.get('dur', '0')
            text_content = text_elem.text or ''

            # Convert start time to readable format
            try:
                start_seconds = float(start_time)
                timestamp = seconds_to_timestamp(start_seconds)

                if text_content.strip():
                    segments.append({
                        'timestamp': timestamp,
                        'text': text_content.strip()
                    })
            except ValueError:
                continue

    except Exception as e:
        logger.error(f"Error parsing SRV content: {e}")

    return segments

def seconds_to_timestamp(seconds: float) -> str:
    """Convert seconds to HH:MM:SS.mmm format"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

def extract_transcript(url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Main function to extract transcript from YouTube video

    Args:
        url: YouTube video URL

    Returns:
        Tuple of (transcript_segments, video_title)
    """
    try:
        logger.info(f"Starting transcript extraction for: {url}")

        # Validate URL
        if not url or not any(domain in url for domain in ['youtube.com', 'youtu.be']):
            logger.error("Invalid YouTube URL")
            return None, None

        # Extract using yt-dlp
        transcript_result, title = extract_transcript_youtube(url)

        if transcript_result and len(transcript_result) > 0:
            logger.info(f"Successfully extracted transcript with {len(transcript_result)} segments")
            return transcript_result, title
        else:
            logger.warning("No transcript found")
            return None, title

    except Exception as e:
        logger.error(f"Extract transcript error: {e}")
        return None, None

def format_as_paragraphs(text: str, max_length: int = 500) -> List[str]:
    """
    Format text into paragraphs of specified maximum length

    Args:
        text: Input text
        max_length: Maximum length per paragraph

    Returns:
        List of paragraph strings
    """
    if not text:
        return []

    paragraphs = []
    current_paragraph = ""

    sentences = text.split('. ')

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        # Add period back if it was removed by split
        if not sentence.endswith('.') and sentence != sentences[-1]:
            sentence += '.'

        # Check if adding this sentence would exceed max length
        if len(current_paragraph) + len(sentence) + 1 > max_length and current_paragraph:
            paragraphs.append(current_paragraph.strip())
            current_paragraph = sentence
        else:
            if current_paragraph:
                current_paragraph += ' ' + sentence
            else:
                current_paragraph = sentence

    # Add the last paragraph
    if current_paragraph:
        paragraphs.append(current_paragraph.strip())

    return paragraphs

def cleanup_files():
    """
    Clean up temporary files created during transcript extraction
    """
    try:
        # This function can be used to clean up any temporary files
        # Currently, we don't create temporary files, but this is here for compatibility
        logger.info("Cleanup completed")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
