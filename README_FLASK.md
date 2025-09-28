# TubeScript AI - Flask YouTube Transcript Generator

A powerful Flask web application for extracting YouTube video transcripts using advanced yt-dlp technology with AI-powered summarization.

## Features

- **Advanced Transcript Extraction**: Extract transcripts using yt-dlp with multiple fallback methods
- **AI-Powered Summarization**: Generate intelligent summaries using Google Gemini AI
- **Multi-Language Support**: Support for multiple languages and automatic captions
- **Real-time Processing**: AJAX-powered interface for seamless user experience
- **Export Options**: Download transcripts in TXT format
- **Responsive Design**: Beautiful, mobile-friendly interface using Tailwind CSS
- **Production Ready**: Optimized for both development and production environments

## Technology Stack

- **Backend**: Flask 3.0.0
- **Frontend**: HTML5, CSS3 (Tailwind CSS), JavaScript (ES6+)
- **Transcript Extraction**: yt-dlp (advanced YouTube downloader)
- **AI Integration**: Google Gemini API
- **HTTP Requests**: requests library
- **Deployment**: Lightweight and fast Flask server

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd tubescript-ai-flask
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   Create a `.env` file in the project root:
   ```env
   # Flask Settings
   FLASK_DEBUG=True
   SECRET_KEY=your-secret-key-here
   PORT=5000
   
   # Gemini AI API Key
   GEMINI_API_KEY=your-gemini-api-key
   
   # Production Settings
   PRODUCTION=false
   SERVER_ENVIRONMENT=development
   ```

5. **Run the Flask application**
   ```bash
   # Method 1: Direct Python
   python app.py
   
   # Method 2: Flask CLI
   flask --app app run --debug --port 5000
   ```

6. **Access the application**
   Open your browser and navigate to `http://127.0.0.1:5000`

## Usage

### Basic Usage

1. **Enter YouTube URL**: Paste any YouTube video URL in the input field
2. **Generate Transcript**: Click "Generate Transcript & Summarize" button
3. **View Results**: 
   - Watch the embedded video player
   - Read the extracted transcript with timestamps
   - Review the AI-generated summary
4. **Export Options**: Copy or download transcript in TXT format

### Advanced Features

- **Automatic Caption Detection**: Supports both manual and automatic captions
- **Multiple Language Priority**: Tries English variants (en, en-US, en-GB, etc.)
- **Fallback Mechanisms**: Multiple extraction methods for maximum compatibility
- **Error Handling**: Comprehensive error handling with user-friendly messages

## API Endpoints

### REST API

- `GET /` - Main application interface
- `POST /extract` - Extract transcript from YouTube URL
- `GET /health` - Health check endpoint

### Example API Usage

```python
import requests

# Extract transcript
response = requests.post('http://localhost:5000/extract', json={
    'youtube_url': 'https://www.youtube.com/watch?v=VIDEO_ID',
    'generate_summary': True
})

data = response.json()
if data['success']:
    print(f"Video Title: {data['video_title']}")
    print(f"Total Segments: {data['total_segments']}")
    print(f"Transcript: {data['transcript']}")
    print(f"Summary: {data['summary']}")
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Flask secret key | Required |
| `FLASK_DEBUG` | Debug mode | `True` |
| `PORT` | Server port | `5000` |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `PRODUCTION` | Production mode | `false` |
| `SERVER_ENVIRONMENT` | Environment type | `development` |

### Production Deployment

For production deployment:

1. **Set Environment Variables**:
   ```env
   PRODUCTION=true
   SERVER_ENVIRONMENT=production
   FLASK_DEBUG=False
   ```

2. **Use Production WSGI Server**:
   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

## Project Structure

```
tubescript-ai-flask/
├── app.py                 # Main Flask application
├── transcript_extractor.py # Advanced transcript extraction logic
├── requirements.txt       # Python dependencies
├── .env                  # Environment configuration
├── templates/
│   └── index.html        # Main web interface
├── cookies/              # YouTube cookies (optional)
└── venv/                 # Virtual environment
```

## Advanced Features

### yt-dlp Integration

The application uses yt-dlp for robust transcript extraction:

- **Multiple Format Support**: VTT, SRV3, SRV2, SRV1
- **Automatic Retries**: Built-in retry mechanisms
- **Cookie Support**: Optional cookie file support
- **User Agent Rotation**: Prevents blocking
- **Production Optimizations**: Enhanced settings for server environments

### AI Summarization

- **Structured Summaries**: Key topics, discussion points, and takeaways
- **Fallback Summaries**: Extractive summaries when AI is unavailable
- **Content Analysis**: Intelligent content processing

## Testing

Test the application:

```bash
# Test transcript extraction
python -c "
from transcript_extractor import extract_transcript
result, title = extract_transcript('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
print(f'Success: {result is not None}')
print(f'Title: {title}')
"

# Test Flask app
curl -X POST http://localhost:5000/extract \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "generate_summary": true}'
```

## Troubleshooting

### Common Issues

1. **No Transcript Found**: Video may not have captions available
2. **API Rate Limits**: YouTube may temporarily block requests
3. **Gemini API Errors**: Check API key and quota

### Solutions

- Use videos with confirmed captions
- Implement request delays for high-volume usage
- Set up proper error handling and user feedback

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **yt-dlp** for advanced YouTube content extraction
- **Google Gemini AI** for intelligent summarization
- **Tailwind CSS** for beautiful UI components
- **Flask** for the lightweight web framework

---

**TubeScript AI Flask** - Fast, reliable YouTube transcript extraction with AI-powered analysis.
