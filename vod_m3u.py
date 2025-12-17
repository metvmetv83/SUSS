import requests
import time

BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"
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
