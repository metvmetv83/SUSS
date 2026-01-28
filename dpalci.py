import requests
import re
import os
import json
import sys

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("HATA: beautifulsoup4 kütüphanesi eksik.")
    sys.exit(1)

KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.8,en-US;q=0.5,en;q=0.3',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    }

def fetch_series(url):
    """Gelişmiş seçiciler ve genişletilmiş tarama ile dizi çekme."""
    try:
        print(f"Veriler çekiliyor: {url}")
        session = requests.Session()
        res = session.get(url, headers=get_headers(), timeout=20)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        results = []
        
        # 1. YÖNTEM: Spesifik Link Yapılarını tara (Genelde en garantisidir)
        # Sitedeki tüm linkleri alıp içinde 'dizi', 'film' veya 'izle' geçenleri filtreleyelim
        for a in soup.find_all('a', href=True):
            title = a.get_text(strip=True)
            href = a['href']
            
            # Link bir dizi/izleme linki gibi görünüyorsa ve başlık varsa al
            if len(title) > 5 and working_url in href and not any(x in href for x in ['/category/', '/etiket/', '/page/']):
                results.append({"baslik": title, "url": href})

        # 2. YÖNTEM: Klasik Seçiciler (Yedek olarak)
        selectors = ['h2 a', 'h3 a', '.post-title a', '.entry-title a', '.video-title a']
        for sel in selectors:
            for item in soup.select(sel):
                t = item.get_text(strip=True)
                h = item.get('href')
                if t and h:
                    results.append({"baslik": t, "url": h})

        # Tekilleştirme
        unique_results = []
        seen = set()
        for item in results:
            if item['baslik'] not in seen:
                unique_results.append(item)
                seen.add(item['baslik'])
        
        # Sonuçları Kaydet
        with open('diziler.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)
        
        print(f"İşlem başarılı: {len(unique_results)} içerik kaydedildi.")
        
        # Eğer hala 0 ise sayfa yapısını debug etmek için log basalım
        if len(unique_results) == 0:
            print("Uyarı: Sayfa okundu ama dizi bulunamadı. HTML boyutu:", len(res.text))

    except Exception as e:
        print(f"Scraping hatası: {e}")

def check_url(url):
    try:
        r = requests.get(url, headers=get_headers(), timeout=15, allow_redirects=True)
        return r.url.rstrip('/') if r.status_code < 400 else None
    except:
        return None

def main():
    global working_url
    input_url = "https://www.dizipal1226.com"
    working_url = check_url(input_url)

    if working_url:
        print(f"Aktif URL: {working_url}")
        
        # Dosya Güncellemeleri
        if os.path.exists(KT_PATH):
            with open(KT_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            new_content = re.sub(r'mainUrl\s*=\s*".*?"', f'mainUrl = "{working_url}"', content)
            with open(KT_PATH, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Güncellendi: {KT_PATH}")

        if os.path.exists(GRADLE_PATH):
            with open(GRADLE_PATH, 'r', encoding='utf-8') as f:
                g_content = f.read()
            v_match = re.search(r'version\s*=\s*(\d+)', g_content)
            if v_match:
                new_v = int(v_match.group(1)) + 1
                new_g = re.sub(r'version\s*=\s*\d+', f'version = {new_v}', g_content)
                with open(GRADLE_PATH, 'w', encoding='utf-8') as f:
                    f.write(new_g)
                print(f"Sürüm yükseltildi: {new_v}")
        
        fetch_series(working_url)
    else:
        print("Çalışan URL bulunamadı.")
        sys.exit(1)

if __name__ == "__main__":
    main()
