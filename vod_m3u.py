import requests
import os
import json
import time
from datetime import datetime

# === TOKEN ===
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_film_details(vod_ids, max_films=20):
    """VOD ID'lerinden film detaylarını al"""
    films = []
    
    print(f"\n🎬 {min(len(vod_ids), max_films)} film alınıyor...")
    
    for i, vod_id in enumerate(vod_ids[:max_films]):
        try:
            url = f"https://core-api.kablowebtv.com/api/vod/detail?VodUId={vod_id}"
            response = requests.get(url, headers=HEADERS, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("IsSucceeded") and data.get("Data"):
                    film = data["Data"][0]
                    films.append(film)
                    
                    # İlerleme göstergesi
                    title = film.get("Title", "Bilinmeyen")[:30]
                    stream = film.get("StreamData", {})
                    has_mpd = "✓" if stream.get("DashStreamUrl") else "✗"
                    is_drm = "DRM" if stream.get("IsDrmEnabled") else "DRM Yok"
                    
                    print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] {title}... {has_mpd} {is_drm}")
                else:
                    print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] ❌ API başarısız")
            else:
                print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] ❌ HTTP {response.status_code}")
                
        except Exception as e:
            print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] ❌ Hata: {type(e).__name__}")
        
        # Kısa bekleme (rate limiting)
        time.sleep(0.1)
    
    return films

def create_proper_m3u(films, output_file="vod_final.m3u"):
    """Doğru formatta M3U oluştur"""
    print(f"\n📝 M3U oluşturuluyor: {output_file}")
    
    valid_count = 0
    drm_count = 0
    no_stream_count = 0
    
    with open(output_file, "w", encoding="utf-8") as f:
        # M3U başlığı
        f.write("#EXTM3U\n")
        
        for film in films:
            title = film.get("Title", "Bilinmeyen")
            uid = film.get("UId", "")
            
            # Logo bul
            logo = ""
            for poster in film.get("Posters", []):
                if poster.get("Type") == "listing":
                    logo = poster.get("ImageUrl", "")
                    break
            
            # Stream bilgileri
            stream = film.get("StreamData", {})
            mpd_url = stream.get("DashStreamUrl")
            hls_url = stream.get("HlsStreamUrl")
            is_drm = stream.get("IsDrmEnabled", True)
            
            # Kategori
            category = "VOD"
            cats = film.get("Categories", [])
            if cats and isinstance(cats, list) and len(cats) > 0:
                cat = cats[0]
                if isinstance(cat, dict):
                    category = cat.get("Name", "VOD")
                else:
                    category = str(cat)
            
            # Stream URL'si seç
            stream_url = None
            if mpd_url and not is_drm:
                stream_url = mpd_url
                stream_type = "MPD"
            elif hls_url and not is_drm:
                stream_url = hls_url
                stream_type = "HLS"
            
            # M3U satırını yaz
            if stream_url:
                # EXTINF satırı
                extinf_line = f'#EXTINF:-1 tvg-id="{uid}" tvg-name="{title}" tvg-logo="{logo}" group-title="{category}",{title}'
                f.write(extinf_line + "\n")
                
                # Stream URL satırı
                f.write(stream_url + "\n")
                
                valid_count += 1
                print(f"  ✅ {title[:40]}... ({stream_type})")
            else:
                if is_drm:
                    drm_count += 1
                else:
                    no_stream_count += 1
                
                if valid_count < 5:  # İlk 5 başarısızı göster
                    reason = "DRM" if is_drm else "Stream URL yok"
                    print(f"  ❌ {title[:30]}... [{reason}]")
    
    print(f"\n📊 İSTATİSTİKLER:")
    print(f"  • Toplam film: {len(films)}")
    print(f"  • M3U'ya yazılan: {valid_count}")
    print(f"  • DRM'li: {drm_count}")
    print(f"  • Stream URL'siz: {no_stream_count}")
    
    return valid_count

def check_m3u_file(filename):
    """M3U dosyasını kontrol et"""
    print(f"\n🔍 {filename} kontrol ediliyor...")
    
    if not os.path.exists(filename):
        print(f"❌ Dosya bulunamadı: {filename}")
        return False
    
    file_size = os.path.getsize(filename)
    print(f"📏 Dosya boyutu: {file_size} bytes")
    
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    print(f"📄 Satır sayısı: {len(lines)}")
    
    if len(lines) > 0:
        print(f"📋 İlk satır: {lines[0]}")
        
        # EXTINF satırlarını say
        extinf_count = sum(1 for line in lines if line.startswith("#EXTINF"))
        print(f"🎬 EXTINF satırları: {extinf_count}")
        
        # Stream URL satırlarını say (EXTINF olmayan ve boş olmayan)
        url_count = sum(1 for line in lines if line and not line.startswith("#"))
        print(f"🔗 Stream URL'leri: {url_count}")
        
        # İçeriği göster
        print(f"\n📝 İLK 10 SATIR:")
        for i, line in enumerate(lines[:10]):
            print(f"  {i+1:2d}: {line[:80]}{'...' if len(line) > 80 else ''}")
    
    return True

def load_vod_ids(filename="vod_ids.txt"):
    """VOD ID'lerini yükle"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        print(f"⚠️  {filename} bulunamadı")
        # Test için örnek ID'ler
        return [
            "07276a61-8422-4ba9-9985-40a0f97e531e",
            "a6234076-4d5a-4483-9afd-3a2d24623032",
            "ed32c713-99c8-4bfb-9fcc-9f22eeb20414"
        ]

def main():
    print("=" * 60)
    print("🎬 VOD M3U OLUŞTURUCU - GÜNCELLENMİŞ")
    print("=" * 60)
    
    start_time = time.time()
    
    # 1. VOD ID'lerini yükle
    vod_ids = load_vod_ids()
    print(f"📋 {len(vod_ids)} VOD ID'si yüklendi")
    
    # 2. İlk 20 filmi al
    films = get_film_details(vod_ids, max_films=20)
    
    if not films:
        print("❌ Hiç film bulunamadı!")
        return
    
    # 3. M3U oluştur
    output_file = "vod_final.m3u"
    valid_count = create_proper_m3u(films, output_file)
    
    # 4. M3U dosyasını kontrol et
    check_m3u_file(output_file)
    
    # 5. Sonuç
    elapsed = time.time() - start_time
    print("\n" + "=" * 40)
    print("✅ İŞLEM TAMAMLANDI!")
    print(f"   • Süre: {elapsed:.1f} saniye")
    print(f"   • Dosya: {os.path.abspath(output_file)}")
    
    if valid_count > 0:
        print(f"\n🎉 {valid_count} film başarıyla eklendi!")
        print(f"📺 İzlemek için: vlc {output_file}")
        
        # Test: İlk filmin detaylarını göster
        print(f"\n🔍 İLK FİLM DETAYI:")
        first_film = films[0]
        title = first_film.get("Title", "Bilinmeyen")
        stream = first_film.get("StreamData", {})
        mpd = stream.get("DashStreamUrl", "YOK")
        drm = stream.get("IsDrmEnabled", True)
        
        print(f"   Başlık: {title}")
        print(f"   MPD URL: {mpd[:80]}...")
        print(f"   DRM: {'Evet' if drm else 'Hayır'}")
    else:
        print("\n⚠️  Hiç film eklenemedi! DRM veya stream URL sorunu olabilir.")

if __name__ == "__main__":
    main()
