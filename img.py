from flask import Flask, render_template_string, request, jsonify, Response
import requests
import random
import string
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import base64
import re
from io import BytesIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import queue
import uuid

app = Flask(__name__)

# Rate limiting
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# Helper functions for API
def generate_user_agent():
    return 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36'

def generate_random_account():
    name = ''.join(random.choices(string.ascii_lowercase, k=20))
    number = ''.join(random.choices(string.digits, k=4))
    return f"{name}{number}@yahoo.com"

def generate_username():
    name = ''.join(random.choices(string.ascii_lowercase, k=20))
    number = ''.join(random.choices(string.digits, k=20))
    return f"{name}{number}"

def generate_random_code(length=32):
    letters_and_digits = string.ascii_letters + string.digits
    return ''.join(random.choice(letters_and_digits) for _ in range(length))

# Fixed Ultra Gen function
def generate_ultra_image(prompt):
    try:
        # ===== 1. Generate Image via Fal Image Generator =====
        headers = {
            'authority': 'fal-image-generator.vercel.app',
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://fal-image-generator.vercel.app',
            'pragma': 'no-cache',
            'referer': 'https://fal-image-generator.vercel.app/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
        }

        json_data = {
            'prompt': prompt,
            'provider': 'fal',
            'modelId': 'fal-ai/flux-pro/v1.1-ultra',
        }

        response = requests.post(
            'https://fal-image-generator.vercel.app/api/generate-images',
            headers=headers,
            json=json_data,
            timeout=30
        )

        if response.status_code != 200:
            raise ValueError(f"Fal generation failed: {response.text}")

        # Extract base64 image data
        raw_text = response.text
        match = re.search(r'([A-Za-z0-9+/=]{100,})', raw_text)
        if not match:
            raise ValueError("No base64 data found in Fal response")

        base64_data = match.group(1) + "=" * (-len(match.group(1)) % 4)
        image_bytes = base64.b64decode(base64_data)

        # ===== 2. Upload to tmpfiles.org =====
        upload_response = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": ("generated.png", image_bytes)}
        )

        if upload_response.status_code == 200:
            data = upload_response.json()
            if data.get("data", {}).get("url"):
                return data["data"]["url"].replace("tmpfiles.org/", "tmpfiles.org/dl/")

        raise ValueError(f"Upload failed: {upload_response.text}")

    except Exception as e:
        print(f"[ERROR] Ultra generation error: {e}")
        return None

# Function to generate a single realistic image
def generate_single_realistic_image(prompt):
    try:
        gen_url = "https://ai-api.magicstudio.com/api/ai-art-generator"
        
        gen_headers = {
            'origin': 'https://magicstudio.com',
            'referer': 'https://magicstudio.com/ai-art-generator/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36',
            'accept': 'application/json, text/plain, */*',
        }

        api_data = {
            'prompt': prompt,
            'output_format': 'bytes',
            'anonymous_user_id': '8279e727-5f1a-45ee-ab41-5f1bbdd29e06',
            'request_timestamp': str(time.time()),
            'user_is_subscribed': 'false',
            'client_id': 'pSgX7WgjukXCBoYwDM8G8GLnRRkvAoJlqa5eAVvj95o'
        }

        response = requests.post(gen_url, headers=gen_headers, data=api_data, timeout=30)
        
        if response.status_code != 200:
            return None

        upload_url = "https://0x0.st"
        upload_headers = {
            'User-Agent': 'curl/7.64.1'
        }
        files = {
            'file': ("image.png", response.content)
        }

        upload = requests.post(upload_url, files=files, headers=upload_headers, timeout=30)
        
        if upload.status_code == 200:
            return upload.text.strip()
        else:
            return None

    except Exception as e:
        print(f"Error generating single image: {str(e)}")
        return None

# Function to generate a single video
def generate_single_video(prompt):
    try:
        api_base = "https://api.yabes-desu.workers.dev/ai/tool/txt2video"
        params = {"prompt": prompt}

        response = requests.get(api_base, params=params, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("success") and "url" in data:
            return data["url"]
        else:
            return None

    except Exception as e:
        print(f"Error generating single video: {str(e)}")
        return None

# HTML Template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Hub - Ultra Fast Generation</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        body {
            background: #0a0a0a;
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 30px;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4, #a8e6cf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
            animation: gradientShift 3s ease-in-out infinite alternate;
        }
        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
        }
        .tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            gap: 10px;
            flex-wrap: wrap;
        }
        .tab {
            background: #1a1a1a;
            border: 1px solid #333;
            padding: 12px 25px;
            border-radius: 25px;
            color: #fff;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .tab.active {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            border-color: transparent;
        }
        .generator-section {
            display: none;
            max-width: 800px;
            margin: 0 auto;
            text-align: center;
        }
        .generator-section.active {
            display: block;
        }
        .section-title {
            font-size: 1.8rem;
            margin-bottom: 20px;
            color: #4ecdc4;
        }
        .input-group {
            margin-bottom: 20px;
        }
        textarea {
            width: 100%;
            height: 100px;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 15px;
            color: #fff;
            font-size: 1rem;
            resize: none;
            margin-bottom: 15px;
            outline: none;
            transition: border-color 0.3s;
        }
        textarea:focus {
            border-color: #4ecdc4;
            box-shadow: 0 0 10px rgba(78, 205, 196, 0.3);
        }
        .number-input {
            width: 200px;
            background: #1a1a1a;
            border: 1px solid #333;
            border-radius: 10px;
            padding: 12px 15px;
            color: #fff;
            font-size: 1rem;
            outline: none;
            margin-bottom: 15px;
            transition: border-color 0.3s;
        }
        .btn {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            border: none;
            padding: 12px 30px;
            border-radius: 25px;
            color: #fff;
            font-size: 1rem;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
            margin: 10px;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(78, 205, 196, 0.4);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        .ultra-btn {
            background: linear-gradient(45deg, #ff4757, #ff3838);
        }
        .realistic-btn {
            background: linear-gradient(45deg, #e74c3c, #f39c12);
        }
        .video-btn {
            background: linear-gradient(45deg, #8e44ad, #3498db);
        }
        .loader {
            display: none;
            border: 5px solid #1a1a1a;
            border-top: 5px solid #4ecdc4;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .progress {
            margin: 20px 0;
            color: #4ecdc4;
            font-size: 1.1rem;
            display: none;
        }
        .result {
            margin-top: 20px;
            display: none;
        }
        .image-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .video-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        .image-item, .video-item {
            position: relative;
            background: #1a1a1a;
            border-radius: 10px;
            padding: 10px;
            box-shadow: 0 0 20px rgba(78, 205, 196, 0.1);
        }
        .generated-image {
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(78, 205, 196, 0.2);
            margin-bottom: 10px;
        }
        .generated-video {
            width: 100%;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(142, 68, 173, 0.2);
            margin-bottom: 10px;
            background: #000;
        }
        .download-btn {
            background: linear-gradient(45deg, #4ecdc4, #45b7b8);
            padding: 8px 20px;
            font-size: 0.9rem;
            margin: 5px;
        }
        .download-video-btn {
            background: linear-gradient(45deg, #8e44ad, #3498db);
            padding: 8px 20px;
            font-size: 0.9rem;
            margin: 5px;
        }
        .download-all-btn {
            background: linear-gradient(45deg, #6c5ce7, #a29bfe);
            padding: 12px 30px;
            margin: 10px;
        }
        .unlimited-badge {
            background: linear-gradient(45deg, #e74c3c, #f39c12);
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.75rem;
            margin-left: 8px;
            display: inline-block;
        }
        .warning-badge {
            background: linear-gradient(45deg, #ff4757, #ff3838);
            padding: 5px 12px;
            border-radius: 15px;
            font-size: 0.75rem;
            margin-left: 8px;
            display: inline-block;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.7; }
            100% { opacity: 1; }
        }
        footer {
            margin-top: 30px;
            font-size: 0.9rem;
            color: #666;
            text-align: center;
        }
        @media (max-width: 600px) {
            h1 {
                font-size: 2rem;
            }
            .tabs {
                flex-direction: column;
                align-items: center;
            }
            .tab {
                width: 200px;
                text-align: center;
            }
            textarea {
                height: 80px;
            }
            .btn {
                padding: 10px 20px;
                font-size: 0.9rem;
            }
            .number-input {
                width: 150px;
            }
            .image-container, .video-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <h1>🚀 AI Hub - Ultra Fast Generation</h1>
        
        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('ultra')">Ultra Gen <span class="unlimited-badge">⚡ Instant</span></div>
            <div class="tab" onclick="switchTab('arting')">Uncensored Image Gen <span class="warning-badge">⚠️ May Be Harmful</span></div>
            <div class="tab" onclick="switchTab('realistic')">Realistic Gen <span class="unlimited-badge">🚀 Unlimited</span></div>
            <div class="tab" onclick="switchTab('video')">Text to Video <span class="unlimited-badge">🎬 Multi-threaded</span></div>
            <div class="tab" onclick="switchTab('chatbot')">AI Chatbot <span class="unlimited-badge">💬 Smart Assistant</span></div>
        </div>
        
        <!-- Ultra Gen Section -->
        <div id="ultra" class="generator-section active">
            <div class="section-title">Ultra Gen ⚡ <span class="unlimited-badge">INSTANT - No Queue</span></div>
            
            <div class="input-group">
                <textarea id="promptUltra" placeholder="Enter your ultra-realistic prompt (e.g., Professional portrait of a CEO in modern office)"></textarea>
            </div>
            
            <button class="btn ultra-btn" onclick="generateUltraGen()">Generate Ultra Image</button>
            
            <div class="loader" id="loaderUltra"></div>
            <div class="progress" id="progressUltra"></div>
            
            <div id="resultUltra" class="result">
                <div class="image-container" id="imageContainerUltra"></div>
                <button class="btn download-btn" onclick="downloadSingleImage(generatedUltraImage, 'ultra')">
                    Download Ultra Image
                </button>
                <button class="btn ultra-btn" onclick="resetForm('ultra')">Generate Again</button>
            </div>
        </div>
        
        <!-- Uncensored AI Section -->
        <div id="arting" class="generator-section">
            <div class="section-title">Uncensored Image Generator ⚠️</div>
            
            <div class="input-group">
                <textarea id="prompt1" placeholder="Enter your image prompt (e.g., A futuristic city at night) - No content restrictions"></textarea>
            </div>
            
            <div class="input-group">
                <label for="imageCount1" style="display: block; margin-bottom: 10px; color: #ff6b6b;">Number of Images (Max 5):</label>
                <input type="number" id="imageCount1" class="number-input" min="1" max="5" value="1" placeholder="1-5 images">
            </div>
            
            <button class="btn" onclick="generateImages('arting')">Generate Uncensored Images</button>
            
            <div class="loader" id="loader1"></div>
            <div class="progress" id="progress1"></div>
            
            <div id="result1" class="result">
                <div class="image-container" id="imageContainer1"></div>
                <button class="btn download-all-btn" onclick="downloadAllImages('arting')">Download All</button>
                <button class="btn" onclick="resetForm('arting')">Generate Again</button>
            </div>
        </div>
        
        <!-- Realistic AI Section -->
        <div id="realistic" class="generator-section">
            <div class="section-title">Realistic Image Generator 🚀 <span class="unlimited-badge">Unlimited + Parallel Processing</span></div>
            
            <div class="input-group">
                <textarea id="prompt2" placeholder="Enter your realistic image prompt (e.g., A professional portrait of a woman in business attire)"></textarea>
            </div>
            
            <div class="input-group">
                <label for="imageCount2" style="display: block; margin-bottom: 10px; color: #e74c3c;">Number of Images (Unlimited - Fast Parallel Generation):</label>
                <input type="number" id="imageCount2" class="number-input" min="1" max="100" value="1" placeholder="Any number">
            </div>
            
            <button class="btn realistic-btn" onclick="generateImages('realistic')">Generate Realistic Images (Parallel)</button>
            
            <div class="loader" id="loader2"></div>
            <div class="progress" id="progress2"></div>
            
            <div id="result2" class="result">
                <div class="image-container" id="imageContainer2"></div>
                <button class="btn download-all-btn" onclick="downloadAllImages('realistic')">Download All</button>
                <button class="btn realistic-btn" onclick="resetForm('realistic')">Generate Again</button>
            </div>
        </div>
        
        <!-- Text to Video Section -->
        <div id="video" class="generator-section">
            <div class="section-title">Text to Video Generator 🎬 <span class="unlimited-badge">Unlimited + Multi-threaded</span></div>
            
            <div class="input-group">
                <textarea id="prompt3" placeholder="Enter your video prompt (e.g., A boy walking in the park, A sunset over mountains)"></textarea>
            </div>
            
            <div class="input-group">
                <label for="videoCount" style="display: block; margin-bottom: 10px; color: #8e44ad;">Number of Videos (Unlimited - Multi-threaded Generation):</label>
                <input type="number" id="videoCount" class="number-input" min="1" max="100" value="1" placeholder="Any number">
            </div>
            
            <button class="btn video-btn" onclick="generateVideos()">Generate Videos (Multi-threaded)</button>
            
            <div class="loader" id="loader3"></div>
            <div class="progress" id="progress3"></div>
            
            <div id="result3" class="result">
                <div class="video-container" id="videoContainer"></div>
                <button class="btn download-all-btn" onclick="downloadAllVideos()">Download All Videos</button>
                <button class="btn video-btn" onclick="resetForm('video')">Generate Again</button>
            </div>
        </div>
        
        <!-- Chatbot Section -->
        <div id="chatbot" class="generator-section">
            <div class="section-title">AI Chatbot Assistant 💬</div>
            
            <div class="chat-container">
                <div class="chat-header">
                    <div>🤖 AI Assistant</div>
                    <small>Ask me anything! I can help with coding, questions, and more.</small>
                </div>
                
                <div class="chat-messages" id="chatMessages">
                    <div class="message bot-message">
                        <div class="message-content">
                            Hello! I'm your AI assistant. How can I help you today? 😊
                        </div>
                    </div>
                </div>
                
                <div class="chat-input-container">
                    <div class="chat-input-wrapper">
                        <input type="text" id="chatInput" class="chat-input" placeholder="Type your message here..." onkeypress="handleChatKeyPress(event)">
                        <button class="send-btn" id="sendBtn" onclick="sendMessage()">Send</button>
                    </div>
                </div>
            </div>
        </div>
        
        <footer>Created by Adarsh Bhai - Ultra Fast AI Hub</footer>
    </div>

    <script>
        let generatedImagesArting = [];
        let generatedImagesRealistic = [];
        let generatedVideos = [];
        let generatedUltraImage = '';
        let chatHistory = [];

        function switchTab(tabName) {
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.generator-section').forEach(section => section.classList.remove('active'));
            
            document.querySelector(`.tab[onclick="switchTab('${tabName}')"]`).classList.add('active');
            document.getElementById(tabName).classList.add('active');
        }

        async function generateUltraGen() {
            const prompt = document.getElementById('promptUltra').value.trim();
            
            if (!prompt) {
                alert('Please enter a prompt!');
                return;
            }

            const loader = document.getElementById('loaderUltra');
            const result = document.getElementById('resultUltra');
            const progress = document.getElementById('progressUltra');
            const generateBtn = event.target;
            const imageContainer = document.getElementById('imageContainerUltra');
            
            loader.style.display = 'block';
            progress.style.display = 'block';
            result.style.display = 'none';
            generateBtn.disabled = true;
            imageContainer.innerHTML = '';
            
            progress.textContent = 'Processing ultra generation...';

            try {
                const response = await fetch('/generate_ultra', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt })
                });
                
                const data = await response.json();
                
                if (data.imageUrl) {
                    generatedUltraImage = data.imageUrl;
                    const imageItem = document.createElement('div');
                    imageItem.className = 'image-item';
                    imageItem.innerHTML = `
                        <img src="${data.imageUrl}" alt="Ultra Generated Image" class="generated-image">
                    `;
                    imageContainer.appendChild(imageItem);
                    result.style.display = 'block';
                    progress.textContent = 'Ultra image generated successfully!';
                } else {
                    alert('Failed to generate ultra image. Please try again.');
                    progress.style.display = 'none';
                }
                
            } catch (error) {
                alert('Error: ' + error.message);
                progress.style.display = 'none';
            } finally {
                loader.style.display = 'none';
                generateBtn.disabled = false;
            }
        }

        async function generateImages(type) {
            const promptId = type === 'arting' ? 'prompt1' : 'prompt2';
            const countId = type === 'arting' ? 'imageCount1' : 'imageCount2';
            const loaderId = type === 'arting' ? 'loader1' : 'loader2';
            const progressId = type === 'arting' ? 'progress1' : 'progress2';
            const resultId = type === 'arting' ? 'result1' : 'result2';
            const containerId = type === 'arting' ? 'imageContainer1' : 'imageContainer2';
            
            const prompt = document.getElementById(promptId).value.trim();
            const imageCount = parseInt(document.getElementById(countId).value) || 1;
            
            if (!prompt) {
                alert('Please enter a prompt!');
                return;
            }

            if (type === 'arting' && (imageCount < 1 || imageCount > 5)) {
                alert('Please select between 1-5 images for Arting AI!');
                return;
            }

            if (type === 'realistic' && (imageCount < 1 || imageCount > 100)) {
                alert('Please select between 1-100 images for Realistic Gen!');
                return;
            }

            const loader = document.getElementById(loaderId);
            const result = document.getElementById(resultId);
            const progress = document.getElementById(progressId);
            const generateBtn = event.target;
            const imageContainer = document.getElementById(containerId);
            
            loader.style.display = 'block';
            progress.style.display = 'block';
            result.style.display = 'none';
            generateBtn.disabled = true;
            imageContainer.innerHTML = '';
            
            if (type === 'arting') {
                generatedImagesArting = [];
            } else {
                generatedImagesRealistic = [];
            }

            try {
                if (type === 'realistic') {
                    progress.textContent = `Starting parallel generation of ${imageCount} images...`;
                    
                    const endpoint = '/generate_realistic_batch';
                    const response = await fetch(endpoint, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt, count: imageCount })
                    });
                    
                    const data = await response.json();
                    
                    if (data.images && data.images.length > 0) {
                        generatedImagesRealistic = data.images;
                        data.images.forEach((imageUrl, index) => {
                            addImageToContainer(imageUrl, index + 1, containerId);
                        });
                        result.style.display = 'block';
                        progress.textContent = `Successfully generated ${data.images.length} image(s) in parallel!`;
                    } else {
                        alert('Failed to generate images. Please try again.');
                        progress.style.display = 'none';
                    }
                } else {
                    for (let i = 0; i < imageCount; i++) {
                        progress.textContent = `Generating image ${i + 1} of ${imageCount}...`;
                        
                        const endpoint = '/generate';
                        const response = await fetch(endpoint, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ prompt })
                        });
                        
                        const data = await response.json();
                        
                        if (data.imageUrl) {
                            generatedImagesArting.push(data.imageUrl);
                            addImageToContainer(data.imageUrl, i + 1, containerId);
                        } else {
                            console.error(`Failed to generate image ${i + 1}`);
                        }
                    }
                    
                    if (generatedImagesArting.length > 0) {
                        result.style.display = 'block';
                        progress.textContent = `Successfully generated ${generatedImagesArting.length} image(s)!`;
                    } else {
                        alert('Failed to generate any images. Please try again.');
                        progress.style.display = 'none';
                    }
                }
                
            } catch (error) {
                alert('Error: ' + error.message);
                progress.style.display = 'none';
            } finally {
                loader.style.display = 'none';
                generateBtn.disabled = false;
            }
        }

        async function generateVideos() {
            const prompt = document.getElementById('prompt3').value.trim();
            const videoCount = parseInt(document.getElementById('videoCount').value) || 1;
            
            if (!prompt) {
                alert('Please enter a video prompt!');
                return;
            }

            if (videoCount < 1 || videoCount > 100) {
                alert('Please select between 1-100 videos!');
                return;
            }

            const loader = document.getElementById('loader3');
            const result = document.getElementById('result3');
            const progress = document.getElementById('progress3');
            const generateBtn = event.target;
            const videoContainer = document.getElementById('videoContainer');
            
            loader.style.display = 'block';
            progress.style.display = 'block';
            result.style.display = 'none';
            generateBtn.disabled = true;
            videoContainer.innerHTML = '';
            generatedVideos = [];

            try {
                progress.textContent = `Starting multi-threaded generation of ${videoCount} video(s)...`;
                
                const response = await fetch('/generate_videos_batch', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt, count: videoCount })
                });
                
                const data = await response.json();
                
                if (data.videos && data.videos.length > 0) {
                    generatedVideos = data.videos;
                    data.videos.forEach((videoUrl, index) => {
                        addVideoToContainer(videoUrl, index + 1);
                    });
                    result.style.display = 'block';
                    progress.textContent = `Successfully generated ${data.videos.length} video(s) using multi-threading!`;
                } else {
                    alert('Failed to generate videos. Please try again.');
                    progress.style.display = 'none';
                }
                
            } catch (error) {
                alert('Error: ' + error.message);
                progress.style.display = 'none';
            } finally {
                loader.style.display = 'none';
                generateBtn.disabled = false;
            }
        }

        function addImageToContainer(imageUrl, index, containerId) {
            const imageContainer = document.getElementById(containerId);
            
            const imageItem = document.createElement('div');
            imageItem.className = 'image-item';
            
            imageItem.innerHTML = `
                <img src="${imageUrl}" alt="Generated Image ${index}" class="generated-image">
                <button class="btn download-btn" onclick="downloadSingleImage('${imageUrl}', ${index})">
                    Download Image ${index}
                </button>
            `;
            
            imageContainer.appendChild(imageItem);
        }

        function addVideoToContainer(videoUrl, index) {
            const videoContainer = document.getElementById('videoContainer');
            
            const videoItem = document.createElement('div');
            videoItem.className = 'video-item';
            
            videoItem.innerHTML = `
                <video controls class="generated-video">
                    <source src="${videoUrl}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
                <button class="btn download-video-btn" onclick="downloadSingleVideo('${videoUrl}', ${index})">
                    Download Video ${index}
                </button>
            `;
            
            videoContainer.appendChild(videoItem);
        }

        function downloadSingleImage(imageUrl, index) {
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = `generated_image_${index}.png`;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        function downloadSingleVideo(videoUrl, index) {
            const link = document.createElement('a');
            link.href = videoUrl;
            link.download = `generated_video_${index}.mp4`;
            link.target = '_blank';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        }

        async function downloadAllImages(type) {
            const currentImages = type === 'arting' ? generatedImagesArting : generatedImagesRealistic;
            
            if (currentImages.length === 0) {
                alert('No images to download!');
                return;
            }

            for (let i = 0; i < currentImages.length; i++) {
                setTimeout(() => {
                    downloadSingleImage(currentImages[i], i + 1);
                }, i * 1000);
            }
        }

        async function downloadAllVideos() {
            if (generatedVideos.length === 0) {
                alert('No videos to download!');
                return;
            }

            for (let i = 0; i < generatedVideos.length; i++) {
                setTimeout(() => {
                    downloadSingleVideo(generatedVideos[i], i + 1);
                }, i * 1000);
            }
        }

        function resetForm(type) {
            if (type === 'ultra') {
                document.getElementById('promptUltra').value = '';
                document.getElementById('resultUltra').style.display = 'none';
                document.getElementById('progressUltra').style.display = 'none';
                document.getElementById('imageContainerUltra').innerHTML = '';
                generatedUltraImage = '';
                return;
            }
            
            if (type === 'video') {
                document.getElementById('prompt3').value = '';
                document.getElementById('videoCount').value = '1';
                document.getElementById('result3').style.display = 'none';
                document.getElementById('progress3').style.display = 'none';
                document.getElementById('videoContainer').innerHTML = '';
                generatedVideos = [];
                return;
            }

            const promptId = type === 'arting' ? 'prompt1' : 'prompt2';
            const countId = type === 'arting' ? 'imageCount1' : 'imageCount2';
            const resultId = type === 'arting' ? 'result1' : 'result2';
            const progressId = type === 'arting' ? 'progress1' : 'progress2';
            const containerId = type === 'arting' ? 'imageContainer1' : 'imageContainer2';
            
            document.getElementById(promptId).value = '';
            document.getElementById(countId).value = '1';
            document.getElementById(resultId).style.display = 'none';
            document.getElementById(progressId).style.display = 'none';
            document.getElementById(containerId).innerHTML = '';
            
            if (type === 'arting') {
                generatedImagesArting = [];
            } else {
                generatedImagesRealistic = [];
            }
        }
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/generate_ultra', methods=['POST'])
@limiter.limit("10 per minute")
def generate_ultra():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        image_url = generate_ultra_image(prompt)
        
        if image_url:
            return jsonify({'imageUrl': image_url})
        else:
            return jsonify({'error': 'Failed to generate ultra image'}), 500

    except Exception as e:
        print(f"Ultra generation error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/generate', methods=['POST'])
@limiter.limit("5 per minute")
def generate_image():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        user = generate_user_agent()
        headers = {
            'authority': 'api.arting.ai',
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9',
            'authorization': '3a2bc631-e77b-4a85-a954-ba9e7bab07e6',
            'cache-control': 'no-cache',
            'content-type': 'application/json',
            'origin': 'https://arting.ai',
            'pragma': 'no-cache',
            'referer': 'https://arting.ai/',
            'sec-ch-ua': '"Chromium";v="137", "Not/A)Brand";v="24"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': user,
        }
        
        json_data = {
            'prompt': prompt,
            'model_id': 'maturemalemix_v14',
            'samples': 1,
            'height': 768,
            'width': 512,
            'negative_prompt': 'painting, extra fingers, mutated hands, poorly drawn hands, poorly drawn face, deformed, ugly, blurry, bad anatomy, bad proportions, extra limbs, cloned face, skinny, glitchy, double torso, extra arms, extra hands, mangled fingers, missing lips, ugly face, distorted face, extra legs, anime',
            'seed': -1,
            'lora_ids': '',
            'lora_weight': '0.7',
            'sampler': 'Euler a',
            'steps': 48,
            'guidance': 7,
            'clip_skip': 2,
            'is_nsfw': True,
        }

        r = requests.session()
        r1 = r.post('https://api.arting.ai/api/cg/text-to-image/create', headers=headers, json=json_data, timeout=30)
        
        if r1.status_code != 200:
            return jsonify({'error': f'Failed to initiate image generation. Status: {r1.status_code}'}), 500
            
        try:
            response_data = r1.json()
        except ValueError:
            return jsonify({'error': 'Invalid JSON response from API'}), 500
            
        request_id = response_data.get("data", {}).get("request_id")
        if not request_id:
            return jsonify({'error': 'Invalid response from API - no request_id'}), 500

        for attempt in range(60):
            try:
                r2 = r.post('https://api.arting.ai/api/cg/text-to-image/get', headers=headers, json={'request_id': request_id}, timeout=30)
                
                if r2.status_code != 200:
                    time.sleep(5)
                    continue
                    
                res_json = r2.json()
                output = res_json.get("data", {}).get("output", [])
                
                if output and len(output) > 0:
                    return jsonify({'imageUrl': output[0]})
                    
            except Exception as e:
                print(f"Polling attempt {attempt + 1} failed: {str(e)}")
                
            time.sleep(5)

        return jsonify({'error': 'Image generation timed out'}), 504

    except Exception as e:
        print(f"Generation error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/generate_realistic_batch', methods=['POST'])
@limiter.limit("5 per minute")
def generate_realistic_batch():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt')
        count = data.get('count', 1)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        max_concurrent = min(random.randint(5, 8), count)
        print(f"Using {max_concurrent} concurrent threads for {count} images")
        
        all_images = []
        
        for batch_start in range(0, count, max_concurrent):
            batch_end = min(batch_start + max_concurrent, count)
            batch_size = batch_end - batch_start
            
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = [executor.submit(generate_single_realistic_image, prompt) for _ in range(batch_size)]
                
                batch_images = []
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        batch_images.append(result)
                
                all_images.extend(batch_images)
                print(f"Batch {batch_start//max_concurrent + 1} completed: {len(batch_images)}/{batch_size} images")

        if all_images:
            return jsonify({
                'images': all_images,
                'total_generated': len(all_images),
                'requested': count,
                'concurrent_threads': max_concurrent
            })
        else:
            return jsonify({'error': 'Failed to generate any images'}), 500

    except Exception as e:
        print(f"Batch generation error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

@app.route('/generate_videos_batch', methods=['POST'])
@limiter.limit("3 per minute")
def generate_videos_batch():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt')
        count = data.get('count', 1)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        max_concurrent = min(random.randint(3, 5), count)
        print(f"Using {max_concurrent} concurrent threads for {count} videos")
        
        all_videos = []
        
        for batch_start in range(0, count, max_concurrent):
            batch_end = min(batch_start + max_concurrent, count)
            batch_size = batch_end - batch_start
            
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                futures = [executor.submit(generate_single_video, prompt) for _ in range(batch_size)]
                
                batch_videos = []
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        batch_videos.append(result)
                
                all_videos.extend(batch_videos)
                print(f"Batch {batch_start//max_concurrent + 1} completed: {len(batch_videos)}/{batch_size} videos")

        if all_videos:
            return jsonify({
                'videos': all_videos,
                'total_generated': len(all_videos),
                'requested': count,
                'concurrent_threads': max_concurrent
            })
        else:
            return jsonify({'error': 'Failed to generate any videos'}), 500

    except Exception as e:
        print(f"Batch video generation error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
