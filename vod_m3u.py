import requests
import os
import time
import json

# === TOKEN ===
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
}

def get_film_details(vod_ids, max_films=50):
    """VOD ID'lerinden film detaylarını al (hata güvenli)"""
    films = []
    
    print(f"\n🎬 İlk {min(len(vod_ids), max_films)} film alınıyor...")
    print("⏳ Bu işlem 30-60 saniye sürebilir...")
    
    for i, vod_id in enumerate(vod_ids[:max_films]):
        try:
            url = f"https://core-api.kablowebtv.com/api/vod/detail?VodUId={vod_id}"
            response = requests.get(url, headers=HEADERS, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("IsSucceeded") and data.get("Data"):
                    film = data["Data"][0]
                    films.append(film)
                    
                    # Film bilgilerini al
                    title = film.get("Title", "Bilinmeyen")[:35]
                    
                    # StreamData kontrolü (None olabilir)
                    stream_data = film.get("StreamData")
                    if stream_data and isinstance(stream_data, dict):
                        has_mpd = "✓" if stream_data.get("DashStreamUrl") else "✗"
                        is_drm = "DRM" if stream_data.get("IsDrmEnabled") else "✓"
                    else:
                        has_mpd = "✗"
                        is_drm = "NoData"
                    
                    print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] {title} {has_mpd} {is_drm}")
                else:
                    print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] ❌ API başarısız")
            else:
                print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] ❌ HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] ⏰ Timeout")
        except Exception as e:
            print(f"  [{i+1:2d}/{min(len(vod_ids), max_films)}] ❌ {type(e).__name__}")
        
        # İlerleme çubuğu (her 10 filmde bir)
        if (i + 1) % 10 == 0:
            print(f"     ↳ {i+1} film tamamlandı...")
        
        # Kısa bekleme
        time.sleep(0.05)
    
    return films

def create_proper_m3u(films, output_file="vod_playlist.m3u"):
    """Doğru formatta M3U oluştur (hata güvenli)"""
    print(f"\n📝 M3U oluşturuluyor: {output_file}")
    
    valid_count = 0
    drm_count = 0
    no_stream_count = 0
    no_data_count = 0
    
    with open(output_file, "w", encoding="utf-8") as f:
        # M3U başlığı
        f.write("#EXTM3U x-tvg-url=\"\"\n")
        
        for i, film in enumerate(films):
            title = film.get("Title", f"Film_{i+1}")
            uid = film.get("UId", f"id_{i+1}")
            
            # Logo bul (güvenli)
            logo = ""
            posters = film.get("Posters", [])
            if posters and isinstance(posters, list):
                for poster in posters:
                    if isinstance(poster, dict) and poster.get("Type") == "listing":
                        logo = poster.get("ImageUrl", "")
                        break
            
            # Stream bilgileri (GÜVENLİ - None kontrolü)
            stream_data = film.get("StreamData")
            mpd_url = None
            hls_url = None
            is_drm = True  # Varsayılan: DRM'li
            
            if stream_data and isinstance(stream_data, dict):
                mpd_url = stream_data.get("DashStreamUrl")
                hls_url = stream_data.get("HlsStreamUrl")
                is_drm = stream_data.get("IsDrmEnabled", True)
            else:
                no_data_count += 1
                continue  # StreamData yoksa atla
            
            # Kategori (güvenli)
            category = "VOD"
            cats = film.get("Categories", [])
            if cats and isinstance(cats, list) and len(cats) > 0:
                cat = cats[0]
                if isinstance(cat, dict):
                    category = cat.get("Name", "VOD")
                else:
                    category = str(cat)
            
            # Stream URL'si seç (DRM'siz olmalı)
            stream_url = None
            if mpd_url and not is_drm:
                stream_url = mpd_url
                stream_type = "DASH"
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
                
                # İlk 10 filmi göster
                if valid_count <= 10:
                    print(f"  ✅ {title[:40]}...")
            else:
                if not stream_data:
                    no_data_count += 1
                elif is_drm:
                    drm_count += 1
                else:
                    no_stream_count += 1
                
                # İlk 5 başarısızı göster
                if (drm_count + no_stream_count + no_data_count) <= 5:
                    reason = "No StreamData" if not stream_data else ("DRM" if is_drm else "No URL")
                    print(f"  ❌ {title[:30]}... [{reason}]")
    
    print(f"\n📊 İSTATİSTİKLER:")
    print(f"  • İşlenen film: {len(films)}")
    print(f"  • M3U'ya eklendi: {valid_count} ✓")
    print(f"  • DRM'li: {drm_count} ✗")
    print(f"  • StreamData yok: {no_data_count} ⚠")
    print(f"  • Stream URL'siz: {no_stream_count} ⚠")
    
    return valid_count

def check_and_show_m3u(filename):
    """M3U dosyasını kontrol et ve göster"""
    print(f"\n🔍 {filename} kontrol ediliyor...")
    
    if not os.path.exists(filename):
        print(f"❌ Dosya bulunamadı: {filename}")
        return 0
    
    file_size = os.path.getsize(filename)
    print(f"📏 Dosya boyutu: {file_size} bytes")
    
    try:
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()
        
        lines = [line.rstrip('\n') for line in content.split('\n') if line.strip()]
        
        print(f"📄 Boş olmayan satır: {len(lines)}")
        
        if len(lines) > 0:
            # EXTINF satırlarını say ve göster
            print(f"\n🎬 M3U İÇERİĞİ:")
            
            extinf_lines = [line for line in lines if line.startswith("#EXTINF")]
            url_lines = [line for line in lines if line and not line.startswith("#")]
            
            print(f"  • EXTINF satırları: {len(extinf_lines)}")
            print(f"  • Stream URL'leri: {len(url_lines)}")
            
            # İlk 5 kaydı göster
            print(f"\n📺 İLK 5 KANAL:")
            for i in range(min(5, len(extinf_lines))):
                if i < len(url_lines):
                    extinf = extinf_lines[i]
                    url = url_lines[i]
                    
                    # EXTINF'ten başlık çıkar
                    title_start = extinf.rfind(',')
                    if title_start != -1:
                        title = extinf[title_start + 1:]
                        print(f"  {i+1}. {title[:50]}")
                        print(f"     📡 {url[:80]}...")
                    else:
                        print(f"  {i+1}. {extinf[:50]}")
            
            return len(extinf_lines)
            
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
    
    return 0

def load_vod_ids(filename="vod_ids.txt"):
    """VOD ID'lerini yükle"""
    try:
        with open(filename, "r", encoding="utf-8") as f:
            ids = []
            for line in f:
                line = line.strip()
                if line:
                    # URL'den veya direkt ID'den al
                    if '/' in line:
                        ids.append(line.split('/')[-1])
                    else:
                        ids.append(line)
            print(f"✅ {len(ids)} VOD ID'si yüklendi")
            return ids
    except Exception as e:
        print(f"⚠️  {filename} bulunamadı veya okunamadı: {e}")
        # Örnek test ID'leri
        return [
            "07276a61-8422-4ba9-9985-40a0f97e531e",  # YANG'DAN SONRA
            "a6234076-4d5a-4483-9afd-3a2d24623032",  # DOSTUMUN YOLCULUĞU
            "ed32c713-99c8-4bfb-9fcc-9f22eeb20414",  # İNŞAAT 2
            "008b8ef8-18a8-4286-aa33-08855a562fc4",  # TUZAK
            "00a5069d-3b8f-4d71-8db3-7e3d3f277f87",  # TÜNELİN UCUNDA
        ]

def main():
    print("=" * 70)
    print("🎬 VOD M3U PLAYLIST OLUŞTURUCU")
    print("=" * 70)
    
    start_time = time.time()
    
    # 1. VOD ID'lerini yükle
    vod_ids = load_vod_ids()
    if not vod_ids:
        print("❌ VOD ID'si bulunamadı!")
        return
    
    # 2. İlk 50 filmi al
    films = get_film_details(vod_ids, max_films=50)
    
    if not films:
        print("❌ Hiç film bulunamadı!")
        return
    
    # 3. M3U oluştur
    output_file = "vod_playlist.m3u"
    valid_count = create_proper_m3u(films, output_file)
    
    # 4. M3U dosyasını kontrol et
    m3u_count = check_and_show_m3u(output_file)
    
    # 5. Sonuç
    elapsed = time.time() - start_time
    print("\n" + "=" * 50)
    print("✅ İŞLEM TAMAMLANDI!")
    print(f"   • Toplam süre: {elapsed:.1f} saniye")
    print(f"   • İşlenen film: {len(films)}")
    print(f"   • Playlist'e eklenen: {valid_count}")
    print(f"   • Dosya: {os.path.abspath(output_file)}")
    
    if valid_count > 0:
        print(f"\n🎉 {valid_count} film başarıyla playlist'e eklendi!")
        print(f"📺 İzlemek için: vlc {output_file}")
        print(f"📺 Veya: mpv {output_file}")
        
        # M3U dosyasının ilk satırlarını göster
        print(f"\n📋 M3U ÖNİZLEME:")
        try:
            with open(output_file, "r", encoding="utf-8") as f:
                for i, line in enumerate(f):
                    if i < 10:  # İlk 10 satır
                        print(f"  {line.rstrip()}")
                    else:
                        break
        except:
            pass
    else:
        print("\n⚠️  Hiç film eklenemedi! Sebepler:")
        print("   1. Tüm filmler DRM korumalı olabilir")
        print("   2. StreamData bilgisi eksik olabilir")
        print("   3. API farklı bir yapıda veri döndürüyor olabilir")

if __name__ == "__main__":
    main()
