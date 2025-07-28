from flask import Flask, render_template_string, request, jsonify
import requests
import random
import string
import time
import base64
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)

# Helper functions for API
def generate_user_agent():
    return 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36'

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

# HTML/CSS/JS template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Image Generator</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        body {
            background: #1a1a1a;
            color: #ffffff;
            min-height: 100vh;
            padding: 20px;
        }
        .main-container {
            max-width: 1000px;
            margin: 0 auto;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 30px;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            text-align: center;
        }
        .tabs {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
            gap: 10px;
        }
        .tab {
            background: #2a2a2a;
            border: 1px solid #444;
            padding: 12px 25px;
            border-radius: 25px;
            color: #fff;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .tab.active {
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            border-color: transparent;
        }
        .tab:hover {
            border-color: #4ecdc4;
        }
        .generator-section {
            display: none;
            max-width: 700px;
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
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 10px;
            padding: 15px;
            color: #fff;
            font-size: 1rem;
            resize: none;
            margin-bottom: 15px;
            outline: none;
        }
        textarea:focus {
            border-color: #4ecdc4;
            box-shadow: 0 0 10px rgba(78, 205, 196, 0.3);
        }
        .number-input {
            width: 200px;
            background: #2a2a2a;
            border: 1px solid #444;
            border-radius: 10px;
            padding: 12px 15px;
            color: #fff;
            font-size: 1rem;
            outline: none;
            margin-bottom: 15px;
        }
        .number-input:focus {
            border-color: #4ecdc4;
            box-shadow: 0 0 10px rgba(78, 205, 196, 0.3);
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
        .realistic-btn {
            background: linear-gradient(45deg, #e74c3c, #f39c12);
        }
        .realistic-btn:hover {
            box-shadow: 0 5px 15px rgba(231, 76, 60, 0.4);
        }
        .loader {
            display: none;
            border: 5px solid #2a2a2a;
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
        .image-item {
            position: relative;
            background: #2a2a2a;
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
        .download-btn {
            background: linear-gradient(45deg, #4ecdc4, #45b7b8);
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
            color: #888;
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
            .image-container {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="main-container">
        <h1>AI Image Generator</h1>
        
        <!-- Tabs -->
        <div class="tabs">
            <div class="tab active" onclick="switchTab('arting')">Uncensored Image Gen <span class="unlimited-badge">⚠️ May Be Harmful</span></div>
            <div class="tab" onclick="switchTab('realistic')">Realistic Gen <span class="unlimited-badge">🚀 Unlimited + Fast</span></div>
        </div>
        
        <!-- Uncensored AI Section -->
        <div id="arting" class="generator-section active">
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
        
        <footer>Created by Adarsh Bhai</footer>
    </div>

    <script>
        let generatedImagesArting = [];
        let generatedImagesRealistic = [];

        function switchTab(tabName) {
            // Remove active class from all tabs and sections
            document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.generator-section').forEach(section => section.classList.remove('active'));
            
            // Add active class to clicked tab and corresponding section
            event.target.classList.add('active');
            document.getElementById(tabName).classList.add('active');
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
                    // Parallel generation for realistic images
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
                    // Sequential generation for uncensored images
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

        function downloadSingleImage(imageUrl, index) {
            const link = document.createElement('a');
            link.href = imageUrl;
            link.download = `generated_image_${index}.png`;
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
                }, i * 1000); // Delay each download by 1 second
            }
        }

        function resetForm(type) {
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

# Route to serve the main page
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Route to handle Arting AI image generation
@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Generate dynamic values
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

        # Step 1: Request to generate
        r = requests.session()
        r1 = r.post('https://api.arting.ai/api/cg/text-to-image/create', headers=headers, json=json_data)
        
        if r1.status_code != 200:
            return jsonify({'error': f'Failed to initiate image generation. Status: {r1.status_code}'}), 500
            
        try:
            response_data = r1.json()
        except ValueError:
            return jsonify({'error': 'Invalid JSON response from API'}), 500
            
        request_id = response_data.get("data", {}).get("request_id")
        if not request_id:
            return jsonify({'error': 'Invalid response from API - no request_id'}), 500

        # Step 2: Poll until output is ready
        for attempt in range(60):  # Max 5 minutes (60 * 5s)
            try:
                r2 = r.post('https://api.arting.ai/api/cg/text-to-image/get', headers=headers, json={'request_id': request_id})
                
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

        # Generate image
        response = requests.post(gen_url, headers=gen_headers, data=api_data, timeout=30)
        
        if response.status_code != 200:
            return None

        # Upload to 0x0.st to get a URL
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
# Route to handle batch realistic image generation (parallel)
@app.route('/generate_realistic_batch', methods=['POST'])
def generate_realistic_batch():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt')
        count = data.get('count', 1)
        
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        # Random concurrent requests between 5-10
        max_concurrent = random.randint(5, 10)
        print(f"Using {max_concurrent} concurrent threads for {count} images")
        
        # Generate images in parallel batches
        all_images = []
        
        # Process in batches if count > max_concurrent
        for batch_start in range(0, count, max_concurrent):
            batch_end = min(batch_start + max_concurrent, count)
            batch_size = batch_end - batch_start
            
            with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                # Submit all tasks for this batch
                futures = [executor.submit(generate_single_realistic_image, prompt) for _ in range(batch_size)]
                
                # Collect results as they complete
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

# Route to handle single realistic image generation
@app.route('/generate_realistic', methods=['POST'])
def generate_realistic_image():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        prompt = data.get('prompt')
        if not prompt:
            return jsonify({'error': 'Prompt is required'}), 400

        result = generate_single_realistic_image(prompt)
        
        if result:
            return jsonify({'imageUrl': result})
        else:
            return jsonify({'error': 'Failed to generate image'}), 500

    except Exception as e:
        print(f"Realistic generation error: {str(e)}")
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
