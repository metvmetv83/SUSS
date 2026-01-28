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
        'X-Requested-With': 'XMLHttpRequest' # Butonun yaptığı isteği taklit etmek için kritik
    }

def clean_text(text):
    try:
        text = text.encode('latin-1').decode('utf-8')
    except: pass
    clean = re.split(r'\d+\. Sezon|Henüz|Kişi|\d+ hafta|\d+ ay|imdb|IMDB', text, flags=re.IGNORECASE)[0]
    return clean.strip()

def scrape_with_infinite_load(base_url, endpoint):
    """'Daha Fazla Göster' mantığını taklit ederek tüm sayfaları tarar."""
    all_results = []
    print(f"\n>>> {endpoint.upper()} taranıyor...")

    # Load More butonları genellikle sayfa sayısını parametre olarak alır
    # 1'den başla ve içerik gelmeyene kadar devam et
    for page in range(1, 15): # İlk 15 sayfayı (yaklaşık 450-500 içerik) tara
        target = f"{base_url.rstrip('/')}/{endpoint.lstrip('/')}/page/{page}/"
        
        try:
            proxy_url = f"{PROXY_BASE}{target}"
            print(f"Sayfa {page} yükleniyor...")
            res = requests.get(proxy_url, headers=get_headers(), timeout=30)
            res.encoding = 'utf-8'
            
            if res.status_code != 200 or len(res.text) < 2000:
                print(f"Daha fazla içerik kalmadı (Sayfa {page}).")
                break
            
            soup = BeautifulSoup(res.text, 'html.parser')
            page_items = 0
            
            for a in soup.find_all('a', href=True):
                href = a['href']
                title = clean_text(a.get_text(strip=True))
                
                # Filtrele: Sadece dizi/film linki olabilecekleri seç
                bad_keywords = ['kategori', 'koleksiyon', 'forum', 'iletisim', 'giris', 'page/']
                if len(title) > 3 and not any(x in href.lower() for x in bad_keywords):
                    full_link = href if href.startswith('http') else f"{base_url.rstrip('/')}/{href.lstrip('/')}"
                    all_results.append({"baslik": title, "url": full_link, "tip": endpoint})
                    page_items += 1
            
            print(f"Sayfa {page}: {page_items} içerik eklendi.")
            if page_items == 0: break
            time.sleep(1) # Ban yememek için

        except Exception as e:
            print(f"Hata: {e}")
            break
            
    return all_results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # 1. Versiyon ve URL Güncelleme
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

    # 2. Infinite Load Tarama
    full_list = []
    full_list.extend(scrape_with_infinite_load(target_url, "diziler"))
    full_list.extend(scrape_with_infinite_load(target_url, "filmler"))

    # Tekrar edenleri temizle
    unique_data = []
    seen = set()
    for item in full_list:
        if item['baslik'].lower() not in seen:
            unique_data.append(item)
            seen.add(item['baslik'].lower())

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"\nİşlem Tamamlandı: {len(unique_data)} içerik dev arşive eklendi!")

if __name__ == "__main__":
    main()
