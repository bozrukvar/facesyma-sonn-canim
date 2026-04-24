#!/usr/bin/env python3
"""
Test Object Detection in Face Validation Service
Tests various images to verify correct detection
"""

import base64
import requests
import json
from pathlib import Path

# Test URL
BASE_URL = "http://localhost:8005"

def encode_image_to_base64(image_path: str) -> str:
    """Convert image file to base64 string"""
    with open(image_path, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

def test_face_validation(image_path: str, test_name: str):
    """Test face validation endpoint"""
    print(f"\n{'='*60}")
    print(f"Test: {test_name}")
    print(f"Image: {image_path}")
    print('='*60)

    if not Path(image_path).exists():
        print(f"❌ Image not found: {image_path}")
        return

    try:
        base64_image = encode_image_to_base64(image_path)
        print(f"✓ Image encoded ({len(base64_image)} chars)")

        response = requests.post(
            f"{BASE_URL}/api/v1/face/validate",
            json={
                "image": base64_image,
                "strict": False
            },
            timeout=30
        )

        print(f"✓ Response status: {response.status_code}")
        result = response.json()

        _rget = result.get
        print(f"\n📊 Results:")
        print(f"  Face Detected: {_rget('face_detected')}")
        print(f"  Is Valid: {_rget('is_valid')}")
        print(f"  Score: {_rget('score')}")

        if _rget('detected_object'):
            print(f"  🔍 Detected Object: {_rget('detected_object')}")

        print(f"\n💬 Issues:")
        for issue in _rget('issues', []):
            print(f"  • {issue}")

        print(f"\n💡 Recommendations:")
        for rec in _rget('recommendations', []):
            print(f"  • {rec}")

        return result

    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def run_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("FACE VALIDATION SERVICE - OBJECT DETECTION TESTS")
    print("="*60)

    # First, test health
    print("\n🏥 Testing Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Service is healthy")
        else:
            print("❌ Service health check failed")
            return
    except Exception as e:
        print(f"❌ Cannot connect to service: {e}")
        print("Make sure the service is running: docker-compose up -d face_validation")
        return

    # Test cases (you would need to provide actual test images)
    test_cases = [
        # ("path/to/human_face.jpg", "Valid human face"),
        # ("path/to/bottle.jpg", "Bottle image"),
        # ("path/to/dog.jpg", "Dog image"),
        # ("path/to/tree.jpg", "Tree image"),
        # ("path/to/car.jpg", "Car image"),
    ]

    if not test_cases:
        print("\n📝 No test images configured.")
        print("To test, add image paths to the test_cases list")
        print("Example:")
        print('  test_cases = [')
        print('    ("test_images/face.jpg", "Valid human face"),')
        print('    ("test_images/bottle.jpg", "Bottle image"),')
        print('  ]')
        return

    results = []
    for image_path, test_name in test_cases:
        result = test_face_validation(image_path, test_name)
        if result:
            results.append((test_name, result))

    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print('='*60)
    for test_name, result in results:
        status = "✅ PASS" if result.get('is_valid') else "❌ FAIL"
        print(f"{status} - {test_name}")

if __name__ == "__main__":
    run_tests()
