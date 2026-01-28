import requests
import re
import os
import json
import time
from urllib.parse import quote

# Dosya Yolları
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
# Farklı bir proxy motoru deniyoruz (AllOrigins alternatifi)
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Cache-Control': 'no-cache',
        'Pragma': 'no-cache',
        'Referer': 'https://www.google.com/'
    }

def scrape_smart(path):
    results = []
    print(f"\n>>> {path.upper()} taranıyor...")
    
    # Sitenin korumasını aşmak için URL'yi encode ediyoruz
    target_url = f"{BASE_URL}/{path}/" if path else f"{BASE_URL}/"
    proxied_url = PROXY_BASE + quote(target_url)
    
    try:
        res = requests.get(proxied_url, headers=get_headers(), timeout=30)
        res.encoding = 'utf-8'
        html = res.text
        
        # 1. Strateji: Makale bloklarını yakala (Daha garantidir)
        # <article ...> ... <h3 class="title"><a href="...">BAŞLIK</a></h3> ... </article>
        articles = re.findall(r'<article[^>]*>(.*?)</article>', html, re.DOTALL)
        
        if not articles:
            # 2. Strateji: Titan TV'nin kullandığı li yapısını yakala
            articles = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL)

        for block in articles:
            # Link ve Başlık ayıkla
            m_link = re.search(r'href="([^"]+)"', block)
            # Başlık bazen <h3> içinde bazen <span> içindedir
            m_title = re.search(r'class="title">([^<]+)<', block) or re.search(r'alt="([^"]+)"', block)
            
            if m_link and m_title:
                href = m_link.group(1)
                title = m_title.group(1).strip().upper()
                
                # Sadece gerçek dizi/film linklerini al
                if BASE_URL in href or href.startswith('/'):
                    full_link = href if href.startswith('http') else f"{BASE_URL}{href}"
                    if not any(x in href for x in ['kategori', 'etiket', 'page/']):
                        results.append({"baslik": title, "url": full_link})

        print(f"  - Bulunan: {len(results)}")
    except Exception as e:
        print(f"  - Hata: {e}")
        
    return results

def main():
    # Versiyon Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))

    # Tarama listesi
    targets = ["diziler", "filmler", "koleksiyon/exxen", "koleksiyon/netflix"]
    all_data = []
    
    for t in targets:
        all_data.extend(scrape_smart(t))
        time.sleep(2) # Korumayı aşmak için bekleme süresi

    # Tekilleştirme
    unique_data = []
    seen = set()
    for item in all_data:
        if item['url'] not in seen:
            unique_data.append(item)
            seen.add(item['url'])

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"\nSonuç: {len(unique_data)} içerik kaydedildi.")

if __name__ == "__main__":
    main()
