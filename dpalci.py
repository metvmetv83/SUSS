import requests
import os
import json
import re

GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
# Alternatif ve daha şeffaf bir proxy kullanıyoruz
PROXY = "https://api.allorigins.win/get?url="

def main():
    print(">>> Veritabanı Sızıntısı Başlatılıyor (API Mode)...")
    
    # 1. Versiyon Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))

    results = []
    # WordPress API uçları: Genellikle içerikler buralarda saklanır
    # posts = yazılar, pages = sayfalar
    api_endpoints = [
        f"{BASE_URL}/wp-json/wp/v2/posts?per_page=100",
        f"{BASE_URL}/wp-json/wp/v2/pages?per_page=100",
        f"{BASE_URL}/wp-json/wp/v2/dizi?per_page=100" # Özel post tipi
    ]

    for endpoint in api_endpoints:
        try:
            print(f"  - Hedef: {endpoint}")
            # AllOrigins proxy üzerinden JSON çek
            full_url = f"{PROXY}{requests.utils.quote(endpoint)}"
            res = requests.get(full_url, timeout=30)
            
            if res.status_code == 200:
                data = res.json()
                # AllOrigins veriyi 'contents' içine string olarak gömer, onu parse etmeliyiz
                if 'contents' in data:
                    posts = json.loads(data['contents'])
                    
                    if isinstance(posts, list):
                        for post in posts:
                            title = post.get('title', {}).get('rendered', '')
                            link = post.get('link', '')
                            if title and link:
                                results.append({
                                    "baslik": title.upper(),
                                    "url": link
                                })
                        print(f"    + {len(posts)} içerik API'den çekildi.")
        except Exception as e:
            print(f"    ! Bu uç kapalı veya korumalı.")

    # Eğer API'ler kapalıysa, Arama Parametresini (s=) kullanarak brute-force dene
    if not results:
        print("  - API kapalı. Arama motoru simülasyonu deneniyor...")
        search_target = f"{BASE_URL}/?s=a" # 'a' harfi içeren her şeyi ara
        try:
            full_url = f"{PROXY}{requests.utils.quote(search_target)}"
            res = requests.get(full_url, timeout=30)
            html = res.json().get('contents', '')
            
            # HTML içinden linkleri cımbızla çek
            links = re.findall(r'href="(https://www.dizipal1226.com/[^/"]+/)"[^>]*>([^<]+)</a>', html)
            for href, title in links:
                if len(title.strip()) > 3 and "kategori" not in href:
                    results.append({"baslik": title.strip().upper(), "url": href})
        except: pass

    # Tekilleştirme
    unique_data = {x['url']: x for x in results}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=4)

    print(f"\nSonuç: {len(unique_data)} içerik kaydedildi.")

if __name__ == "__main__":
    main()
