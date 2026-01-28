import requests
import re
import os
import json
import time

# Dosya Yolları
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Referer': f'{BASE_URL}/'
    }

def brute_scrape(path_suffix):
    results = []
    print(f"\n>>> {path_suffix.upper()} taranıyor...")
    
    # İlk 5 sayfayı brute-force tara (Her sayfa ~20-30 içerik)
    for p in range(1, 6):
        target = f"{BASE_URL}/{path_suffix}/page/{p}/"
        if p == 1: target = f"{BASE_URL}/{path_suffix}/"
        
        print(f"  - Sayfa {p} zorlanıyor: {target}")
        
        try:
            # Proxy'siz doğrudan dene (GitHub Actions bazen direkt erişebilir)
            # Eğer hata alırsak Proxy'yi buraya tekrar ekleyebiliriz
            res = requests.get(target, headers=get_headers(), timeout=20)
            res.encoding = 'utf-8'
            html = res.text

            # En kaba regex: Site içindeki tüm /dizi/ veya /film/ linklerini yakala
            # Kalıp: href="https://.../dizi-adi" >Dizi Adı<
            links = re.findall(r'href="([^"]+)"[^>]*>([^<]+)</a>', html)
            
            found_this_page = 0
            for href, title in links:
                title = title.strip().upper()
                # Filtre: Gereksiz sayfaları (kategori, sayfa, reklam) ele
                if len(title) > 3 and BASE_URL in href:
                    if not any(x in href.lower() for x in ['kategori', 'etiket', 'page/', 'iletisim', 'dmca']):
                        results.append({"baslik": title, "url": href})
                        found_this_page += 1
            
            print(f"    + {found_this_page} içerik bulundu.")
            if found_this_page == 0: break
            time.sleep(1)
            
        except Exception as e:
            print(f"    ! Hata: {e}")
            break
            
    return results

def main():
    # 1. Versiyonu artır
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Sürüm: {new_v}")

    # 2. Ana bölümleri tara (Koleksiyon yerine doğrudan diziler/filmler)
    all_content = []
    sections = ["diziler", "filmler", "koleksiyon/exxen", "koleksiyon/netflix"]
    
    for s in sections:
        all_content.extend(brute_scrape(s))

    # 3. Tekilleştirme
    unique_list = []
    seen = set()
    for item in all_content:
        if item['url'] not in seen:
            unique_list.append(item)
            seen.add(item['url'])

    # 4. Kaydet
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=4)

    print(f"\nSonuç: {len(unique_list)} içerik kaydedildi.")

if __name__ == "__main__":
    main()
