import requests
import re
import os
import json
import sys
import time

try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit(1)

KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://www.dizipal1226.com/'
    }

def fetch_all(base_url, category_path):
    """Sonsuz döngü ile tüm içerikleri çeker."""
    results = []
    # Genellikle DiziPal yapısında /filmler/page/2/ şeklinde gidilir.
    # Eğer bu çalışmazsa doğrudan /filmler sayfasındaki tüm linkleri kazırız.
    for page in range(1, 11): # İlk 10 sayfayı dene
        url = f"{base_url}/{category_path}/page/{page}/"
        proxy_url = f"{PROXY_BASE}{url}"
        print(f"{category_path} - Sayfa {page} çekiliyor...")
        
        try:
            res = requests.get(proxy_url, headers=get_headers(), timeout=30)
            if res.status_code != 200 or len(res.text) < 5000:
                break
                
            soup = BeautifulSoup(res.text, 'html.parser')
            items = soup.find_all('a', href=True)
            
            found_count = 0
            for a in items:
                href = a['href']
                title = a.get_text(strip=True)
                
                # Gereksiz linkleri filtrele
                if len(title) > 5 and base_url in href and not any(x in href for x in ['/page/', '/kategori/', '/etiket/']):
                    results.append({"baslik": title, "url": href})
                    found_count += 1
            
            if found_count == 0: break
            time.sleep(1) # Ban koruması
        except:
            break
            
    return results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # URL ve Versiyon Güncelleme
    if os.path.exists(KT_PATH):
        with open(KT_PATH, 'r', encoding='utf-8') as f: content = f.read()
        new_content = re.sub(r'override var mainUrl = ".*?"', f'override var mainUrl = "{target_url}"', content)
        with open(KT_PATH, 'w', encoding='utf-8') as f: f.write(new_content)
    
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r', encoding='utf-8') as f: g_content = f.read()
        v_match = re.search(r'version\s*=\s*(\d+)', g_content)
        if v_match:
            new_v = int(v_match.group(1)) + 1
            new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', g_content)
            with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)

    # Verileri Çek
    final_data = []
    final_data.extend(fetch_all(target_url, "filmler"))
    final_data.extend(fetch_all(target_url, "diziler"))

    # Tekilleştirme
    unique_data = []
    seen = set()
    for item in final_data:
        if item['url'] not in seen:
            unique_data.append(item)
            seen.add(item['url'])

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"Toplam {len(unique_data)} içerik başarıyla kaydedildi!")

if __name__ == "__main__":
    main()
