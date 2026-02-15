import cloudscraper
from bs4 import BeautifulSoup
import json

def scrape_dizipal():
    # Cloudflare'i aşmak için özel tarayıcı oluştur
    scraper = cloudscraper.create_scraper(
        browser={
            'browser': 'chrome',
            'platform': 'windows',
            'desktop': True
        }
    )
    
    target_url = "https://dizipal.cx/filmler/"
    
    try:
        print(f"Bypass denemesi yapılıyor: {target_url}")
        response = scraper.get(target_url, timeout=30)
        
        if response.status_code != 200:
            print(f"Hala engel var. Durum kodu: {response.status_code}")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        items = soup.find_all('div', class_='post-item')
        results = []

        for item in items:
            link_tag = item.find('a')
            img_tag = item.find('img')
            
            if link_tag:
                results.append({
                    "baslik": link_tag.get('title', ''),
                    "url": link_tag.get('href', ''),
                    "afis": img_tag.get('data-src') or img_tag.get('src') if img_tag else ""
                })

        with open('filmler.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        print(f"Başarı! {len(results)} film GitHub engeli aşılarak çekildi.")

    except Exception as e:
        print(f"Bypass hatası: {e}")

if __name__ == "__main__":
    scrape_dizipal()
