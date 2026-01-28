import requests
import re
import os
import json
import time
from urllib.parse import quote

# Ayarlar
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
PROXY_BASE = "https://api.allorigins.win/get?url="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

def scrape_category_pages(category):
    results = []
    print(f"\n>>> {category.upper()} Arşivi Taranıyor...")

    for p in range(1, 5):
        # Sayfalama formatını ?paged= olarak değiştirdik
        if p == 1:
            target = f"{BASE_URL}/koleksiyon/{category}"
        else:
            target = f"{BASE_URL}/koleksiyon/{category}?paged={p}"
        
        print(f"  - Sayfa {p} yükleniyor...")
        
        try:
            url = PROXY_BASE + quote(target)
            res = requests.get(url, headers=get_headers(), timeout=40)
            
            if res.status_code == 200:
                html = res.json().get('contents', '')
                
                # Daha esnek bir regex: İçerik bloklarını yakala
                items = re.findall(r'href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
                
                if not items:
                    # Alternatif yapı denemesi
                    items = re.findall(r'class="title">.*?<a href="([^"]+)">([^<]+)</a>', html, re.DOTALL)

                if not items:
                    break
                
                found_count = 0
                for href, title in items:
                    if not any(x in href for x in ['/page/', '/kategori/', '?paged=']):
                        full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
                        results.append({"baslik": title.strip().upper(), "url": full_link})
                        found_count += 1
                
                print(f"    + {found_count} içerik eklendi.")
                if found_count < 10: break # Sayfa tam dolu değilse son sayfadır
                time.sleep(1)
            else:
                break
        except:
            break
            
    return results

def main():
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Sürüm Yükseltildi: {new_v}")

    # Daha geniş koleksiyon listesi
    categories = ["exxen", "netflix", "gain", "disney", "blutv", "belgesel", "film-arsivi", "yabanci-diziler"]
    final_data = []
    
    for cat in categories:
        final_data.extend(scrape_category_pages(cat))

    # Tekilleştirme
    unique_data = {item['url']: item for item in final_data}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique_data), f, ensure_ascii=False, indent=4)

    print(f"\n--- İŞLEM TAMAMLANDI ---")
    print(f"Toplam {len(unique_data)} benzersiz içerik dev arşive eklendi!")

if __name__ == "__main__":
    main()
