#!/usr/bin/env python3
"""
Flask YouTube Transcript Generator
Advanced transcript extraction using yt-dlp
"""

import os
import logging
from flask import Flask, render_template, request, jsonify
from transcript_extractor import extract_transcript
import google.generativeai as genai

# Configure logging to reduce noise
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress Google API warnings
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'
logging.getLogger('google').setLevel(logging.ERROR)
logging.getLogger('googleapiclient').setLevel(logging.ERROR)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Configure Gemini AI with optimization
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyAjKscGa6w2Z-hxF2de-KqDvnzz7qzxHj0')
_gemini_model = None

def get_gemini_model():
    """Get cached Gemini model instance"""
    global _gemini_model
    if _gemini_model is None and GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            _gemini_model = genai.GenerativeModel(
                'gemini-1.5-flash',  # Faster model
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1000,  # Limit output for speed
                    top_p=0.8,
                    top_k=40
                )
            )
        except Exception as e:
            logger.error(f"Failed to initialize Gemini model: {e}")
            _gemini_model = None
    return _gemini_model

def generate_ai_summary(transcript_text):
    """Generate AI summary using Gemini with optimization"""
    try:
        if not transcript_text or len(transcript_text.strip()) < 50:
            return generate_fallback_summary(transcript_text)

        model = get_gemini_model()
        if not model:
            return generate_fallback_summary(transcript_text)

        # Optimize prompt for speed
        prompt = f"""Summarize this YouTube transcript in 3 sections:

**Topics:** Main subjects discussed
**Points:** Key arguments and ideas
**Takeaways:** Important conclusions

Transcript: {transcript_text[:2000]}"""  # Reduced limit for speed

        response = model.generate_content(prompt)
        return response.text if response.text else generate_fallback_summary(transcript_text)

    except Exception as e:
        logger.error(f"Gemini AI error: {e}")
        return generate_fallback_summary(transcript_text)

def generate_fallback_summary(transcript_text):
    """Generate fast fallback summary without AI"""
    if not transcript_text or len(transcript_text.strip()) < 50:
        return "**Summary:** Transcript too short for meaningful summary."

    # Fast extractive summary
    sentences = transcript_text.split('. ')[:20]  # Limit processing
    meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if len(meaningful_sentences) <= 3:
        summary_sentences = meaningful_sentences
    else:
        # Take first, middle, and last sentences
        summary_sentences = [
            meaningful_sentences[0],
            meaningful_sentences[len(meaningful_sentences)//2],
            meaningful_sentences[-1]
        ]

    summary = '. '.join(summary_sentences)
    if summary and not summary.endswith('.'):
        summary += '.'

    return f"""**Topics:** Video content analysis
**Points:** {summary}
**Takeaways:** Review full transcript for detailed insights"""

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_transcript_route():
    """Extract transcript from YouTube URL with optimization"""
    try:
        data = request.get_json()
        youtube_url = data.get('youtube_url', '').strip()
        generate_summary = data.get('generate_summary', True)

        if not youtube_url:
            return jsonify({
                'success': False,
                'error': 'Please provide a YouTube URL'
            }), 400

        # Extract video ID early for faster processing
        video_id = None
        if 'youtube.com/watch?v=' in youtube_url:
            video_id = youtube_url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in youtube_url:
            video_id = youtube_url.split('youtu.be/')[1].split('?')[0]

        logger.warning(f"Processing video: {video_id}")

        # Determine if we should use proxy (always use for production-like requests)
        use_proxy = True  # Always use proxy to avoid bot detection

        # Extract transcript using advanced method with proxy
        transcript_segments, video_title = extract_transcript(youtube_url, use_proxy)

        if not transcript_segments:
            error_msg = 'Could not extract transcript from this video.'
            if video_title:
                error_msg += f' Video "{video_title}" may not have captions available or may be restricted.'
            else:
                error_msg += ' The video may not have captions available, be private, or be restricted in your region.'

            return jsonify({
                'success': False,
                'error': error_msg
            }), 400

        # Optimize transcript formatting
        formatted_transcript = []
        full_text_parts = []

        for segment in transcript_segments[:500]:  # Limit segments for performance
            timestamp = segment.get('timestamp', '00:00:00.000')
            text = segment.get('text', '').strip()

            if text:
                # Faster timestamp conversion
                try:
                    if ':' in timestamp:
                        time_parts = timestamp.split(':')
                        if len(time_parts) >= 2:
                            minutes = int(float(time_parts[-2]))
                            seconds = int(float(time_parts[-1]))
                            display_time = f"{minutes:02d}:{seconds:02d}"
                        else:
                            display_time = "00:00"
                    else:
                        display_time = "00:00"
                except:
                    display_time = "00:00"

                formatted_transcript.append({
                    'timestamp': display_time,
                    'text': text
                })
                full_text_parts.append(text)

        # Generate summary if requested (async-like processing)
        summary = ""
        if generate_summary and full_text_parts:
            full_text = " ".join(full_text_parts[:100])  # Limit text for speed
            summary = generate_ai_summary(full_text)

        return jsonify({
            'success': True,
            'video_id': video_id,
            'video_title': video_title or 'Unknown Title',
            'transcript': formatted_transcript,
            'summary': summary,
            'total_segments': len(formatted_transcript)
        })

    except Exception as e:
        logger.error(f"Error processing request: {e}")
        return jsonify({
            'success': False,
            'error': f'An error occurred while processing the video: {str(e)}'
        }), 500

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'YouTube Transcript Generator'})

if __name__ == '__main__':
    # Create necessary directories
    os.makedirs('cookies', exist_ok=True)
    
    # Run the app
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    
    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)
