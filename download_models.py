import os
import requests
from pathlib import Path

MODELS_DIR = Path(__file__).resolve().parent / "backend" / "models"
MODEL_URL = "https://huggingface.co/onnx-community/nsfw-image-detector-ONNX/resolve/main/onnx/model.onnx?download=true"
MODEL_FILENAME = "nsfw_model.onnx"

def download_model():
    if not MODELS_DIR.exists():
        MODELS_DIR.mkdir(parents=True)
        
    target_path = MODELS_DIR / MODEL_FILENAME
    
    if target_path.exists():
        print(f"Model already exists at {target_path}")
        return
        
    print(f"Downloading model from {MODEL_URL}...")
    response = requests.get(MODEL_URL, stream=True)
    if response.status_code == 200:
        with open(target_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Successfully downloaded model to {target_path}")
    else:
        print(f"Failed to download model. Status code: {response.status_code}")

if __name__ == "__main__":
    download_model()
