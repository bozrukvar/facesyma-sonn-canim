#!/usr/bin/env python3
"""
Facesyma Test Module — API Endpoint Tests
==========================================
Quick validation script to test all endpoints.

Run with local server:
  uvicorn api.test_api:app --reload --port 8004

Then in another terminal:
  python test_api_endpoints.py
"""

import requests
import json

BASE_URL = "http://localhost:8004"

def test_health():
    """Test health endpoint"""
    print("\n[1/5] Testing /test/health")
    response = requests.get(f"{BASE_URL}/test/health")
    assert response.status_code == 200
    print(f"      ✓ {response.json()}")

def test_types():
    """Test types endpoint"""
    print("\n[2/5] Testing /test/types")
    response = requests.get(f"{BASE_URL}/test/types")
    assert response.status_code == 200
    types = response.json()
    print(f"      ✓ Found {len(types)} test types:")
    for t in types:
        print(f"        - {t['test_type']}: {t['name']}")

def test_languages():
    """Test languages endpoint"""
    print("\n[3/5] Testing /test/languages")
    response = requests.get(f"{BASE_URL}/test/languages")
    assert response.status_code == 200
    langs = response.json()["languages"]
    print(f"      ✓ Found {len(langs)} languages:")
    for l in langs[:5]:
        print(f"        - {l['code']}: {l['name']}")
    print(f"        ... and {len(langs) - 5} more")

def test_start_test():
    """Test start test endpoint"""
    print("\n[4/5] Testing POST /test/start (personality test)")
    payload = {
        "test_type": "personality",
        "lang": "en"
    }
    response = requests.post(f"{BASE_URL}/test/start", json=payload)
    assert response.status_code == 200
    data = response.json()
    print(f"      ✓ Session created: {data['session_id'][:8]}...")
    print(f"      ✓ Questions: {len(data['questions'])} (expected 20)")
    print(f"      ✓ First question: \"{data['questions'][0]['text'][:50]}...\"")

    return data["session_id"]

def test_submit_test(session_id):
    """Test submit test endpoint"""
    print("\n[5/5] Testing POST /test/submit (personality test)")

    # Create sample answers (1-5 scale)
    answers = [
        {"q_id": "P001", "score": 4},
        {"q_id": "P002", "score": 3},
        {"q_id": "P003", "score": 2},
        {"q_id": "P004", "score": 5},
        {"q_id": "P005", "score": 3},
        {"q_id": "P006", "score": 4},
        {"q_id": "P007", "score": 2},
        {"q_id": "P008", "score": 1},
        {"q_id": "P009", "score": 5},
        {"q_id": "P010", "score": 4},
        {"q_id": "P011", "score": 2},
        {"q_id": "P012", "score": 3},
        {"q_id": "P013", "score": 4},
        {"q_id": "P014", "score": 5},
        {"q_id": "P015", "score": 2},
        {"q_id": "P016", "score": 3},
        {"q_id": "P017", "score": 4},
        {"q_id": "P018", "score": 3},
        {"q_id": "P019", "score": 5},
        {"q_id": "P020", "score": 4},
    ]

    payload = {
        "session_id": session_id,
        "test_type": "personality",
        "lang": "en",
        "answers": answers
    }

    response = requests.post(f"{BASE_URL}/test/submit", json=payload)
    assert response.status_code == 200
    data = response.json()

    print(f"      ✓ Result created: {data['result_id'][:8]}...")
    print(f"      ✓ Domain scores:")
    for domain, score in sorted(data['domain_scores'].items()):
        print(f"        - {domain}: {score:.1f}/100")
    print(f"      ✓ AI Interpretation: \"{data['ai_interpretation'][:60]}...\"")

def main():
    print("=" * 70)
    print("FACESYMA TEST MODULE — API VALIDATION")
    print("=" * 70)

    try:
        test_health()
        test_types()
        test_languages()
        session_id = test_start_test()
        test_submit_test(session_id)

        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
    except requests.exceptions.ConnectionError:
        print(f"\n❌ Cannot connect to {BASE_URL}")
        print("   Make sure the server is running: uvicorn api.test_api:app --reload --port 8004")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main()
