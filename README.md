# Inovor UI - Python Flask API

A Flask-based web application that provides AI image generation and chat functionality.

## 🐛 Recent Bug Fixes & Improvements

### Fixed Issues:
1. **Fixed `requirements.txt`**: Added version pinning and proper formatting
2. **Enhanced security**: Added input validation, CORS configuration, and security headers
3. **Improved error handling**: Better logging and error responses
4. **Added environment variable support**: Moved hardcoded tokens to environment configuration
5. **Added input validation**: XSS protection and content filtering

### Security Improvements:
- ✅ Input validation and sanitization for prompts and messages
- ✅ CORS configuration for secure cross-origin requests
- ✅ XSS protection through input filtering
- ✅ Proper error handling with logging
- ✅ Environment variable support for sensitive data

## 🚀 Setup Instructions

### Python Flask App:
```bash
# Install dependencies
pip install -r requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your actual API keys
# Then run the app
python img.py
```

## 📁 Project Structure

- `img.py` - Main Flask application with image generation and chat APIs
- `requirements.txt` - Python dependencies
- `.env.example` - Environment variables template
- `.gitignore` - Git ignore rules

## 🔧 API Endpoints

- `GET /` - Main web interface
- `POST /generate` - Generate AI images (Arting AI)
- `POST /generate_realistic` - Generate realistic images (Magic Studio)
- `POST /generate_realistic_batch` - Batch realistic image generation
- `POST /chat` - Chat with AI

## 🛡️ Security Notes

- Move API tokens from hardcoded values to environment variables
- Use HTTPS in production
- Consider implementing rate limiting for production use
- Review and update CORS origins for your domain