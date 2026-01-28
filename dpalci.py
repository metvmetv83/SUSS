import requests
import re
import os
import json
import sys
import time
from urllib.parse import quote

# Dosya Yolları
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.dizipal1226.com/'
    }

def scrape_titan_logic(base_url, category):
    """Paylaştığın Titan TV PHP mantığını kullanarak link toplar."""
    results = []
    # DiziPal'da koleksiyonlar çok zengin içerik barındırır
    target = f"{base_url}/koleksiyon/{category}"
    print(f"\n>>> KOLEKSİYON Taranıyor: {category}")
    
    try:
        # Proxy üzerinden veri çek
        encoded_url = quote(target)
        res = requests.get(f"{PROXY_BASE}{encoded_url}", headers=get_headers(), timeout=30)
        res.encoding = 'utf-8'
        html = res.text

        # PHP kodundaki preg_match_all mantığı (Regex)
        # 1. Önce li bloklarını yakala
        items = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL | re.IGNORECASE)
        print(f"Blok Analizi: {len(items)} potansiyel içerik bulundu.")

        for item in items:
            # 2. Blok içindeki Link, Başlık ve Resim bilgilerini ayıkla
            m_link = re.search(r'href="([^"]+)"', item, re.IGNORECASE)
            m_title = re.search(r'class="title">([^<]+)</span>', item, re.IGNORECASE)
            
            if m_link and m_title:
                link = m_link.group(1)
                title = m_title.group(1).strip()
                
                # Linki tam adrese çevir
                full_link = link if link.startswith('http') else f"{base_url.rstrip('/')}/{link.lstrip('/')}"
                
                if len(title) > 2:
                    results.append({
                        "baslik": title.upper(),
                        "url": full_link,
                        "kategori": category
                    })

    except Exception as e:
        print(f"Hata oluştu ({category}): {e}")
        
    return results

def main():
    target_url = "https://www.dizipal1226.com"
    
    # 1. Versiyon Güncelleme
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            new_c = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content)
            with open(GRADLE_PATH, 'w') as f: f.write(new_c)
            print(f"Yeni Sürüm: {new_v}")

    # 2. Veri Toplama (Popüler Koleksiyonlar)
    koleksiyonlar = ["exxen", "netflix", "gain", "disney", "beindizi", "diziler", "filmler"]
    all_extracted = []
    
    for kol in koleksiyonlar:
        extracted = scrape_titan_logic(target_url, kol)
        all_extracted.extend(extracted)
        time.sleep(1) # Ban koruması

    # 3. Tekilleştirme
    unique_data = []
    seen = set()
    for item in all_extracted:
        if item['url'] not in seen:
            unique_data.append(item)
            seen.add(item['url'])

    # 4. JSON Yazma
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_data, f, ensure_ascii=False, indent=4)

    print(f"\nİşlem Tamamlandı: Toplam {len(unique_data)} içerik çekildi.")

if __name__ == "__main__":
    main()
