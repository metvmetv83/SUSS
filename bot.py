import requests
from bs4 import BeautifulSoup
import json

def scrape_dizipal():
    # 1. YÖNTEM: AllOrigins Proxy (Daha stabil)
    # Eğer bu çalışmazsa 2. yöntemi (CodeTabs) deneyebilirsin.
    target_url = "https://dizipal.cx/filmler/"
    proxy_url = f"https://api.allorigins.win/raw?url={target_url}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    }

    try:
        print(f"Proxy üzerinden bağlanılıyor: {proxy_url}")
        # Proxy üzerinden GET isteği atıyoruz
        response = requests.get(proxy_url, headers=headers, timeout=30)
        
        # Eğer AllOrigins hata verirse CodeTabs proxy'sini dene
        if response.status_code != 200:
            print("AllOrigins başarısız oldu, CodeTabs deneniyor...")
            proxy_url = f"https://api.codetabs.com/v1/proxy/?quest={target_url}"
            response = requests.get(proxy_url, headers=headers, timeout=30)

        if response.status_code == 200:
            html_content = response.text
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # HTML yapısını analiz et (Gönderdiğin HTML'e göre)
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

            if len(results) > 0:
                with open('filmler.json', 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=4)
                print(f"BAŞARI! {len(results)} film proxy ile çekildi.")
            else:
                print("Hata: Sayfa çekildi ama film kutuları (post-item) bulunamadı.")
                # Hata ayıklama için sayfanın ilk 500 karakterini yazdıralım
                print("Sayfa içeriği (ilk 500):", html_content[:500])
        else:
            print(f"Proxy de başarısız oldu. Durum kodu: {response.status_code}")

    except Exception as e:
        print(f"Bağlantı hatası: {e}")

if __name__ == "__main__":
    scrape_dizipal()
