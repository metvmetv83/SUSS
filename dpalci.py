import requests
import re
import os
import json
import sys
from bs4 import BeautifulSoup

# DOSYA YOLLARI
KT_PATH = "DiziPal/src/main/kotlin/com/Pitipitii/DiziPal.kt"
GRADLE_PATH = "DiziPal/build.gradle.kts"

def get_headers():
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Referer': 'https://www.google.com/'
    }

def check_url(url):
    try:
        print(f"Kontrol ediliyor: {url}")
        # allow_redirects=True sayesinde dizipal.com'dan .uk'ye geçişleri takip eder
        response = requests.get(url, headers=get_headers(), timeout=15, allow_redirects=True)
        if response.status_code < 400:
            return response.url.rstrip('/')
        return None
    except Exception as e:
        print(f"Bağlantı hatası: {e}")
        return None

def fetch_series(url):
    """Sitedeki son eklenen dizi ve filmleri çeker."""
    try:
        print(f"Dizi listesi alınıyor: {url}")
        res = requests.get(url, headers=get_headers(), timeout=15)
        soup = BeautifulSoup(res.text, 'html.parser')
        
        results = []
        # Dizipal genellikle 'article' etiketleri veya belirli class'lar kullanır
        # En yaygın seçicileri ekledim
        items = soup.select('article h2 a, .post-title a, .entry-title a')
        
        for link in items:
            title = link.get_text(strip=True)
            href = link.get('href')
            if title and href:
                results.append({"baslik": title, "url": href})
        
        # Sadece benzersiz olanları tut (Tekrarı engelle)
        unique_results = [dict(t) for t in {tuple(d.items()) for d in results}]
        
        with open('diziler.json', 'w', encoding='utf-8') as f:
            json.dump(unique_results, f, ensure_ascii=False, indent=4)
        
        print(f"İşlem başarılı: {len(unique_results)} dizi diziler.json dosyasına yazıldı.")
    except Exception as e:
        print(f"Veri çekme hatası: {e}")

def main():
    # 1. Mevcut adresi doğrula (Senin verdiğin adres)
    input_url = "https://www.dizipal1226.com" 
    working_url = check_url(input_url)

    if not working_url:
        print("Verilen URL'ye ulaşılamadı. Alternatif aranıyor...")
        # Eğer verdiğin link de kapandıysa brute-force (1226 -> 1227...)
        base_num = 1226
        for i in range(base_num, base_num + 10):
            test_url = f"https://dizipal{i}.com"
            working_url = check_url(test_url)
            if working_url: break

    if working_url:
        print(f"Aktif Adres: {working_url}")
        
        # 2. Kotlin Dosyasını Güncelle
        if os.path.exists(KT_PATH):
            with open(KT_PATH, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Eski URL'yi bul ve yenisiyle değiştir
            updated_content = re.sub(r'mainUrl\s*=\s*".*?"', f'mainUrl = "{working_url}"', content)
            
            with open(KT_PATH, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            print("Kotlin dosyası güncellendi.")

        # 3. Gradle Versiyon Artırımı
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

        # 4. Dizileri Çek
        fetch_series(working_url)
    else:
        print("Maalesef çalışan bir adres bulunamadı.")
        sys.exit(1)

if __name__ == "__main__":
    main()
