import requests
import re
import os
import json
import time
from urllib.parse import quote

# Dosya Yolları
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
PROXY = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': f'{BASE_URL}/'
    }

def main():
    print(">>> Arama Motoru Üzerinden Sızma Başlatıldı...")
    
    # 1. Versiyon Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))

    results = []
    # Alfabedeki harfleri kullanarak her şeyi ara (En etkili yöntem budur)
    search_queries = ['a', 'e', 'i', 'o', 'u', 'b', 'c', 'd'] 

    for q in search_queries:
        print(f"  - '{q}' harfi ile içerikler aranıyor...")
        # Arama URL'si: ?s=harf
        target = f"{BASE_URL}/?s={q}"
        proxied_url = PROXY + quote(target)
        
        try:
            res = requests.get(proxied_url, headers=get_headers(), timeout=30)
            html = res.text
            
            # Senin "çekiyordu" dediğin regex mantığına en yakın yapı
            # Link ve Başlığı ayıkla
            items = re.findall(r'href="(https://www.dizipal1226.com/[^/"]+/)"[^>]*>(.*?)</a>', html)
            
            found_count = 0
            for href, content in items:
                # Başlığı temizle (HTML taglarını sil)
                title = re.sub('<[^<]+?>', '', content).strip().upper()
                
                # Gereksiz linkleri temizle
                bad_words = ['kategori', 'etiket', 'page', 'iletisim', 'dmca', 'yorum', 'kayit']
                if len(title) > 3 and not any(w in href for w in bad_words):
                    results.append({"baslik": title, "url": href})
                    found_count += 1
            
            print(f"    + {found_count} içerik bulundu.")
            time.sleep(2) # Korumaya yakalanmamak için bekle
            
        except Exception as e:
            print(f"    ! Hata: {e}")

    # Tekilleştirme
    unique_data = []
    seen = set()
    for item in results:
        if item['url'] not in seen:
            unique_data.append(item)
            seen.add(item['url'])

    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"\nSonuç: {len(unique_data)} benzersiz içerik kaydedildi.")

if __name__ == "__main__":
    main()
