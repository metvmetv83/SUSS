import requests
import time

BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjMwYTM5YzllLWE4ZDYtNGEwMC05NDBmLTFjMTE4NDgzZDcxMiIsInNnZCI6ImJkNmUyNmY5LWJkMzYtNDE2ZC05YWQzLTYzNjhlNGZkYTMyMiIsInNwZ2QiOiJjYjZmZGMwMi1iOGJlLTQ3MTYtYTZjYi1iZTEyYTg4YjdmMDkiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NTE3MDMxODQsImV4cCI6MTc1MTcwMzI0NCwiaWF0IjoxNzUxNzAzMTg0fQ.SGC_FfT7cU1RVM4E5rMYO2IsA4aYUoYq2SXl51-PZwM"

def test_api():
    """API'nin çalışıp çalışmadığını test et"""
    headers = {"Authorization": BEARER_TOKEN, "User-Agent": "Mozilla/5.0"}
    
    print("🔍 API Testi...")
    
    # Test 1: VOD list endpoint
    url1 = "https://core-api.kablowebtv.com/api/vod/list"
    print(f"1. Testing: {url1}")
    try:
        r1 = requests.get(url1, headers=headers, params={"PageSize": 1}, timeout=10)
        print(f"   Status: {r1.status_code}")
        print(f"   Response: {r1.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Hata: {e}")
    
    print("-" * 40)
    
    # Test 2: VOD detail endpoint
    test_vod_id = "0c38309b-3e7d-426e-b6e5-0316b61ae8f6"  # Örnek ID
    url2 = f"https://core-api.kablowebtv.com/api/vod/detail?VodUId={test_vod_id}"
    print(f"2. Testing: {url2}")
    try:
        r2 = requests.get(url2, headers=headers, timeout=10)
        print(f"   Status: {r2.status_code}")
        print(f"   Response: {r2.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Hata: {e}")
    
    print("-" * 40)
    
    # Test 3: Categories endpoint
    url3 = "https://core-api.kablowebtv.com/api/vod/categories"
    print(f"3. Testing: {url3}")
    try:
        r3 = requests.get(url3, headers=headers, timeout=10)
        print(f"   Status: {r3.status_code}")
        print(f"   Response: {r3.text[:200]}...")
    except Exception as e:
        print(f"   ❌ Hata: {e}")

if __name__ == "__main__":
    test_api()
