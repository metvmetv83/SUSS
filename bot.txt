import requests
from bs4 import BeautifulSoup
import json
import os

def get_data():
    target_url = "https://dizipal.cx/filmler/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(target_url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        items = soup.find_all('div', class_='post-item')
        results = []
        
        for item in items:
            link_tag = item.find('a')
            img_tag = item.find('img')
            
            if link_tag:
                title = link_tag.get('title', '')
                url = link_tag.get('href', '')
                # data-src varsa onu al, yoksa src al
                img = img_tag.get('data-src') or img_tag.get('src', '')
                
                results.append({
                    "baslik": title,
                    "url": url,
                    "afis": img
                })
        
        # JSON dosyasına kaydet
        with open('filmler.json', 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=4)
            
        print("Veri başarıyla güncellendi!")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    get_data()
