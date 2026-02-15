import requests
from bs4 import BeautifulSoup
import json
import time

def scrape_dizipal():
    # Sayfa URL'sini değişkene alıyoruz
    base_url = "https://dizipal.cx/filmler/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://dizipal.cx/"
    }

    try:
        print(f"Bağlanılıyor: {base_url}")
        response = requests.get(base_url, headers=headers, timeout=30)
        
        # Cloudflare kontrolü
        if "Güvenlik doğrulaması" in response.text or response.status_code == 403:
            print("Hata: Cloudflare engeline takıldı. GitHub IP'si şu an reddediliyor.")
            return

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Senin attığın HTML'deki ana yapı: post-item sınıfına sahip div'ler
        items = soup.find_all('div', class_='post-item')
        results = []

        print(f"Bulunan potansiyel kutu sayısı: {len(items)}")

        for item in items:
            # 1. Link ve Başlığı al (a etiketi içinden)
            link_tag = item.find('a')
            if not link_tag:
                continue
                
            film_url = link_tag.get('href', '')
            film_baslik = link_tag.get('title', '')

            # 2. Afişi al (img etiketi içinden)
            # Dizipal 'data-src', 'srcset' veya düz 'src' kullanıyor olabilir.
            img_tag = item.find('img')
            film_afis = ""
            if img_tag:
                # Öncelik sırasına göre resim linkini çekiyoruz
                film_afis = img_tag.get('data-src') or img_tag.get('src') or img_tag.get('srcset', '').split(' ')[0]

            # 3. Eğer link ve başlık varsa listeye ekle
            if film_url and film_baslik:
                # İstersen burada her film için detay sayfasına gidip 'embed' çekebilirsin 
                # ama başlangıç için önce listeyi dolduralım.
                results.append({
                    "baslik": film_baslik,
                    "url": film_url,
                    "afis": film_afis
                })

        # Sonuçları kaydet
        with open('filmler.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        print(f"Başarıyla {len(results)} film çekildi ve filmler.json dosyasına kaydedildi.")

    except Exception as e:
        print(f"Bir hata meydana geldi: {e}")

if __name__ == "__main__":
    scrape_dizipal()
