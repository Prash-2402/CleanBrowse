import os
import re
import requests
import numpy as np
import onnxruntime as ort
from PIL import Image
from io import BytesIO
from backend.api_config import (
    UNSAFE_KEYWORDS,
    IMAGE_MODEL_PATH,
    SAFE_LABEL,
    UNSAFE_LABEL,
)

# Precompile keyword regex for metadata pass (more aggressive for URLs)
KEYWORD_PATTERN = r'(?:^|[^a-zA-Z0-9])(?:' + '|'.join(map(re.escape, UNSAFE_KEYWORDS)) + r')(?=[^a-zA-Z0-9]|$)'
KEYWORD_REGEX = re.compile(KEYWORD_PATTERN, re.IGNORECASE)

class ImageModerator:
    def __init__(self):
        self.session = None
        try:
            if IMAGE_MODEL_PATH.exists():
                self.session = ort.InferenceSession(str(IMAGE_MODEL_PATH))
                print(f"ImageModerator: ONNX session initialized from {IMAGE_MODEL_PATH}")
        except Exception as e:
            print(f"ImageModerator: Failed to load ONNX model - {e}")

    def analyze(self, image_url, alt_text="", title=""):
        """3-Tier Analysis: Metadata -> Local AI -> OpenAI Fallback"""
        
        # Tier 1: Metadata Check (Fast)
        metadata_content = f"{image_url} {alt_text} {title}"
        if KEYWORD_REGEX.search(metadata_content):
            return {"label": UNSAFE_LABEL, "score": 1.0, "reason": "metadata_match"}

        # Tier 2: Local AI Check
        if not self.session:
            return {"label": SAFE_LABEL, "score": 0.0, "reason": "model_unavailable"}

        try:
            image_data = self._fetch_image(image_url)
            if not image_data:
                return {"label": SAFE_LABEL, "score": 0.0, "reason": "fetch_failed"}

            score = self._run_local_inference(image_data)
            
            # Decision Logic
            if score >= 0.7:
                return {"label": UNSAFE_LABEL, "score": score, "reason": "local_ai_high_confidence"}
            elif score <= 0.3:
                return {"label": SAFE_LABEL, "score": score, "reason": "local_ai_safe"}
            else:
                # Tier 3: OpenAI Fallback (Ambiguous range 0.3 - 0.7)
                return self._call_openai_fallback(image_url, score)
                
        except Exception as e:
            print(f"ImageModerator: Analysis error - {e}")
            return {"label": SAFE_LABEL, "score": 0.0, "reason": f"error: {str(e)}"}

    def _fetch_image(self, url):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                return Image.open(BytesIO(response.content)).convert('RGB')
        except:
            pass
        return None

    def _run_local_inference(self, pil_img):
        # Preprocess: Resize to 224x224 (standard for MobileNet)
        img = pil_img.resize((224, 224))
        img_data = np.array(img).astype('float32')
        
        # Normalize (standard ImageNet normalization)
        img_data /= 255.0
        # img_data = (img_data - [0.485, 0.456, 0.406]) / [0.229, 0.224, 0.225] # Not always needed for all models
        
        # Transpose to (Batch, Channel, Height, Width) if model expects it
        # Most ONNX models expect (1, 3, 224, 224) or (1, 224, 224, 3)
        input_meta = self.session.get_inputs()[0]
        input_name = input_meta.name
        input_shape = input_meta.shape
        
        # Check if model expects NCHW (Channels at index 1 or named 'num_channels')
        if len(input_shape) == 4 and (input_shape[1] == 3 or input_shape[1] == 'num_channels'):
            img_data = img_data.transpose(2, 0, 1)
            
        img_data = np.expand_dims(img_data, axis=0)
        
        outputs = self.session.run(None, {input_name: img_data})
        # The output depends on the specific model. 
        # Usually it's an array of probabilities for categories like [Drawing, Hentai, Neutral, Porn, Sexy]
        # We'll assume the model format is [Safe, Unsafe] or similar.
        # For the onnx-community detector, it returns probabilities for 5-6 categories.
        
        probs = outputs[0][0]
        # Common NSFWJS output indices: 0:drawing, 1:hentai, 2:neutral, 3:porn, 4:sexy
        # Unsafe = hentai + porn + sexy
        if len(probs) >= 5:
            unsafe_score = float(probs[1] + probs[3] + probs[4])
        else:
            # Fallback if model shape is different
            unsafe_score = float(max(probs)) # risky fallback
            
        return unsafe_score

    def _call_openai_fallback(self, image_url, local_score):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"label": SAFE_LABEL, "score": local_score, "reason": "openai_key_missing"}

        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        
        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Is this image safe for a child under 13? Reply with only 'Safe' or 'Unsafe' and a short reason."},
                            {"type": "image_url", "image_url": {"url": image_url}}
                        ],
                    }
                ],
                max_tokens=50,
            )
            result_text = response.choices[0].message.content.lower()
            is_unsafe = "unsafe" in result_text
            return {
                "label": UNSAFE_LABEL if is_unsafe else SAFE_LABEL,
                "score": 1.0 if is_unsafe else 0.0,
                "reason": f"openai_decision: {result_text}"
            }
        except Exception as e:
            print(f"OpenAI Fallback failed: {e}")
            return {"label": SAFE_LABEL, "score": local_score, "reason": "openai_error"}

# Singleton instance
moderator = ImageModerator()
