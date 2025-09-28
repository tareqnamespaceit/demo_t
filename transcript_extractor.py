import os
import re
import logging
import yt_dlp
import random
import urllib.request
import ssl
from typing import List, Dict, Tuple, Optional

# Import alternative transcript API
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    YOUTUBE_TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_API_AVAILABLE = False

# Configure logger to reduce noise
logger = logging.getLogger(__name__)
logger.setLevel(logging.WARNING)

# Suppress yt-dlp verbose output
class QuietLogger:
    def debug(self, msg): pass
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): logger.error(msg)

# Multiple proxy configurations
PROXY_LIST = [
    "http://pclffufy:0tmsp6ud1whi@142.111.48.253:7030/",
    "http://brd-customer-hl_adb32df2-zone-data_center:4jiibj3g0lmw@brd.superproxy.io:33335",
    # Add more proxies as needed
]

def get_random_proxy():
    """Get a random proxy from the list"""
    return random.choice(PROXY_LIST)

def test_proxy(proxy_url):
    """Test if a proxy is working"""
    try:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({'https': proxy_url, 'http': proxy_url})
        )
        opener.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')]

        response = opener.open('https://httpbin.org/ip', timeout=10)
        result = response.read().decode()
        logger.warning(f"Proxy {proxy_url[:30]}... is working")
        return True
    except Exception as e:
        logger.warning(f"Proxy {proxy_url[:30]}... failed: {e}")
        return False

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

def get_advanced_ydl_opts(use_proxy: bool = True, proxy_url: str = None, client_type: str = 'android') -> Dict:
    """
    Get advanced yt-dlp options for better YouTube compatibility

    Args:
        use_proxy: Whether to use proxy for requests
        proxy_url: Specific proxy URL to use
        client_type: Client type (android, web, tv, ios)

    Returns:
        Dictionary of yt-dlp options
    """
    # Get cookies file path
    cookies_file = os.path.join(os.path.dirname(__file__), 'cookies', 'youtube_cookies.txt')

    # Base options optimized for AWS Cloud9
    opts = {
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': ['en', 'en-US', 'en-GB', 'en-CA', 'en-AU'],
        'skip_download': True,
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'retries': 2,  # Reduced for faster fallback
        'fragment_retries': 2,
        'sleep_interval': 0.5,
        'max_sleep_interval': 3,
        'socket_timeout': 30,
        'http_chunk_size': 10485760,  # 10MB chunks for better performance
        'user_agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com/',
        'logger': QuietLogger(),
        'extractor_args': {
            'youtube': {
                'player_client': [client_type],
                'skip': ['dash', 'hls'],
                'innertube_host': 'youtubei.googleapis.com',
            }
        }
    }

    # Add cookies if available
    if os.path.exists(cookies_file):
        opts['cookiefile'] = cookies_file

    # Add proxy configuration if enabled
    if use_proxy and proxy_url:
        opts.update({
            'proxy': proxy_url,
            'geo_bypass': True,
            'geo_bypass_country': 'US',
            'sleep_interval': 1,  # Balanced for proxy
            'max_sleep_interval': 5,
            'retries': 3,
            'fragment_retries': 3,
            'socket_timeout': 45,
        })
        logger.warning(f"Using proxy: {proxy_url[:30]}... with {client_type} client")

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

def extract_transcript_youtube(url: str, use_proxy: bool = True) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Extract transcript from YouTube video using yt-dlp with multiple proxy support

    Args:
        url: YouTube video URL
        use_proxy: Whether to use proxy for requests

    Returns:
        Tuple of (transcript_segments, video_title)
    """
    try:
        logger.warning(f"Extracting transcript from: {url}")

        # Get video ID for validation
        video_id = get_youtube_video_id(url)
        if not video_id:
            logger.error("Could not extract video ID from URL")
            return None, None

        # Define multiple extraction strategies
        strategies = []

        # Prioritize direct connection for better compatibility
        # Add direct connection strategies first
        for client in ['web', 'android', 'ios', 'tv']:
            strategies.append((False, None, client))

        # Add proxy strategies if enabled (as fallback)
        if use_proxy:
            working_proxies = []
            # Test proxies first
            for proxy in PROXY_LIST:
                if test_proxy(proxy):
                    working_proxies.append(proxy)

            # Add proxy strategies with different clients
            for proxy in working_proxies[:1]:  # Use only 1 working proxy to save time
                for client in ['web', 'android']:  # Only most reliable clients
                    strategies.append((True, proxy, client))

        logger.warning(f"Trying {len(strategies)} different strategies...")

        for attempt, (proxy_enabled, proxy_url, client_type) in enumerate(strategies, 1):
            try:
                strategy_name = f"{'Proxy' if proxy_enabled else 'Direct'} + {client_type}"
                if proxy_enabled:
                    strategy_name += f" ({proxy_url[:20]}...)"

                logger.warning(f"Attempt {attempt}: {strategy_name}")

                # Get yt-dlp options
                ydl_opts = get_advanced_ydl_opts(proxy_enabled, proxy_url, client_type)

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        # Extract video info with timeout
                        info = ydl.extract_info(url, download=False)

                        if not info:
                            logger.error("Could not extract video information")
                            if attempt == len(strategies):  # If this was the last attempt
                                return None, None
                            continue  # Try next attempt

                        video_title = info.get('title', 'Unknown Title')
                        logger.warning(f"✅ Video found: {video_title}")

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
                                logger.warning(f"✅ Found manual subtitles in {lang}")
                                break

                        # If no manual subtitles, try automatic captions
                        if not transcript_data:
                            for lang in lang_priority:
                                if lang in automatic_captions:
                                    transcript_data = automatic_captions[lang]
                                    subtitle_source = f"auto_{lang}"
                                    logger.warning(f"✅ Found automatic captions in {lang}")
                                    break

                        if not transcript_data:
                            logger.warning("❌ No subtitles or captions found")
                            if attempt == len(strategies):  # If this was the last attempt
                                return None, video_title
                            continue  # Try next attempt

                        # Download subtitle content with proxy support
                        subtitle_content = None
                        for subtitle_format in transcript_data:
                            if subtitle_format.get('ext') in ['vtt', 'srv3', 'srv2', 'srv1']:
                                try:
                                    subtitle_url = subtitle_format.get('url')
                                    if subtitle_url:
                                        import requests

                                        # Use proxy for subtitle download if enabled
                                        proxies = None
                                        if proxy_enabled and proxy_url:
                                            proxies = {
                                                'http': proxy_url,
                                                'https': proxy_url
                                            }

                                        headers = {
                                            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                                            'Accept': 'text/vtt,application/x-subrip,text/plain,*/*',
                                            'Accept-Language': 'en-US,en;q=0.9',
                                            'Referer': 'https://www.youtube.com/'
                                        }

                                        response = requests.get(
                                            subtitle_url,
                                            timeout=20,
                                            proxies=proxies,
                                            headers=headers
                                        )
                                        if response.status_code == 200:
                                            subtitle_content = response.text
                                            logger.warning(f"✅ Downloaded subtitle content ({len(subtitle_content)} chars)")
                                            break
                                except Exception as e:
                                    logger.warning(f"❌ Failed to download subtitle format {subtitle_format.get('ext')}: {e}")
                                    continue

                        if not subtitle_content:
                            logger.error("❌ Could not download subtitle content")
                            if attempt == len(strategies):  # If this was the last attempt
                                return None, video_title
                            continue  # Try next attempt

                        # Parse subtitle content
                        transcript_segments = parse_subtitle_content(subtitle_content)

                        if transcript_segments:
                            logger.warning(f"🎉 SUCCESS! Extracted {len(transcript_segments)} transcript segments using {strategy_name}")
                            return transcript_segments, video_title
                        else:
                            logger.error("❌ Failed to parse subtitle content")
                            if attempt == len(strategies):  # If this was the last attempt
                                return None, video_title
                            continue  # Try next attempt

                    except Exception as e:
                        logger.error(f"❌ yt-dlp extraction failed (attempt {attempt}): {e}")
                        if attempt == len(strategies):  # If this was the last attempt
                            return None, None
                        continue  # Try next attempt

            except Exception as e:
                logger.error(f"❌ Configuration error (attempt {attempt}): {e}")
                if attempt == len(strategies):  # If this was the last attempt
                    return None, None
                continue  # Try next attempt

        # If we get here, all strategies failed
        logger.error(f"❌ All {len(strategies)} strategies failed")
        return None, None

    except Exception as e:
        logger.error(f"❌ Transcript extraction error: {e}")
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

def extract_transcript_alternative(url: str) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Alternative transcript extraction using youtube-transcript-api

    Args:
        url: YouTube video URL

    Returns:
        Tuple of (transcript_segments, video_title)
    """
    if not YOUTUBE_TRANSCRIPT_API_AVAILABLE:
        logger.error("youtube-transcript-api not available")
        return None, None

    try:
        # Get video ID
        video_id = get_youtube_video_id(url)
        if not video_id:
            logger.error("Could not extract video ID from URL")
            return None, None

        logger.warning(f"🔄 Trying alternative API for video: {video_id}")

        # Try to get transcript
        transcript_list = YouTubeTranscriptApi.list_transcripts(video_id).find_transcript(['en', 'en-US', 'en-GB']).fetch()

        if transcript_list:
            # Convert to our format
            transcript_segments = []
            for item in transcript_list:
                segment = {
                    'start': item.get('start', 0),
                    'duration': item.get('duration', 0),
                    'text': item.get('text', '').strip()
                }
                transcript_segments.append(segment)

            logger.warning(f"✅ Alternative API success! Extracted {len(transcript_segments)} segments")
            return transcript_segments, f"Video {video_id}"

        return None, None

    except Exception as e:
        logger.error(f"❌ Alternative API failed: {e}")
        return None, None

def extract_transcript(url: str, use_proxy: bool = True) -> Tuple[Optional[List[Dict]], Optional[str]]:
    """
    Main function to extract transcript from YouTube video with multiple fallback methods

    Args:
        url: YouTube video URL
        use_proxy: Whether to use proxy for requests

    Returns:
        Tuple of (transcript_segments, video_title)
    """
    try:
        logger.warning(f"Starting transcript extraction for: {url}")

        # Validate URL
        if not url or not any(domain in url for domain in ['youtube.com', 'youtu.be']):
            logger.error("Invalid YouTube URL")
            return None, None

        # Method 1: Try yt-dlp with proxy support
        logger.warning("🔄 Method 1: Advanced yt-dlp extraction")
        transcript_result, title = extract_transcript_youtube(url, use_proxy)

        if transcript_result and len(transcript_result) > 0:
            logger.warning(f"✅ yt-dlp success! Extracted {len(transcript_result)} segments")
            return transcript_result, title

        # Method 2: Try alternative API
        logger.warning("🔄 Method 2: Alternative transcript API")
        transcript_result, alt_title = extract_transcript_alternative(url)

        if transcript_result and len(transcript_result) > 0:
            logger.warning(f"✅ Alternative API success! Extracted {len(transcript_result)} segments")
            return transcript_result, alt_title or title

        logger.warning("❌ All methods failed - No transcript found")
        return None, title

    except Exception as e:
        logger.error(f"❌ Extract transcript error: {e}")
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
