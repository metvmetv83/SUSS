import os
import json
import re
import time
import random
import requests

BASE_URL = "https://www.hdfilmizle.now"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0"
]

def get_headers():
    random_ip = f"{random.randint(1,254)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}"
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Referer": BASE_URL + "/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "X-Forwarded-For": random_ip,
        "CF-Connecting-IP": random_ip,
        "True-Client-IP": random_ip
    }

def dizi_kazı(max_sayfa=2):
    sonuclar = []
    
    for sayfa in range(1, max_sayfa + 1):
        print(f"🔄 [DİZİ] Sayfa {sayfa} taranıyor...")
        target_url = f"{BASE_URL}/yabanci-dizi-izle-3/page/{sayfa}/"
        
        try:
            res = requests.get(target_url, headers=get_headers(), timeout=15)
            if res.status_code != 200:
                print(f"⚠️ Sayfa {sayfa} yüklenemedi. HTTP Durumu: {res.status_code}")
                continue
                
            html = res.text
            main_match = re.search(r'id="moviesListResult"([\s\S]*?)<\/nav>', html)
            if not main_match:
                print(f"⚠️ Sayfa {sayfa} üzerinde 'moviesListResult' alanı bulunamadı.")
                continue
                
            list_html = main_match.group(1)
            card_regex = r'<a\s+href="([^"]+)"\s+title="([^"]+)"[^>]*class="([^"]*poster[^"]*)"[^>]*>([\s\S]*?)<\/a>'
            matches = re.findall(card_regex, list_html, re.IGNORECASE)
            
            for match in matches:
                link, title, _, card_inner = match
                title = title.strip()
                
                # Poster Bulma
                poster = ""
                ds_match = re.search(r'data-src="([^"]+)"', card_inner)
                if ds_match:
                    poster = ds_match.group(1)
                else:
                    s_match = re.search(r'src="([^"]+)"', card_inner)
                    if s_match: poster = s_match.group(1)
                
                temiz_url = link if link.startswith("http") else BASE_URL + link
                dizi_ana = re.match(r'(https:\/\/www\.hdfilmizle\.now\/dizi\/[^\/]+\/)', temiz_url)
                if dizi_ana: 
                    temiz_url = dizi_ana.group(1)
                    
                if poster and not poster.startswith("http"):
                    poster = BASE_URL + poster
                    
                print(f"   🎬 Dizi detayı çekiliyor: {title}")
                time.sleep(random.uniform(1.0, 2.5)) # İnsan taklidi gecikme süresi
                
                try:
                    detay_res = requests.get(temiz_url, headers=get_headers(), timeout=15)
                    if detay_res.status_code != 200: 
                        continue
                    detay_html = detay_res.text
                    
                    # Sayfadaki tüm bölüm linklerini regex gruplarına göre topla
                    bolum_matches = re.findall(r'<a[^>]+href="([^"]*\/sezon-\d+\/bolum-\d+\/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)<\/h3>', detay_html, re.IGNORECASE)
                    
                    if not bolum_matches:
                        # Alternatif regex pattern (farklı tema yapıları için)
                        bolum_matches = re.findall(r'<a[^>]+href="([^"]*\/bolum-\d+\/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)<\/h3>', detay_html, re.IGNORECASE)

                    bolum_detaylari = []
                    
                    # Bulgulanan tüm bölümleri tek tek dolaş
                    for b_link, b_title in bolum_matches:
                        b_url = b_link if b_link.startswith("http") else BASE_URL + b_link
                        time.sleep(0.8) # Bölüm geçişlerinde hafif bekleme
                        
                        try:
                            b_res = requests.get(b_url, headers=get_headers(), timeout=10)
                            if b_res.status_code == 200:
                                v_match = re.search(r'<iframe[^>]+(?:data-src|src)="([^"]*vidrame\.pro\/vr\/([a-zA-Z0-9]+)[^"]*)"', b_res.text, re.IGNORECASE)
                                if v_match:
                                    bolum_detaylari.append({
                                        "bolum_adi": b_title.strip(),
                                        "m3u8": f"https://vidrame.pro/vr/get/{v_match.group(2)}/master.m3u8"
                                    })
                        except Exception as ep_err:
                            print(f"      ❌ Bölüm çekilemedi ({b_title.strip()}): {ep_err}")
                            pass
                                
                    if bolum_detaylari:
                        # Bölümleri isimlerine göre sıralı hale getir
                        bolum_detaylari.sort(key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x['bolum_adi'])])
                        
                        sonuclar.append({
                            "title": title,
                            "poster": poster,
                            "url": temiz_url,
                            "toplam_bolum": len(bolum_detaylari),
                            "bolumler": bolum_detaylari
                        })
                        print(f"      ✅ Başarıyla eklendi: {len(bolum_detaylari)} Bölüm")
                except Exception as e:
                    print(f"   ❌ Hata oluştu ({title}): {e}")
                    
        except Exception as e:
            print(f"❌ Sayfa hatası: {e}")
            
    return sonuclar

if __name__ == "__main__":
    # Sadece dizileri çekiyoruz
    veri = {
        "diziler": dizi_kazı(max_sayfa=2) # Taranacak sayfa sayısını buradan değiştirebilirsin
    }
    
    hedef_klasor = "hdf"
    if not os.path.exists(hedef_klasor):
        os.makedirs(hedef_klasor)
        
    hedef_dosya = os.path.join(hedef_klasor, "data.json")
    
    with open(hedef_dosya, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
        
    print(f"\n✅ Tüm işlemler tamamlandı. Veriler '{hedef_dosya}' dosyasına yazıldı!")
