import requests
import os
import json
import time

# === YENİ BEARER TOKEN ===
BEARER_TOKEN = "Bearer eyJhbGciOiJIUzI1NiJ9.eyJjZ2QiOiIwOTNkNzIwYS01MDJjLTQxZWQtYTgwZi0yYjgxNjk4NGZiOTUiLCJkaSI6IjBmYTAzNTlkLWExOWItNDFiMi05ZTczLTI5ZWNiNjk2OTY0MCIsImFwdiI6IjEuMC4wIiwiZW52IjoiTElWRSIsImFibiI6IjEwMDAiLCJzcGdkIjoiYTA5MDg3ODQtZDEyOC00NjFmLWI3NmItYTU3ZGViMWI4MGNjIiwiaWNoIjoiMCIsInNnZCI6ImViODc3NDRjLTk4NDItNDUwNy05YjBhLTQ0N2RmYjg2NjJhZCIsImlkbSI6IjAiLCJkY3QiOiIzRUY3NSIsImlhIjoiOjpmZmZmOjEwLjAuMC41IiwiY3NoIjoiVFJLU1QiLCJpcGIiOiIwIn0.bT8PK2SvGy2CdmbcCnwlr8RatdDiBe_08k7YlnuQqJE"

HEADERS = {
    "Authorization": BEARER_TOKEN,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://tvheryerde.com",
    "Origin": "https://tvheryerde.com",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7"
}

OUTPUT_M3U = "vod_hizli.m3u"
VOD_ID_FILE = "vod_ids.txt"

def test_new_token():
    """Yeni token ile API testi"""
    print("🔐 Yeni Token ile API Testi...")
    print(f"Token: {BEARER_TOKEN[:50]}...")
    
    # Daha uzun timeout ve farklı endpoint dene
    test_urls = [
        "https://core-api.kablowebtv.com/api/vod/list?PageSize=1",
        "https://core-api.kablowebtv.com/api/channels",  # Canlı TV endpoint'i
        "https://core-api.kablowebtv.com/api/home"       # Home endpoint'i
    ]
    
    for url in test_urls:
        print(f"\n📡 Testing: {url}")
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            print(f"   ✅ Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   📊 Content: {response.text[:100]}...")
                # JSON ise parse et
                try:
                    data = response.json()
                    print(f"   📋 JSON Keys: {list(data.keys())}")
                except:
                    pass
            elif response.status_code == 401:
                print("   ❌ 401 Unauthorized - Token geçersiz!")
            elif response.status_code == 403:
                print("   ❌ 403 Forbidden - Erişim engellendi!")
        except requests.exceptions.Timeout:
            print("   ⏰ Timeout - API yanıt vermiyor")
        except Exception as e:
            print(f"   ❌ Hata: {type(e).__name__}")

def get_vod_list_simple():
    """Basit şekilde VOD listesi al"""
    print("\n🎬 VOD Listesi alınıyor...")
    
    url = "https://core-api.kablowebtv.com/api/vod/list"
    
    # Farklı parametreler dene
    params_list = [
        {"PageSize": 10, "PageNumber": 1},
        {"PageSize": 5},
        {}  # Parametresiz
    ]
    
    for params in params_list:
        print(f"\n🔍 Params ile deneme: {params}")
        try:
            response = requests.get(url, headers=HEADERS, params=params, timeout=20)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ Başarılı!")
                
                try:
                    data = response.json()
                    print(f"   📊 JSON yapısı: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"   🔑 Keys: {list(data.keys())}")
                        
                        # Farklı data yapıları
                        if "Data" in data:
                            data_part = data["Data"]
                            if isinstance(data_part, dict) and "Items" in data_part:
                                films = data_part["Items"]
                                print(f"   🎥 Film sayısı: {len(films)}")
                                return films
                            elif isinstance(data_part, list):
                                print(f"   🎥 Direct list: {len(data_part)} items")
                                return data_part
                        elif "Items" in data:
                            films = data["Items"]
                            print(f"   🎥 Film sayısı: {len(films)}")
                            return films
                        elif isinstance(data, list):
                            print(f"   🎥 Direct array: {len(data)} items")
                            return data
                    
                    return data
                    
                except json.JSONDecodeError:
                    print(f"   ❌ JSON decode hatası: {response.text[:100]}")
                    break
                    
            else:
                print(f"   ❌ HTTP {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Hata: {type(e).__name__}")
    
    return []

def create_m3u_from_films(films):
    """Film listesinden M3U oluştur"""
    if not films:
        print("❌ Film bulunamadı!")
        return 0
    
    print(f"\n📝 {len(films)} film işleniyor...")
    
    valid_count = 0
    with open(OUTPUT_M3U, "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        
        for i, film in enumerate(films):
            if isinstance(film, dict):
                # Başlık
                title = film.get("Title") or film.get("title") or film.get("Name") or f"Film {i+1}"
                
                # Stream URL
                stream_url = None
                is_drm = True
                
                # Farklı stream formatları
                if "StreamData" in film and isinstance(film["StreamData"], dict):
                    stream_data = film["StreamData"]
                    stream_url = stream_data.get("DashStreamUrl") or stream_data.get("HlsStreamUrl")
                    is_drm = stream_data.get("IsDrmEnabled", True)
                elif "stream_url" in film:
                    stream_url = film["stream_url"]
                elif "url" in film:
                    stream_url = film["url"]
                
                # Logo
                logo = ""
                if "Posters" in film and isinstance(film["Posters"], list):
                    for poster in film["Posters"]:
                        if isinstance(poster, dict):
                            if poster.get("Type") == "listing":
                                logo = poster.get("ImageUrl", "")
                                break
                
                # ID
                vod_id = film.get("UId") or film.get("id") or str(i+1)
                
                # Kategori
                category = "VOD"
                if "Categories" in film and film["Categories"]:
                    cats = film["Categories"]
                    if isinstance(cats, list) and len(cats) > 0:
                        if isinstance(cats[0], dict):
                            category = cats[0].get("Name", "VOD")
                        else:
                            category = str(cats[0])
                
                # M3U'ya yaz
                if stream_url and not is_drm:
                    f.write(f'#EXTINF:-1 tvg-id="{vod_id}" tvg-logo="{logo}" group-title="{category}",{title}\n')
                    f.write(f'{stream_url}\n')
                    valid_count += 1
                    
                    if valid_count <= 5:  # İlk 5 filmi göster
                        print(f"  ✓ {title[:40]}...")
                else:
                    if valid_count <= 3:  # İlk 3 başarısızı göster
                        drm_status = "DRM" if is_drm else "Stream yok"
                        print(f"  ✗ {title[:30]}... [{drm_status}]")
    
    print(f"\n✅ {valid_count} film '{OUTPUT_M3U}' dosyasına yazıldı!")
    return valid_count

def get_vod_from_ids():
    """vod_ids.txt'den ID'leri oku ve filmleri al"""
    if not os.path.exists(VOD_ID_FILE):
        print(f"⚠️  {VOD_ID_FILE} bulunamadı")
        return []
    
    print(f"\n📂 {VOD_ID_FILE} dosyası okunuyor...")
    
    try:
        with open(VOD_ID_FILE, "r", encoding="utf-8") as f:
            vod_ids = [line.strip() for line in f if line.strip()]
        
        print(f"📋 {len(vod_ids)} VOD ID'si bulundu")
        
        # Sadece ilk 10'u al (test için)
        test_ids = vod_ids[:10]
        films = []
        
        print(f"\n🔍 İlk {len(test_ids)} film alınıyor...")
        
        for i, vod_id in enumerate(test_ids):
            print(f"  [{i+1}/{len(test_ids)}] ID: {vod_id}")
            
            url = "https://core-api.kablowebtv.com/api/vod/detail"
            params = {"VodUId": vod_id}
            
            try:
                response = requests.get(url, headers=HEADERS, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("IsSucceeded") and data.get("Data"):
                        films.append(data["Data"][0])
                        print(f"    ✅ Bulundu")
                    else:
                        print(f"    ❌ API başarısız")
                else:
                    print(f"    ❌ HTTP {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Hata: {type(e).__name__}")
            
            # Kısa bekleme
            time.sleep(0.1)
        
        return films
        
    except Exception as e:
        print(f"❌ Dosya okuma hatası: {e}")
        return []

def main():
    print("=" * 60)
    print("🎬 VOD M3U OLUŞTURUCU")
    print("=" * 60)
    
    start_time = time.time()
    
    # 1. Önce token testi
    test_new_token()
    
    # 2. VOD listesini al
    print("\n" + "=" * 40)
    films = get_vod_list_simple()
    
    # 3. Eğer liste boşsa, ID'lerden dene
    if not films:
        print("\n⚠️  Liste boş, ID'lerden deniyor...")
        films = get_vod_from_ids()
    
    # 4. M3U oluştur
    print("\n" + "=" * 40)
    if films:
        valid_count = create_m3u_from_films(films)
        
        # 5. Sonuç
        elapsed = time.time() - start_time
        print("\n" + "=" * 40)
        print("📊 SONUÇLAR:")
        print(f"  • Toplam film: {len(films)}")
        print(f"  • M3U'ya yazılan: {valid_count}")
        print(f"  • Süre: {elapsed:.1f} saniye")
        print(f"  • Dosya: {os.path.abspath(OUTPUT_M3U)}")
        
        if valid_count > 0:
            print(f"\n✅ BAŞARILI! VLC ile açın: vlc {OUTPUT_M3U}")
    else:
        print("❌ Hiç film bulunamadı!")
        
        # Alternatif: Test M3U oluştur
        print("\n🔄 Test M3U oluşturuluyor...")
        create_test_m3u()

def create_test_m3u():
    """Test amaçlı örnek M3U oluştur"""
    test_entries = [
        "#EXTM3U",
        "#EXTINF:-1 tvg-id=\"1\" tvg-logo=\"\" group-title=\"Test\",Test Film 1",
        "https://test-stream.com/film1.mpd",
        "#EXTINF:-1 tvg-id=\"2\" tvg-logo=\"\" group-title=\"Test\",Test Film 2",
        "https://test-stream.com/film2.mpd",
        "#EXTINF:-1 tvg-id=\"3\" tvg-logo=\"\" group-title=\"Test\",Test Film 3",
        "https://test-stream.com/film3.mpd"
    ]
    
    with open("test_example.m3u", "w", encoding="utf-8") as f:
        f.write("\n".join(test_entries))
    
    print("✅ Test M3U oluşturuldu: test_example.m3u")
    print("📍 Formatı görmek için bu dosyayı inceleyin")

if __name__ == "__main__":
    main()
