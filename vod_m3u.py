import requests
import os
import json
import concurrent.futures
from datetime import datetime
import sys

# === KULLANICININ GİRMESİ GEREKEN ===
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjMwYTM5YzllLWE4ZDYtNGEwMC05NDBmLTFjMTE4NDgzZDcxMiIsInNnZCI6ImJkNmUyNmY5LWJkMzYtNDE2ZC05YWQzLTYzNjhlNGZkYTMyMiIsInNwZ2QiOiJjYjZmZGMwMi1iOGJlLTQ3MTYtYTZjYi1iZTEyYTg4YjdmMDkiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NTE3MDMxODQsImV4cCI6MTc1MTcwMzI0NCwiaWF0IjoxNzUxNzAzMTg0fQ.SGC_FfT7cU1RVM4E5rMYO2IsA4aYUoYq2SXl51-PZwM"
OUTPUT_M3U = "vodden.m3u"
VOD_ID_FILE = "vod_ids.txt"

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com"
}

def load_vod_ids(filename):
    """VOD ID'lerini hızlı yükle"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip().split("/")[-1] for line in f if line.strip()]
    except:
        return []

def get_film_detail_batch(vod_ids):
    """Tek seferde çoklu film detayı al"""
    url = "https://core-api.kablowebtv.com/api/vod/detail-batch"
    
    try:
        payload = {"VodUIds": vod_ids}
        res = requests.post(url, headers=HEADERS, json=payload, timeout=30)
        
        if res.status_code == 200:
            data = res.json()
            if data.get("IsSucceeded"):
                return data.get("Data", [])
        return []
    except:
        return []

def get_film_detail_single(vod_id):
    """Tek film detayı al (paralel çalışma için)"""
    url = "https://core-api.kablowebtv.com/api/vod/detail"
    
    try:
        res = requests.get(url, headers=HEADERS, params={"VodUId": vod_id}, timeout=10)
        if res.status_code == 200:
            data = res.json()
            if data.get("IsSucceeded") and data.get("Data"):
                return data["Data"][0]
    except:
        pass
    return None

def get_films_fast(vod_ids, batch_size=20):
    """Hızlı film çekme - batch ve paralel"""
    all_films = []
    
    print(f"[→] Batch modunda {len(vod_ids)} film çekiliyor...")
    
    # Önce batch API'yi dene
    if len(vod_ids) <= 50:  # Küçük listeler için batch
        batch_result = get_film_detail_batch(vod_ids)
        if batch_result:
            print(f"[✓] Batch API ile {len(batch_result)} film alındı")
            return batch_result
    
    # Batch yoksa paralel çek
    print("[→] Paralel çekim başlıyor...")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        # Tüm istekleri gönder
        future_to_id = {executor.submit(get_film_detail_single, vid): vid for vid in vod_ids}
        
        # Sonuçları topla
        completed = 0
        for future in concurrent.futures.as_completed(future_to_id):
            completed += 1
            film = future.result()
            if film:
                all_films.append(film)
            
            # İlerleme çubuğu
            if completed % 10 == 0 or completed == len(vod_ids):
                sys.stdout.write(f"\r[→] {completed}/{len(vod_ids)} film alındı")
                sys.stdout.flush()
    
    print()  # Yeni satır
    return all_films

def write_m3u_fast(films):
    """Hızlı M3U yazma"""
    if not films:
        return 0
    
    valid_count = 0
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for film in films:
            title = film.get("Title", "Bilinmeyen")
            uid = film.get("UId", "")
            
            # Logo
            logo = ""
            for poster in film.get("Posters", []):
                if poster.get("Type", "").lower() == "listing":
                    logo = poster.get("ImageUrl", "")
                    break
            
            # Stream
            stream = film.get("StreamData", {})
            mpd = stream.get("DashStreamUrl")
            is_drm = stream.get("IsDrmEnabled", True)
            
            if mpd and not is_drm:
                # Kategori
                categories = film.get("Categories", [])
                genre = "VOD"
                if categories:
                    genre = categories[0].get("Name", "VOD") if isinstance(categories[0], dict) else str(categories[0])
                
                f.write(f'#EXTINF:-1 tvg-id="{uid}" tvg-logo="{logo}" group-title="{genre}",{title}\n')
                f.write(f'{mpd}\n')
                valid_count += 1
    
    return valid_count

def main():
    print("=" * 40)
    print("⚡ HIZLI VOD ÇEKME ARACI")
    print("=" * 40)
    
    # ID'leri yükle
    vod_ids = load_vod_ids(VOD_ID_FILE)
    if not vod_ids:
        print("[!] vod_ids.txt dosyasına VOD ID'leri yazın!")
        print("    Örnek: 0c38309b-3e7d-426e-b6e5-0316b61ae8f6")
        return
    
    print(f"[✓] {len(vod_ids)} film ID'si yüklendi")
    
    # Filmleri çek
    start_time = datetime.now()
    films = get_films_fast(vod_ids)
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"[✓] {len(films)} film {elapsed:.1f} saniyede alındı")
    
    # M3U'ya yaz
    valid_count = write_m3u_fast(films)
    
    # Sonuç
    print("\n" + "=" * 40)
    print("SONUÇ:")
    print(f"  • Toplam ID: {len(vod_ids)}")
    print(f"  • Bulunan film: {len(films)}")
    print(f"  • M3U'ya yazılan: {valid_count}")
    print(f"  • Süre: {elapsed:.1f} saniye")
    print(f"  • Dosya: {OUTPUT_M3U}")
    
    # Test için birkaç film göster
    if films:
        print("\n📺 İlk 5 film:")
        for i, film in enumerate(films[:5]):
            title = film.get("Title", "Bilinmeyen")
            stream = film.get("StreamData", {})
            has_mpd = "✓" if stream.get("DashStreamUrl") else "✗"
            is_drm = "DRM" if stream.get("IsDrmEnabled") else "DRM Yok"
            print(f"  {i+1}. {title[:40]}... [{has_mpd} {is_drm}]")

if __name__ == "__main__":
    main()
