import requests
import re
import os
import json
import sys

# BeautifulSoup kontrolü
try:
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit(1)

KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"
PROXY_BASE = "https://api.codetabs.com/v1/proxy/?quest="

def get_headers():
    return {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'}

def main():
    target_url = "https://www.dizipal1226.com"
    sitemap_url = f"{target_url}/sitemap.xml"
    
    print(f"Site Haritası taranıyor: {sitemap_url}")
    
    try:
        # Proxy üzerinden sitemap'i çek
        res = requests.get(f"{PROXY_BASE}{sitemap_url}", headers=get_headers(), timeout=30)
        
        # Eğer sitemap.xml yoksa sitemap_index.xml veya post-sitemap.xml dene
        if res.status_code != 200:
            print("Standart sitemap bulunamadı, alternatif deneniyor...")
            res = requests.get(f"{PROXY_BASE}{target_url}/post-sitemap.xml", headers=get_headers(), timeout=30)

        # Linkleri ayıkla (Regex ile en hızlı çözüm)
        # <loc>https://.../dizi-adi</loc> yapısını yakalar
        all_links = re.findall(r'<loc>(.*?)</loc>', res.text)
        print(f"Sitemap içerisinde {len(all_links)} toplam link bulundu.")

        results = []
        for link in all_links:
            # Filtreleme: Sadece içerik linklerini al (Kategori, etiket ve ana sayfayı ele)
            if any(x in link for x in ['/kategori/', '/etiket/', '/page/', 'sitemap', target_url + '/$']):
                continue
            
            # Linkten başlık türet (URL'deki son kısmı al ve temizle)
            slug = link.rstrip('/').split('/')[-1]
            title = slug.replace('-', ' ').title()
            
            if len(title) > 3:
                results.append({"baslik": title, "url": link})

        # Tekilleştirme
        unique_results = []
        seen = set()
        for item in results:
            if item['url'] not in seen:
                unique_results.append(item)
                seen.add(item['url'])

        # JSON Kaydet
        with open('diziler.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)
        
        print(f"İşlem Başarılı! {len(unique_results)} içerik sitemap üzerinden çekildi.")

        # --- Dosya Güncellemeleri ---
        if len(unique_results) > 0:
            if os.path.exists(KT_PATH):
                with open(KT_PATH, 'r', encoding='utf-8') as f: content = f.read()
                new_content = re.sub(r'override var mainUrl = ".*?"', f'override var mainUrl = "{target_url}"', content)
                with open(KT_PATH, 'w', encoding='utf-8') as f: f.write(new_content)
                print("Kotlin güncellendi.")

            if os.path.exists(GRADLE_PATH):
                with open(GRADLE_PATH, 'r', encoding='utf-8') as f: g_content = f.read()
                v_match = re.search(r'version\s*=\s*(\d+)', g_content)
                if v_match:
                    new_v = int(v_match.group(1)) + 1
                    new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', g_content)
                    with open(GRADLE_PATH, 'w', encoding='utf-8') as f: f.write(new_g)
                    print(f"Versiyon: {new_v}")

    except Exception as e:
        print(f"Sitemap hatası: {e}")

if __name__ == "__main__":
    main()
