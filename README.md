# TubeScript AI - YouTube Transcript Generator

একটি সম্পূর্ণ Django-based YouTube transcript generator এবং AI summarizer application যা আপনার দেওয়া HTML design অনুযায়ী তৈরি করা হয়েছে।

## 🚀 Features

- **YouTube Transcript Generation**: যেকোনো YouTube video থেকে automatic transcript বের করা
- **AI-Powered Summarization**: Transcript থেকে intelligent summary তৈরি করা
- **Multi-language Support**: 180+ ভাষায় transcript এবং translation
- **Download Options**: TXT, JSON, SRT format এ download
- **Copy to Clipboard**: Transcript এবং summary copy করার সুবিধা
- **Usage Tracking**: Free users এর জন্য daily limit tracking
- **Responsive Design**: Mobile-friendly interface
- **Real-time Processing**: AJAX-based dynamic loading

## 📁 Project Structure

```
tubescript_ai/
├── transcript_generator.py          # Standalone script
├── example_usage.py                 # Script usage examples
├── requirements.txt                 # Dependencies
├── manage.py                        # Django management
├── tubescript_ai/                   # Django project
│   ├── settings.py                  # Project settings
│   ├── urls.py                      # Main URL configuration
│   └── ...
├── transcript/                      # Django app
│   ├── models.py                    # Database models
│   ├── views.py                     # View logic
│   ├── forms.py                     # Form definitions
│   ├── urls.py                      # App URLs
│   └── ...
├── templates/                       # HTML templates
│   ├── base.html                    # Base template
│   └── transcript/
│       └── transcript_generator.html # Main page
└── static/                          # Static files
```

## 🛠️ Installation & Setup

### 1. Prerequisites
- Python 3.8+
- pip package manager

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Run Development Server
```bash
python manage.py runserver
```

Application will be available at: http://127.0.0.1:8000/

## 📖 Usage

### Standalone Script Usage

```bash
# Basic usage
python transcript_generator.py "https://www.youtube.com/watch?v=VIDEO_ID"

# With specific language
python transcript_generator.py "https://www.youtube.com/watch?v=VIDEO_ID" --language bn

# With translation
python transcript_generator.py "https://www.youtube.com/watch?v=VIDEO_ID" --translate hi

# Different output formats
python transcript_generator.py "https://www.youtube.com/watch?v=VIDEO_ID" --format srt

# List available transcripts
python transcript_generator.py "https://www.youtube.com/watch?v=VIDEO_ID" --list

# Custom output filename
python transcript_generator.py "https://www.youtube.com/watch?v=VIDEO_ID" --output my_transcript
```

### Web Application Usage

1. Open http://127.0.0.1:8000/ in your browser
2. Enter a YouTube video URL
3. Click "Generate Transcript & Summarize"
4. View transcript and AI summary
5. Use copy, download, and translation features

## 🔧 Configuration

### Environment Variables (Optional)
Create a `.env` file for production settings:

```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
```

### Database Configuration
Default: SQLite (for development)
For production, update `DATABASES` in `settings.py`

## 📊 Models

### VideoTranscript
- Stores video metadata and transcript data
- Tracks processing status
- Supports multiple languages

### TranscriptRequest
- Tracks user requests
- Logs IP addresses and user agents
- Records language preferences

### UserUsage
- Monitors usage limits
- Tracks daily/monthly requests
- Supports both authenticated and anonymous users

## 🎨 Frontend Features

### Design Elements
- Modern Tailwind CSS styling
- Responsive grid layout
- Interactive loading animations
- Smooth transitions and hover effects
- Professional color scheme

### JavaScript Functionality
- AJAX form submissions
- Dynamic content loading
- Copy to clipboard
- File downloads
- Language translation dropdowns
- Real-time notifications

## 🔒 Security Features

- CSRF protection
- Input validation
- Rate limiting
- IP-based usage tracking
- Secure file downloads

## 📱 Mobile Responsiveness

- Responsive grid system
- Mobile-optimized navigation
- Touch-friendly interface
- Adaptive font sizes
- Optimized for all screen sizes

## 🌐 Language Support

### Supported Languages (180+)
- Major world languages: English, Chinese, Hindi, Spanish, French, Arabic, etc.
- Regional languages: Bengali, Tamil, Telugu, Gujarati, Marathi, etc.
- European languages: German, Italian, Russian, Polish, etc.
- Asian languages: Japanese, Korean, Thai, Vietnamese, etc.
- African languages: Swahili, Amharic, etc.

## 🚀 Deployment

### Development
```bash
python manage.py runserver
```

### Production Deployment (Updated)

#### Quick Production Setup:
1. Upload code to your server
2. Run the automated deployment script:
```bash
python deploy_to_server.py
```

#### Manual Production Setup:
1. Set environment variable: `export DJANGO_ENV=production`
2. Configure proper database (PostgreSQL recommended)
3. Set up static file serving: `python manage.py collectstatic`
4. Use production WSGI server (Gunicorn, uWSGI)
5. Configure reverse proxy (Nginx)

#### Production Features:
- **Automatic Proxy Configuration**: Prevents IP blocking on production domains
- **Domain-based Detection**: Auto-detects youtubesummarypro.com and enables proxy
- **Fallback Mechanisms**: AJAX fallback to regular form submission
- **Comprehensive Testing**: Multiple test scripts for validation

#### Testing Production:
```bash
# Test proxy connection
python test_proxy_direct.py

# Test production server
python test_production_only.py

# Test both local and production
python test_local_and_server.py

# Debug production environment
python debug_server_environment.py
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch
3. Make changes
4. Test thoroughly
5. Submit pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:
- Check the documentation
- Review example usage
- Test with provided demo videos
- Ensure proper dependencies installation

## 🔄 Updates

### Version 1.0.0
- Initial release
- Complete YouTube transcript generation
- AI summarization
- Multi-language support
- Web interface matching provided design
- Standalone script functionality

---

**Made with ❤️ for content creators and developers**
