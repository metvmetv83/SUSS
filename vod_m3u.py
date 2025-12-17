import requests
import time
import os
import json
from datetime import datetime

# === KULLANICININ GİRMESİ GEREKEN ===
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbnYiOiJMSVZFIiwiaXBiIjoiMCIsImNnZCI6IjA5M2Q3MjBhLTUwMmMtNDFlZC1hODBmLTJiODE2OTg0ZmI5NSIsImNzaCI6IlRSS1NUIiwiZGN0IjoiM0VGNzUiLCJkaSI6IjMwYTM5YzllLWE4ZDYtNGEwMC05NDBmLTFjMTE4NDgzZDcxMiIsInNnZCI6ImJkNmUyNmY5LWJkMzYtNDE2ZC05YWQzLTYzNjhlNGZkYTMyMiIsInNwZ2QiOiJjYjZmZGMwMi1iOGJlLTQ3MTYtYTZjYi1iZTEyYTg4YjdmMDkiLCJpY2giOiIwIiwiaWRtIjoiMCIsImlhIjoiOjpmZmZmOjEwLjAuMC4yMDYiLCJhcHYiOiIxLjAuMCIsImFibiI6IjEwMDAiLCJuYmYiOjE3NTE3MDMxODQsImV4cCI6MTc1MTcwMzI0NCwiaWF0IjoxNzUxNzAzMTg0fQ.SGC_FfT7cU1RVM4E5rMYO2IsA4aYUoYq2SXl51-PZwM"
OUTPUT_M3U = "vodden.m3u"
VOD_ID_FILE = "vod_ids.txt"
LOG_FILE = "vod_log.json"  # Hata logu için

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
}

def check_token_expiry():
    """Token'in süresinin dolup dolmadığını kontrol et"""
    try:
        import jwt
        token = BEARER_TOKEN.replace("Bearer ", "")
        decoded = jwt.decode(token, options={"verify_signature": False})
        exp_timestamp = decoded.get('exp')
        if exp_timestamp:
            exp_date = datetime.fromtimestamp(exp_timestamp)
            now = datetime.now()
            if exp_date < now:
                print(f"[!] TOKEN SÜRESİ DOLMUŞ: {exp_date}")
                return False
            else:
                print(f"[✓] Token geçerli, süresi: {exp_date}")
                return True
    except Exception as e:
        print(f"[!] Token kontrol hatası: {e}")
    return True

def load_vod_ids(filename):
    """VOD ID'lerini yükle, farklı formatları destekle"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            ids = []
            for line in f:
                line = line.strip()
                if line:
                    # Sadece ID'yi al (URL'den veya tam satırdan)
                    if "vod/" in line:
                        # URL formatı: https://tvheryerde.com/vod/12345-abcde
                        parts = line.split("/")
                        if parts:
                            ids.append(parts[-1])
                    elif len(line) > 10:  # UID formatı kontrolü
                        ids.append(line)
            print(f"[✓] {len(ids)} VOD ID yüklendi")
            return ids
    except FileNotFoundError:
        print(f"[!] {filename} bulunamadı!")
        # Örnek ID'lerle devam et (test için)
        return ["0c38309b-3e7d-426e-b6e5-0316b61ae8f6", "8e94b70f-9f34-4aff-b7bd-9ce706884426"]
    except Exception as e:
        print(f"[!] Dosya okuma hatası: {e}")
        return []

def get_film_detail(vod_id):
    """Film detaylarını API'den al"""
    url = "https://core-api.kablowebtv.com/api/vod/detail"
    params = {"VodUId": vod_id}
    
    try:
        print(f"  → API isteği: {vod_id}")
        res = requests.get(url, headers=HEADERS, params=params, timeout=15)
        res.raise_for_status()
        
        data = res.json()
        
        if data.get("IsSucceeded"):
            if data.get("Data") and len(data["Data"]) > 0:
                film = data["Data"][0]
                title = film.get("Title", "Bilinmeyen")
                print(f"  ✓ Bulundu: {title}")
                return film
            else:
                print(f"  [!] Data boş: {vod_id}")
        else:
            print(f"  [!] API başarısız: {data.get('Message', 'Bilinmeyen hata')}")
            
    except requests.exceptions.Timeout:
        print(f"  [!] Timeout: {vod_id}")
    except requests.exceptions.RequestException as e:
        print(f"  [!] Network hatası: {vod_id} → {e}")
    except json.JSONDecodeError:
        print(f"  [!] JSON decode hatası: {vod_id}")
    except Exception as e:
        print(f"  [!] Beklenmeyen hata: {vod_id} → {type(e).__name__}: {e}")
    
    return None

def extract_stream_info(film):
    """Filmden stream bilgilerini çıkar"""
    if not film:
        return None, None, None, None
    
    title = film.get("Title", "Bilinmeyen")
    uid = film.get("UId", "")
    
    # Logo URL'sini bul
    logo = ""
    for poster in film.get("Posters", []):
        if poster.get("Type", "").lower() == "listing":
            logo = poster.get("ImageUrl", "")
            break
    
    # Stream bilgileri
    stream = film.get("StreamData", {})
    mpd = stream.get("DashStreamUrl")
    hls = stream.get("HlsStreamUrl")
    is_drm = stream.get("IsDrmEnabled", True)
    
    # Kategori/Genre
    categories = film.get("Categories", [])
    genre = "VOD"
    if categories and isinstance(categories, list) and len(categories) > 0:
        if isinstance(categories[0], dict):
            genre = categories[0].get("Name", "VOD")
        else:
            genre = str(categories[0])
    
    return title, uid, logo, mpd, hls, is_drm, genre

def write_m3u(films, output_file=OUTPUT_M3U):
    """Filmleri M3U formatında yaz"""
    if not films:
        print("[!] Yazılacak film bulunamadı!")
        return 0
    
    m3u_path = os.path.join(os.getcwd(), output_file)
    valid_count = 0
    
    with open(m3u_path, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for film in films:
            title, uid, logo, mpd, hls, is_drm, genre = extract_stream_info(film)
            
            # Stream URL'si seç (önce MPD, sonra HLS)
            stream_url = None
            if mpd and not is_drm:
                stream_url = mpd
                stream_type = "MPD"
            elif hls and not is_drm:
                stream_url = hls
                stream_type = "HLS"
            
            if stream_url:
                # M3U satırını yaz
                f.write(f'#EXTINF:-1 tvg-id="{uid}" tvg-name="{title}" tvg-logo="{logo}" group-title="{genre}",{title}\n')
                f.write(f'{stream_url}\n')
                valid_count += 1
                print(f"  ✓ Eklendi: {title} ({stream_type})")
            else:
                print(f"  [!] Atlanıyor: {title} (DRM veya stream yok)")
    
    print(f"[✓] {valid_count}/{len(films)} film yazıldı → {output_file}")
    return valid_count

def save_log(films, log_file=LOG_FILE):
    """Detaylı log kaydı"""
    log_data = {
        "timestamp": datetime.now().isoformat(),
        "total_films": len(films),
        "films": []
    }
    
    for film in films:
        title, uid, logo, mpd, hls, is_drm, genre = extract_stream_info(film)
        log_data["films"].append({
            "title": title,
            "id": uid,
            "logo": logo,
            "mpd_url": mpd,
            "hls_url": hls,
            "drm": is_drm,
            "genre": genre,
            "has_stream": bool(mpd or hls)
        })
    
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_data, f, indent=2, ensure_ascii=False)
    
    print(f"[✓] Log kaydedildi: {log_file}")

def main():
    print("=" * 50)
    print("VOD Film Çekme Aracı")
    print("=" * 50)
    
    # Token kontrolü
    if not check_token_expiry():
        print("[!] Lütfen yeni bir Bearer Token alın!")
        return
    
    # VOD ID'lerini yükle
    vod_ids = load_vod_ids(VOD_ID_FILE)
    if not vod_ids:
        print("[!] İşlenecek VOD ID bulunamadı!")
        return
    
    collected = []
    print(f"\n[▶] {len(vod_ids)} adet film işleniyor...\n")
    
    # Her film için detay al
    for i, vid in enumerate(vod_ids, 1):
        print(f"[{i}/{len(vod_ids)}] İşleniyor: {vid}")
        detail = get_film_detail(vid)
        if detail:
            collected.append(detail)
        
        # Rate limiting
        if i < len(vod_ids):  # Son filmde bekleme
            time.sleep(0.3)
    
    print(f"\n[✓] Toplam {len(collected)} film detayı alındı")
    
    # M3U dosyasını oluştur
    valid_count = write_m3u(collected)
    
    # Log kaydet
    if collected:
        save_log(collected)
    
    # Sonuçları göster
    print("\n" + "=" * 50)
    print("SONUÇLAR:")
    print(f"  • Toplam ID: {len(vod_ids)}")
    print(f"  • Başarılı: {len(collected)}")
    print(f"  • M3U'ya yazılan: {valid_count}")
    print(f"  • Çalışma dizini: {os.getcwd()}")
    
    # Dosya listesi
    print("\n📂 Mevcut dosyalar:")
    files = os.listdir()
    for file in sorted(files)[:10]:  # İlk 10 dosya
        if file.endswith(('.m3u', '.txt', '.json')):
            print(f"  • {file}")
    
    if len(files) > 10:
        print(f"  • ... ve {len(files) - 10} daha")

if __name__ == "__main__":
    main()
