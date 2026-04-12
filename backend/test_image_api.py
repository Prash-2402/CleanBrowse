import requests
import json

BASE_URL = "http://127.0.0.1:5000"
ANALYZE_IMAGE_ROUTE = "/analyze-image"

def test_analyze_image():
    print("--- Testing Image Moderation API ---")
    
    test_cases = [
        {
            "name": "Safe Image (Metadata)",
            "data": {
                "image_url": "http://example.com/cat.jpg",
                "alt_text": "A cute cat",
                "title": "Cat"
            },
            "expected_label": "safe"
        },
        {
            "name": "Unsafe Image (Metadata - URL)",
            "data": {
                "image_url": "http://example.com/porn_thumbnail.jpg",
                "alt_text": "Some image",
                "title": ""
            },
            "expected_label": "unsafe"
        },
        {
            "name": "Unsafe Image (Metadata - Alt)",
            "data": {
                "image_url": "http://example.com/img123.jpg",
                "alt_text": "Explicit content here",
                "title": ""
            },
            "expected_label": "unsafe"
        },
        {
            "name": "AI Analysis Fallback (Safe)",
            "data": {
                "image_url": "https://raw.githubusercontent.com/onnx/models/main/vision/classification/mobilenet/dependencies/cat.jpg",
                "alt_text": "Random image",
                "title": ""
            },
            # This should trigger Local AI analysis
            "expected_label": "safe"
        }
    ]

    for case in test_cases:
        print(f"\nRunning test: {case['name']}")
        try:
            response = requests.post(f"{BASE_URL}{ANALYZE_IMAGE_ROUTE}", json=case['data'])
            if response.status_code == 200:
                result = response.json()
                print(f"Result: {result}")
                if result.get("label") == case['expected_label']:
                    print("PASS")
                else:
                    print(f"FAIL: Expected {case['expected_label']}, got {result.get('label')}")
            else:
                print(f"FAIL: Status Code {response.status_code}, {response.text}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    test_analyze_image()
