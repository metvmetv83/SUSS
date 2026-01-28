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
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

def scrape_category_pages(category):
    results = []
    print(f"\n>>> {category.upper()} Arşivi Taranıyor...")

    # Her kategori için ilk 5 sayfayı tara (Toplam ~100 içerik per kategori)
    for p in range(1, 6):
        if p == 1:
            target = f"{BASE_URL}/koleksiyon/{category}"
        else:
            target = f"{BASE_URL}/koleksiyon/{category}/page/{p}/"
        
        print(f"  - Sayfa {p} yükleniyor...")
        
        try:
            url = PROXY_BASE + quote(target)
            # Timeout süresini 40 saniyeye çıkardık
            res = requests.get(url, headers=get_headers(), timeout=40)
            
            if res.status_code == 200:
                data = res.json()
                html = data.get('contents', '')
                
                # İçerik yakalama (Link ve Başlık)
                items = re.findall(r'href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
                
                if not items:
                    print(f"    ! Sayfa {p} boş döndü veya içerik bitti.")
                    break
                
                found_count = 0
                for href, title in items:
                    # Sadece dizi linklerini al (gereksiz sayfaları süz)
                    if not any(x in href for x in ['/page/', '/kategori/']):
                        full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
                        results.append({"baslik": title.strip().upper(), "url": full_link})
                        found_count += 1
                
                print(f"    + {found_count} içerik eklendi.")
                time.sleep(1) # Sunucuyu yormayalım
            else:
                break
        except Exception as e:
            print(f"    ! Sayfa {p} hatası: {e}")
            break
            
    return results

def main():
    # Sürüm Güncelleme
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Yeni Sürüm Hazırlanıyor: {new_v}")

    # Koleksiyon listesi
    categories = ["exxen", "netflix", "gain", "disney", "blutv", "beindizi"]
    final_data = []
    
    for cat in categories:
        final_data.extend(scrape_category_pages(cat))

    # Tekilleştirme
    unique_data = []
    seen = set()
    for item in final_data:
        if item['url'] not in seen:
            unique_data.append(item)
            seen.add(item['url'])

    # JSON Kaydet
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"\n--- İŞLEM TAMAMLANDI ---")
    print(f"Toplam {len(unique_data)} içerik dev arşive eklendi!")

if __name__ == "__main__":
    main()
