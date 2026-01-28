import requests
import re
import os
import json
import sys

# BeautifulSoup'un yüklü olup olmadığını kontrol et
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("HATA: beautifulsoup4 kütüphanesi yüklü değil! YAML dosyanızda 'pip install beautifulsoup4' olduğundan emin olun.")
    sys.exit(1)

# AYARLAR - GitHub deponuzdaki dosya yolları
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7',
        'Referer': 'https://www.google.com/',
        'Cache-Control': 'no-cache',
    }

def check_url(url):
    """URL'yi kontrol eder ve yönlendirmeleri (Redirect) takip eder."""
    try:
        print(f"Kontrol ediliyor: {url}")
        response = requests.get(url, headers=get_headers(), timeout=15, allow_redirects=True)
        # Site sizi nereye yönlendirirse (örn: .uk) o adresi döndürür
        if response.status_code < 400:
            return response.url.rstrip('/')
        return None
    except Exception as e:
        print(f"Bağlantı hatası ({url}): {e}")
        return None

def fetch_series(url):
    """Sitedeki son eklenen dizi ve filmleri çeker."""
    try:
        print(f"Veriler çekiliyor: {url}")
        res = requests.get(url, headers=get_headers(), timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        results = []
        # DiziPal'ın kullandığı tüm muhtemel HTML yapıları
        selectors = [
            'article h2 a', 
            '.post-title a', 
            '.entry-title a', 
            '.video-block a', 
            '.list-title a'
        ]
        
        for selector in selectors:
            items = soup.select(selector)
            for link in items:
                title = link.get_text(strip=True)
                href = link.get('href')
                # Sadece gerçek dizi/film başlıklarını ve tam linkleri al
                if title and len(title) > 3 and href and href.startswith('http'):
                    results.append({"baslik": title, "url": href})
        
        # Benzersiz olanları filtrele (Aynı başlığı tekrar alma)
        unique_results = []
        seen = set()
        for item in results:
            if item['baslik'] not in seen:
                unique_results.append(item)
                seen.add(item['baslik'])
        
        with open('diziler.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)
        
        print(f"İşlem başarılı: {len(unique_results)} içerik diziler.json dosyasına kaydedildi.")
    except Exception as e:
        print(f"Scraping hatası: {e}")

def main():
    # 1. Başlangıç URL'si (Senin verdiğin çalışan adres)
    input_url = "https://www.dizipal1226.com"
    working_url = check_url(input_url)

    # Eğer verdiğin adres de çalışmıyorsa brute-force yap
    if not working_url:
        print("Verilen URL çalışmıyor, alternatifler deneniyor...")
        base_num = 1226
        for i in range(base_num, base_num + 10):
            test_url = f"https://dizipal{i}.com"
            working_url = check_url(test_url)
            if working_url:
                break

    if working_url:
        print(f"Aktif URL: {working_url}")
        
        # 2. Kotlin Dosyasını Güncelle
        if os.path.exists(KT_PATH):
            with open(KT_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Regex ile mainUrl satırını tamamen değiştirir
            new_content = re.sub(r'override var mainUrl = ".*?"', f'override var mainUrl = "{working_url}"', content)
            
            with open(KT_PATH, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"Güncellendi: {KT_PATH}")
        else:
            print(f"UYARI: {KT_PATH} dosyası bulunamadı, güncellenemedi.")

        # 3. Gradle Versiyonunu Artır
        if os.path.exists(GRADLE_PATH):
            with open(GRADLE_PATH, 'r', encoding='utf-8') as f:
                g_content = f.read()
            
            v_match = re.search(r'version\s*=\s*(\d+)', g_content)
            if v_match:
                old_v = v_match.group(1)
                new_v = str(int(old_v) + 1)
                new_g = g_content.replace(f"version = {old_v}", f"version = {new_v}")
                with open(GRADLE_PATH, 'w', encoding='utf-8') as f:
                    f.write(new_g)
                print(f"Sürüm yükseltildi: {new_v}")
        
        # 4. İçerikleri (Dizileri) Çek
        fetch_series(working_url)
        
    else:
        print("HATA: Hiçbir çalışan DiziPal adresi bulunamadı!")
        sys.exit(1)

if __name__ == "__main__":
    main()
