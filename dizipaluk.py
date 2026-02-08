import cloudscraper
import json
import re

def main():
    # Cloudflare bypass özellikli scraper
    scraper = cloudscraper.create_scraper()
    
    url = "https://dizipal.uk/filmler/"
    print(f"🔍 Tarama başlıyor: {url}")
    
    response = scraper.get(url)
    
    if response.status_code == 200:
        html = response.text
        # Regex ile film linklerini ve başlıklarını yakala
        # div.post-item içindeki a href ve title'ları arıyoruz
        pattern = r'<div[^>]*class="[^"]*post-item[^"]*"[^>]*>.*?<a[^>]*href="([^"]+)"[^>]*title="([^"]+)"'
        matches = re.findall(pattern, html, re.DOTALL)
        
        movies = []
        for url, title in matches:
            movies.append({
                "title": title.strip(),
                "url": url.strip()
            })
        
        # Veriyi kaydet
        with open("filmler.json", "w", encoding="utf-8") as f:
            json.dump(movies, f, ensure_ascii=False, indent=4)
        
        print(f"✅ Başarılı: {len(movies)} film kaydedildi.")
    else:
        print(f"❌ Hata: Kod {response.status_code}")

if __name__ == "__main__":
    main()
