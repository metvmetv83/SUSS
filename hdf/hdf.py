#!/usr/bin/env python3
import json
import re
import time
import random
import requests
from datetime import datetime

BASE_URL = "https://www.hdfilmizle.now"
WORKER_URL = "https://hdfilmdizijson.64fetih.workers.dev"  # Worker'ınızın adresi

def worker_istek(tip="dizi", sayfa=1):
    """Worker üzerinden veri çek"""
    url = f"{WORKER_URL}/?tip={tip}&sayfa={sayfa}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Worker hatası: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"Worker bağlantı hatası: {e}")
        return None

def direkt_kazı(max_sayfa=5, max_episodes=10):
    """Worker kullanmadan direkt kazı (Worker çalışmazsa yedek)"""
    print("📡 Worker kullanılmadan direkt kazı yapılıyor...")
    
    tüm_diziler = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": BASE_URL
    }
    
    for sayfa in range(1, max_sayfa + 1):
        print(f"\n🔄 Sayfa {sayfa}/{max_sayfa}")
        url = f"{BASE_URL}/yabanci-dizi-izle-3/page/{sayfa}/"
        
        try:
            response = requests.get(url, headers=headers, timeout=20)
            if response.status_code != 200:
                continue
            
            html = response.text
            main_match = re.search(r'id="moviesListResult"([\s\S]*?)</nav>', html)
            if not main_match:
                continue
            
            # Kartları bul
            card_pattern = r'<a\s+href="([^"]+)"\s+title="([^"]+)"'
            matches = re.findall(card_pattern, main_match.group(1))
            
            print(f"   📋 {len(matches)} dizi bulundu")
            
            for link, title in matches:
                print(f"\n   🎬 {title[:50]}")
                
                dizi_url = link if link.startswith("http") else BASE_URL + link
                dizi_match = re.match(r'(https://www\.hdfilmizle\.now/dizi/[^/]+/)', dizi_url)
                if dizi_match:
                    dizi_url = dizi_match.group(1)
                
                try:
                    detay_response = requests.get(dizi_url, headers=headers, timeout=15)
                    if detay_response.status_code != 200:
                        continue
                    
                    detay_html = detay_response.text
                    
                    # Bölümleri bul
                    bolum_pattern = r'<a[^>]+href="([^"]*/sezon-\d+/bolum-\d+/[^"]*)"'
                    bolum_links = re.findall(bolum_pattern, detay_html)
                    
                    if not bolum_links:
                        bolum_pattern = r'<a[^>]+href="([^"]*/bolum-\d+/[^"]*)"'
                        bolum_links = re.findall(bolum_pattern, detay_html)
                    
                    print(f"      📺 {len(bolum_links)} bölüm bulundu")
                    
                    bolumler = []
                    for b_link in bolum_links[:max_episodes]:
                        b_url = b_link if b_link.startswith("http") else BASE_URL + b_link
                        b_response = requests.get(b_url, headers=headers, timeout=10)
                        
                        if b_response.status_code == 200:
                            v_match = re.search(r'vidrame\.pro/vr/([a-zA-Z0-9]+)', b_response.text)
                            if v_match:
                                bolumler.append({
                                    "bolum_adi": f"Bölüm {len(bolumler)+1}",
                                    "m3u8": f"https://vidrame.pro/vr/get/{v_match.group(1)}/master.m3u8"
                                })
                        
                        time.sleep(0.3)
                    
                    if bolumler:
                        tüm_diziler.append({
                            "title": title,
                            "url": dizi_url,
                            "toplam_bolum": len(bolum_links),
                            "cekilen_bolum": len(bolumler),
                            "bolumler": bolumler
                        })
                        print(f"      ✅ {len(bolumler)} bölüm eklendi")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"      ❌ Hata: {str(e)[:50]}")
                    continue
            
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ Sayfa hatası: {e}")
            continue
    
    return tüm_diziler

def worker_kazı(max_sayfa=10):
    """Worker üzerinden tüm sayfaları çek"""
    print("📡 Worker üzerinden veri çekiliyor...")
    print(f"   Worker: {WORKER_URL}")
    
    tüm_diziler = []
    basarili = 0
    basarisiz = 0
    
    for sayfa in range(1, max_sayfa + 1):
        print(f"\n🔄 Sayfa {sayfa}/{max_sayfa} çekiliyor...")
        
        veri = worker_istek("dizi", sayfa)
        
        if veri and veri.get("durum") == "basarili":
            print(f"   📋 {veri.get('toplam_kart', 0)} kart, {veri.get('basarili_cekme', 0)} başarılı")
            
            for dizi in veri.get("veriler", []):
                if dizi.get("hata"):
                    basarisiz += 1
                    print(f"   ❌ {dizi.get('title', '?')} - {dizi.get('mesaj', 'Hata')}")
                else:
                    basarili += 1
                    tüm_diziler.append(dizi)
                    print(f"   ✅ {dizi.get('title', '?')} - {dizi.get('cekilen_bolum', 0)}/{dizi.get('toplam_bolum', 0)} bölüm")
        else:
            print(f"   ⚠️ Sayfa {sayfa} alınamadı")
        
        time.sleep(0.5)  # Rate limiting
    
    print(f"\n📊 İSTATİSTİKLER:")
    print(f"   ✅ Başarılı: {basarili} dizi")
    print(f"   ❌ Başarısız: {basarisiz} dizi")
    print(f"   📈 Toplam: {len(tüm_diziler)} dizi")
    
    return tüm_diziler

def main():
    print("🎬 HDFilm Dizi Kazıyıcı")
    print("=" * 40)
    
    # Önce Worker'ı dene
    print("\n🔍 Worker test ediliyor...")
    test = worker_istek("dizi", 1)
    
    if test and test.get("durum") == "basarili":
        print("✅ Worker çalışıyor!")
        max_sayfa = int(input("Kaç sayfa çekilsin? (1-20, varsayılan 5): ") or "5")
        max_sayfa = min(max_sayfa, 20)
        diziler = worker_kazı(max_sayfa)
    else:
        print("⚠️ Worker çalışmıyor, direkt kazı yapılacak...")
        max_sayfa = int(input("Kaç sayfa taranacak? (varsayılan 2): ") or "2")
        max_episodes = int(input("Her dizi için max bölüm? (varsayılan 10): ") or "10")
        diziler = direkt_kazı(max_sayfa, max_episodes)
    
    # Kaydet
    veri = {
        "metadata": {
            "tarih": datetime.now().isoformat(),
            "kaynak": WORKER_URL if test else "DIRECT",
            "toplam_dizi": len(diziler)
        },
        "diziler": diziler
    }
    
    with open("hdf/diziler.json", "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ {len(diziler)} dizi kaydedildi: hdf/diziler.json")

if __name__ == "__main__":
    main()
