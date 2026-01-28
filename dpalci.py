import requests
import re
import os
import json
import time
from urllib.parse import quote

# Ayarlar
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
BASE_URL = "https://www.dizipal1226.com"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'X-Requested-With': 'XMLHttpRequest',
        'Referer': f'{BASE_URL}/'
    }

def scrape_titan_deep(category):
    results = []
    session = requests.Session()
    last_id = "" # API için gerekli olan tarih ID'si
    
    print(f"\n>>> {category.upper()} Koleksiyonu Derin Taranıyor...")

    # 1. Aşama: İlk Sayfayı Çek (Senin çalışan mantığın)
    try:
        target = f"{BASE_URL}/koleksiyon/{category}"
        url = PROXY_BASE + quote(target)
        res = session.get(url, headers=get_headers(), timeout=30)
        html = res.text
        
        # İçerik ayıklama
        items = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL | re.IGNORECASE)
        for item in items:
            m_link = re.search(r'href="([^"]+)"', item)
            m_title = re.search(r'class="title">([^<]+)</span>', item)
            # API için gerekli olan 'id' (date) bilgisini a etiketinden çekiyoruz
            m_id = re.search(r'id="([^"]+)"', item) 
            
            if m_link and m_title:
                link = m_link.group(1)
                full_link = link if link.startswith('http') else f"{BASE_URL}{link}"
                results.append({"baslik": m_title.group(1).strip().upper(), "url": full_link})
                if m_id: last_id = m_id.group(1) # En son ID'yi güncelle

        print(f"  - İlk sayfa tamam: {len(results)} içerik.")

        # 2. Aşama: API ile "Daha Fazla" içerik çek (Derinleşme)
        # Sitenin API'si bazen proxy üzerinden POST kabul etmeyebilir, 
        # bu yüzden doğrudan siteye sağlam headerlar ile gidiyoruz.
        for p in range(1, 6): 
            if not last_id: break
            
            payload = {
                'date': last_id,
                'tur': category,
                'type': '', 'durum': '', 'kelime': '', 'siralama': ''
            }
            
            # API isteği (Direkt veya Proxy üzerinden denenebilir)
            api_url = f"{BASE_URL}/api/load-series"
            try:
                # Not: Proxy POST'u bozarsa burası boş döner. O zaman sadece ilk sayfaları alabiliriz.
                res = session.post(api_url, data=payload, headers=get_headers(), timeout=20)
                if res.status_code == 200:
                    ajax_data = res.json()
                    ajax_html = "".join(ajax_data) if isinstance(ajax_data, list) else str(ajax_data)
                    
                    new_items = re.findall(r'<a[^>]+id="([^"]+)"[^>]+href="([^"]+)"[^>]*>.*?class="title">([^<]+)</span>', ajax_html, re.DOTALL)
                    
                    if not new_items: break
                    
                    for n_id, n_href, n_title in new_items:
                        n_url = n_href if n_href.startswith('http') else f"{BASE_URL}{n_href}"
                        results.append({"baslik": n_title.strip().upper(), "url": n_url})
                        last_id = n_id # Bir sonraki tık için ID güncelle
                    
                    print(f"  - Kaydırma {p}: +{len(new_items)} yeni içerik.")
                    time.sleep(1)
                else:
                    break
            except:
                break

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
            with open(GRADLE_PATH, 'w') as f: 
                f.write(re.sub(r'version\s*=\s*\d+', f'version = {new_v}', content))
            print(f"Sürüm: {new_v}")

    # Koleksiyonlar
    kats = ["exxen", "netflix", "gain", "disney", "beindizi", "blutv"]
    all_data = []
    for k in kats:
        all_data.extend(scrape_titan_deep(k))

    # Tekilleştirme
    unique = {x['url']: x for x in all_data}.values()
    
    with open('diziler.json', 'w', encoding='utf-8') as f:
        json.dump(list(unique), f, ensure_ascii=False, indent=4)

    print(f"\nBitti! Toplam {len(unique)} benzersiz içerik kaydedildi.")

if __name__ == "__main__":
    main()
