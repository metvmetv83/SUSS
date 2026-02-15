import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_dizipal():
    base_url = "https://dizipal.cx/filmler/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Referer": "https://dizipal.cx/"
    }

    try:
        # 1. Sayfadaki filmleri listele
        response = requests.get(base_url, headers=headers, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = soup.find_all('div', class_='post-item')
        results = []

        for item in items:
            link_tag = item.find('a')
            img_tag = item.find('img')
            
            if link_tag:
                film_url = link_tag.get('href')
                film_baslik = link_tag.get('title')
                film_afis = img_tag.get('data-src') or img_tag.get('src')

                # 2. Film detayına git (Embed linkini çekmek için)
                # Not: Bu işlem süreyi uzatır, GitHub Actions için sorun değil.
                try:
                    time.sleep(1) # IP ban yememek için kısa bekleme
                    inner_res = requests.get(film_url, headers=headers, timeout=15)
                    inner_soup = BeautifulSoup(inner_res.text, 'html.parser')
                    
                    # Iframe/Embed bulma
                    iframe = inner_soup.find('iframe', src=True)
                    embed_url = iframe['src'] if iframe else ""
                except:
                    embed_url = ""

                results.append({
                    "baslik": film_baslik,
                    "url": film_url,
                    "afis": film_afis,
                    "embed": embed_url
                })
        
        # 3. Sonuçları JSON olarak kaydet
        with open('filmler.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        print(f"Başarıyla {len(results)} film çekildi ve kaydedildi.")

    except Exception as e:
        print(f"Hata: {e}")

if __name__ == "__main__":
    scrape_dizipal()
