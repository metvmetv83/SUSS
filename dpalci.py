import requests
import re
import os
import json
from urllib.parse import quote

KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
PROXY = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

def scrape_collection_deep(category):
    all_found = []
    print(f"\n>>> {category.upper()} Koleksiyonu taranıyor...")
    
    # API POST çalışmıyorsa, sayfa yapısı üzerinden zorlayalım
    # DiziPal koleksiyonları genellikle /page/2/ şeklinde ilerleyebilir
    for page in range(1, 6): # İlk 5 sayfayı tara
        target = f"{BASE_URL}/koleksiyon/{category}/page/{page}/"
        if page == 1:
            target = f"{BASE_URL}/koleksiyon/{category}/"
            
        print(f"  - Sayfa {page} taranıyor...")
        
        try:
            # Proxy kullanarak GET isteği at
            url = PROXY + quote(target)
            res = requests.get(url, headers=get_headers(), timeout=25)
            html = res.text

            # PHP kodundaki preg_match_all mantığı: <li> bloklarını yakala
            items = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL | re.IGNORECASE)
            
            if not items:
                # Alternatif: li yoksa doğrudan a etiketlerini ara
                items = re.findall(r'<a[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', html, re.DOTALL)
                if not items: break
                
                page_count = 0
                for href, title in items:
                    full_url = href if href.startswith('http') else f"{BASE_URL}{href}"
                    all_found.append({"baslik": title.strip().upper(), "url": full_url})
                    page_count += 1
            else:
                page_count = 0
                for item in items:
                    m_link = re.search(r'href="([^"]+)"', item)
                    m_title = re.search(r'class="title">([^<]+)</span>', item)
                    
                    if m_link and m_title:
                        link = m_link.group(1)
                        title = m_title.group(1).strip().upper()
                        full_url = link if link.startswith('http') else f"{BASE_URL}{link}"
                        all_found.append({"baslik": title, "url": full_url})
                        page_count += 1
            
            print(f"    + {page_count} içerik çekildi.")
            if page_count < 10: break # Sayfa tam dolu değilse son sayfaya gelinmiştir
            
        except Exception as e:
            print(f"    ! Hata: {e}")
            break
            
    return all_found

def main():
    # 1. Versiyon Güncelle
    if os.path.exists(GRADLE_PATH):
        with open(GRADLE_PATH, 'r') as f: content = f.read()
        v = re.search(r'version\s*=\s*(\d+)', content)
        if v:
            new_v = int(v.group(1)) + 1
            with open(GRADLE_PATH, 'w') as f: 
                f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Versiyon: {new_v}")

    # 2. Kategorileri Tara
    final_list = []
    # Sitedeki en popüler koleksiyon isimleri
    cats = ["exxen", "netflix", "gain", "disney", "beindizi", "blutv"]
    
    for c in cats:
        final_list.extend(scrape_collection_deep(c))

    # 3. Tekilleştirme
    unique_results = []
    seen = set()
    for item in final_list:
        if item['url'] not in seen:
            unique_results.append(item)
            seen.add(item['url'])

    # 4. Kaydet
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(unique_results, f, ensure_ascii=False, indent=4)

    print(f"\nİşlem Tamamlandı: {len(unique_results)} benzersiz içerik kaydedildi.")

if __name__ == "__main__":
    main()
