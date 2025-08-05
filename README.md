# Inovor UI - Image Generation & Chat API

A Flask-based web application that provides AI image generation and chat functionality.

## 🐛 Recent Bug Fixes & Improvements

### Fixed Issues:
1. **Fixed typo in `index.js`**: Changed "reloded" → "reloaded"
2. **Added missing `package.json`**: Proper Node.js dependency management
3. **Fixed `requirements.txt`**: Added version pinning and proper formatting
4. **Enhanced security**: Added input validation, CORS configuration, and security headers
5. **Improved error handling**: Better logging and error responses
6. **Added environment variable support**: Moved hardcoded tokens to environment configuration

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

### Node.js Monitor Service:
```bash
# Install dependencies
npm install

# Start the service
npm start
```

## 📁 Project Structure

- `img.py` - Main Flask application with image generation and chat APIs
- `index.js` - Node.js service for website monitoring
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies
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