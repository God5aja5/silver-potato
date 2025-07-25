from flask import Flask, render_template_string, request, jsonify
import requests
import random
import string
import time
import base64

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
    <title>Text to Photo Generator</title>
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
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }
        .container {
            max-width: 700px;
            width: 100%;
            text-align: center;
        }
        h1 {
            font-size: 2.5rem;
            margin-bottom: 20px;
            background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
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
        #result {
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
        footer {
            margin-top: 30px;
            font-size: 0.9rem;
            color: #888;
        }
        @media (max-width: 600px) {
            h1 {
                font-size: 2rem;
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
    <div class="container">
        <h1>Text to Photo Generator</h1>
        
        <div class="input-group">
            <textarea id="prompt" placeholder="Enter your image prompt (e.g., A futuristic city at night)"></textarea>
        </div>
        
        <div class="input-group">
            <label for="imageCount" style="display: block; margin-bottom: 10px; color: #4ecdc4;">Number of Images:</label>
            <input type="number" id="imageCount" class="number-input" min="1" max="5" value="1" placeholder="1-5 images">
        </div>
        
        <button class="btn" onclick="generateImages()">Generate Images</button>
        
        <div class="loader" id="loader"></div>
        <div class="progress" id="progress"></div>
        
        <div id="result">
            <div class="image-container" id="imageContainer"></div>
            <button class="btn download-all-btn" onclick="downloadAllImages()">Download All</button>
            <button class="btn" onclick="resetForm()">Generate Again</button>
        </div>
        
        <footer>Created by Adarsh Bhai</footer>
    </div>

    <script>
        let generatedImages = [];

        async function generateImages() {
            const prompt = document.getElementById('prompt').value.trim();
            const imageCount = parseInt(document.getElementById('imageCount').value) || 1;
            
            if (!prompt) {
                alert('Please enter a prompt!');
                return;
            }

            if (imageCount < 1 || imageCount > 5) {
                alert('Please select between 1-5 images!');
                return;
            }

            const loader = document.getElementById('loader');
            const result = document.getElementById('result');
            const progress = document.getElementById('progress');
            const generateBtn = document.querySelector('.btn[onclick="generateImages()"]');
            const imageContainer = document.getElementById('imageContainer');
            
            loader.style.display = 'block';
            progress.style.display = 'block';
            result.style.display = 'none';
            generateBtn.disabled = true;
            imageContainer.innerHTML = '';
            generatedImages = [];

            try {
                for (let i = 0; i < imageCount; i++) {
                    progress.textContent = `Generating image ${i + 1} of ${imageCount}...`;
                    
                    const response = await fetch('/generate', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ prompt })
                    });
                    
                    const data = await response.json();
                    
                    if (data.imageUrl) {
                        generatedImages.push(data.imageUrl);
                        addImageToContainer(data.imageUrl, i + 1);
                    } else {
                        console.error(`Failed to generate image ${i + 1}`);
                    }
                }
                
                if (generatedImages.length > 0) {
                    result.style.display = 'block';
                    progress.textContent = `Successfully generated ${generatedImages.length} image(s)!`;
                } else {
                    alert('Failed to generate any images. Please try again.');
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

        function addImageToContainer(imageUrl, index) {
            const imageContainer = document.getElementById('imageContainer');
            
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

        async function downloadAllImages() {
            if (generatedImages.length === 0) {
                alert('No images to download!');
                return;
            }

            for (let i = 0; i < generatedImages.length; i++) {
                setTimeout(() => {
                    downloadSingleImage(generatedImages[i], i + 1);
                }, i * 1000); // Delay each download by 1 second
            }
        }

        function resetForm() {
            document.getElementById('prompt').value = '';
            document.getElementById('imageCount').value = '1';
            document.getElementById('result').style.display = 'none';
            document.getElementById('progress').style.display = 'none';
            document.getElementById('imageContainer').innerHTML = '';
            generatedImages = [];
        }
    </script>
</body>
</html>
"""

# Route to serve the main page
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

# Route to handle image generation
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
            'prompt': prompt,  # Fixed the typo: was 'promt'
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
