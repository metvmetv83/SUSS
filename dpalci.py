import requests
import re
import os
import json
import time
from urllib.parse import quote

GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"

PROXIES = [
    "https://api.allorigins.win/get?url=",
    "https://api.codetabs.com/v1/proxy/?quest="
]

def get_headers():
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'}

def fetch_with_retry(target_url):
    for proxy in PROXIES:
        try:
            full_url = proxy + quote(target_url)
            res = requests.get(full_url, headers=get_headers(), timeout=25)
            if res.status_code == 200:
                if "allorigins" in proxy:
                    return res.json().get('contents', '')
                return res.text
        except:
            continue
    return ""

def scrape_any_path(path_suffix):
    """Hem koleksiyonları hem de özel sayfaları (diziler/filmler) tarar."""
    results = []
    # path_suffix'e göre temiz URL oluşturma
    target_base = f"{BASE_URL}/{path_suffix}"
    print(f"\n>>> {path_suffix.upper()} taranıyor...")

    for p in range(1, 8):
        # Sayfalama: İlk sayfa yalın, sonrakiler formatlı
        if p == 1:
            current_url = target_base
        else:
            # Diziler/Filmler /page/2 kullanırken, koleksiyonlar ?paged=2 kullanabiliyor
            # İkisini de kapsayan genel yapı
            current_url = f"{target_base}/page/{p}/" if "koleksiyon" not in path_suffix else f"{target_base}?paged={p}"
        
        print(f"  - Sayfa {p} zorlanıyor...")
        html = fetch_with_retry(current_url)
        if not html: break
            
        # Gelişmiş Regex: Link ve Başlığı her türlü yapıdan yakalar
        items = re.findall(r'href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
        if not items:
            items = re.findall(r'class="title">.*?<a href="([^"]+)">([^<]+)</a>', html, re.DOTALL)

        if not items:
            print(f"    ! Bu sayfa boş veya içerik bitti.")
            break
        
        page_count = 0
        for href, title in items:
            if not any(x in href for x in ['/page/', '/kategori/', '?paged=']):
                full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
                results.append({"baslik": title.strip().upper(), "url": full_link})
                page_count += 1
        
        print(f"    + {page_count} içerik yakalandı.")
        if page_count < 5: break
        time.sleep(0.3)
            
    return results

def main():
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Versiyon Yükseltildi: {new_v}")

    # Senin verdiğin tam liste (Koleksiyonlar, Türler ve Ana Sayfalar)
    targets = [
        "koleksiyon/netflix", "koleksiyon/exxen", "koleksiyon/blutv", 
        "koleksiyon/disney", "koleksiyon/amazon-prime", "koleksiyon/tod-bein", 
        "koleksiyon/gain", "tur/mubi", "diziler", "filmler"
    ]
    
    final_data = []
    for t in targets:
        final_data.extend(scrape_any_path(t))

    # Tekilleştirme
    unique_data = {item['url']: item for item in final_data}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=4)

    print(f"\n--- İŞLEM TAMAMLANDI ---")
    print(f"Toplam {len(unique_data)} benzersiz içerik kaydedildi.")

if __name__ == "__main__":
    main()
