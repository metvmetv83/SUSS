import requests
import re
import os
import json
import time
from urllib.parse import quote

GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"

# İki farklı proxy üzerinden yük dengeleme yapacağız
PROXIES = [
    "https://api.allorigins.win/get?url=",
    "https://api.codetabs.com/v1/proxy/?quest="
]

def get_headers():
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

def fetch_with_retry(target_url):
    """İki farklı proxy'yi sırayla deneyerek veriyi çeker."""
    for proxy in PROXIES:
        try:
            full_url = proxy + quote(target_url)
            res = requests.get(full_url, headers=get_headers(), timeout=25)
            if res.status_code == 200:
                # AllOrigins JSON döner, Codetabs direkt text döner
                if "allorigins" in proxy:
                    return res.json().get('contents', '')
                return res.text
        except:
            continue
    return ""

def scrape_category_pages(category):
    results = []
    print(f"\n>>> {category.upper()} Koleksiyonu Zorlanıyor...")

    for p in range(1, 8): # 7 sayfa derinliğe kadar zorla
        target = f"{BASE_URL}/koleksiyon/{category}" + (f"?paged={p}" if p > 1 else "")
        print(f"  - Sayfa {p} taranıyor...")
        
        html = fetch_with_retry(target)
        if not html:
            break
            
        # Canavar Regex: Hem klasik yapıyı hem de yeni article yapılarını yakalar
        items = re.findall(r'href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
        if not items:
            items = re.findall(r'class="title">.*?<a href="([^"]+)">([^<]+)</a>', html, re.DOTALL)

        if not items:
            print(f"    ! Veri bulunamadı, bu kategori tamamlandı.")
            break
        
        page_count = 0
        for href, title in items:
            if not any(x in href for x in ['/page/', '/kategori/', '?paged=']):
                full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
                results.append({"baslik": title.strip().upper(), "url": full_link})
                page_count += 1
        
        print(f"    + {page_count} içerik yakalandı.")
        if page_count < 5: break # Sayfada çok az içerik varsa son sayfadır
        time.sleep(0.5)
            
    return results

def main():
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Versiyon Yükseltildi: {new_v}")

    # Eksiksiz Koleksiyon Listesi
    categories = [
        "exxen", "netflix", "gain", "disney", "blutv", 
        "yerli-dizi", "yabanci-diziler", "anime", "belgesel", "film-arsivi"
    ]
    
    final_data = []
    for cat in categories:
        final_data.extend(scrape_category_pages(cat))

    # Tekilleştirme (URL bazlı)
    unique_data = {item['url']: item for item in final_data}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=4)

    print(f"\n--- DEV ARŞİV GÜNCELLENDİ ---")
    print(f"Toplam {len(unique_data)} benzersiz içerik sisteme işlendi!")

if __name__ == "__main__":
    main()
