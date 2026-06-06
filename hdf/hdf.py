#!/usr/bin/env python3
import os
import json
import re
import time
import random
import argparse
from typing import List, Dict, Optional
from curl_cffi import requests
import yaml
from datetime import datetime

BASE_URL = "https://www.hdfilmizle.now"

def get_headers():
    random_ip = f"{random.randint(1,254)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}"
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "referer": BASE_URL + "/",
        "x-forwarded-for": random_ip,
        "cf-connecting-ip": random_ip,
        "true-client-ip": random_ip,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def get_total_pages(tip: str = "dizi") -> int:
    if tip == "dizi":
        url = f"{BASE_URL}/yabanci-dizi-izle-3/"
    else:
        url = f"{BASE_URL}/"
    
    try:
        res = requests.get(url, headers=get_headers(), impersonate="chrome", timeout=30)
        if res.status_code == 200:
            page_links = re.findall(r'/page/(\d+)/', res.text)
            if page_links:
                return max(int(p) for p in page_links)
    except Exception as e:
        print(f"⚠️ Sayfa sayısı bulunamadı: {e}")
    
    return 10

def extract_episodes(detay_html: str, base_url: str) -> List[Dict]:
    bolumler = []
    
    patterns = [
        r'<a[^>]+href="([^"]*/sezon-\d+/bolum-\d+/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>',
        r'<a[^>]+href="([^"]*/bolum-\d+/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>',
        r'<a[^>]+href="([^"]*/bolum[^"]*)"[^>]+title="([^"]+)"[^>]*>',
        r'<a\s+href="([^"]*(?:sezon|bolum)[^"]*)"[^>]*>([^<]+(?:Bölüm|Episode)[^<]*)</a>'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, detay_html, re.IGNORECASE)
        for match in matches:
            bolum_url = match[0] if match[0].startswith("http") else base_url + match[0]
            bolum_title = re.sub(r'<[^>]*>', '', match[1]).strip() if len(match) > 1 else f"Bölüm {len(bolumler)+1}"
            bolumler.append({"title": bolum_title, "url": bolum_url})
    
    unique = {}
    for b in bolumler:
        if b["url"] not in unique:
            unique[b["url"]] = b
    
    return list(unique.values())

def get_episode_video(episode_url: str) -> Optional[str]:
    for deneme in range(2):
        try:
            res = requests.get(episode_url, headers=get_headers(), impersonate="chrome", timeout=20)
            if res.status_code != 200:
                continue
            
            patterns = [
                r'<iframe[^>]+(?:data-src|src)="([^"]*vidrame\.pro/vr/([a-zA-Z0-9]+)[^"]*)"',
                r'<iframe[^>]+(?:data-src|src)="([^"]*\.(?:m3u8|mp4)[^"]*)"',
                r'(?:file|source):\s*["\']([^"\']*\.m3u8[^"\']*)["\']'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, res.text, re.IGNORECASE)
                if match:
                    if match.group(2):
                        return f"https://vidrame.pro/vr/get/{match.group(2)}/master.m3u8"
                    elif match.group(1):
                        return match.group(1)
            
            time.sleep(0.5)
        except Exception:
            pass
    
    return None

def process_series(series_url: str, title: str, poster: str, max_episodes: int = 20) -> Optional[Dict]:
    print(f"   🎬 İşleniyor: {title}")
    
    try:
        res = requests.get(series_url, headers=get_headers(), impersonate="chrome", timeout=30)
        if res.status_code != 200:
            return None
        
        bolumler = extract_episodes(res.text, BASE_URL)
        
        if not bolumler:
            print(f"      ⚠️ Bölüm bulunamadı: {title}")
            return None
        
        print(f"      📺 {len(bolumler)} bölüm bulundu, işleniyor...")
        
        bolum_detaylari = []
        for i, bolum in enumerate(bolumler[:max_episodes]):
            print(f"         Bölüm {i+1}/{min(len(bolumler), max_episodes)}: {bolum['title']}")
            
            m3u8 = get_episode_video(bolum["url"])
            if m3u8:
                bolum_detaylari.append({
                    "bolum_adi": bolum["title"],
                    "bolum_url": bolum["url"],
                    "m3u8": m3u8
                })
            
            time.sleep(random.uniform(0.5, 1.0))
        
        if bolum_detaylari:
            bolum_detaylari.sort(key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x['bolum_adi'])])
            
            return {
                "title": title,
                "poster": poster,
                "url": series_url,
                "toplam_bolum": len(bolumler),
                "cekilen_bolum": len(bolum_detaylari),
                "bolumler": bolum_detaylari
            }
    
    except Exception as e:
        print(f"      ❌ Hata: {e}")
    
    return None

def dizi_kazı(max_sayfa: int = None, max_episodes: int = 20):
    if max_sayfa is None:
        max_sayfa = get_total_pages("dizi")
        print(f"📊 Toplam {max_sayfa} sayfa bulundu")
    
    tüm_diziler = []
    
    for sayfa in range(1, max_sayfa + 1):
        print(f"\n🔄 [DİZİ] Sayfa {sayfa}/{max_sayfa} taranıyor...")
        target_url = f"{BASE_URL}/yabanci-dizi-izle-3/page/{sayfa}/"
        
        try:
            res = requests.get(target_url, headers=get_headers(), impersonate="chrome", timeout=30)
            if res.status_code != 200:
                print(f"⚠️ Sayfa {sayfa} yüklenemedi. HTTP: {res.status_code}")
                continue
            
            html = res.text
            main_match = re.search(r'id="moviesListResult"([\s\S]*?)</nav>', html)
            if not main_match:
                print(f"⚠️ Sayfa {sayfa}: 'moviesListResult' bulunamadı")
                continue
            
            list_html = main_match.group(1)
            card_regex = r'<a\s+href="([^"]+)"\s+title="([^"]+)"[^>]*class="([^"]*poster[^"]*)"[^>]*>([\s\S]*?)</a>'
            matches = re.findall(card_regex, list_html, re.IGNORECASE)
            
            print(f"   📋 {len(matches)} dizi bulundu")
            
            for match in matches:
                link, title, _, card_inner = match
                title = title.strip()
                
                poster = ""
                ds_match = re.search(r'data-src="([^"]+)"', card_inner)
                if ds_match:
                    poster = ds_match.group(1)
                else:
                    s_match = re.search(r'src="([^"]+)"', card_inner)
                    if s_match:
                        poster = s_match.group(1)
                
                temiz_url = link if link.startswith("http") else BASE_URL + link
                dizi_ana = re.match(r'(https://www\.hdfilmizle\.now/dizi/[^/]+/)', temiz_url)
                if dizi_ana:
                    temiz_url = dizi_ana.group(1)
                
                if poster and not poster.startswith("http"):
                    poster = BASE_URL + poster
                
                time.sleep(random.uniform(1.0, 2.0))
                
                dizi_data = process_series(temiz_url, title, poster, max_episodes)
                if dizi_data:
                    tüm_diziler.append(dizi_data)
                    print(f"      ✅ Başarılı! Toplam bölüm: {dizi_data['toplam_bolum']}")
                else:
                    print(f"      ❌ Başarısız")
        
        except Exception as e:
            print(f"❌ Sayfa {sayfa} genel hatası: {e}")
        
        if sayfa < max_sayfa:
            wait_time = random.uniform(2, 4)
            print(f"   ⏳ {wait_time:.1f} saniye bekleniyor...")
            time.sleep(wait_time)
    
    return tüm_diziler

def save_data(data: Dict, filename: str, format: str = "both"):
    """JSON ve/veya YAML formatında kaydet"""
    os.makedirs("hdf", exist_ok=True)
    
    if format in ["json", "both"]:
        json_path = os.path.join("hdf", f"{filename}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ JSON kaydedildi: {json_path}")
    
    if format in ["yaml", "both"]:
        yaml_path = os.path.join("hdf", f"{filename}.yaml")
        with open(yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        print(f"✅ YAML kaydedildi: {yaml_path}")

def main():
    parser = argparse.ArgumentParser(description='HDFilmIzle Kazıyıcı')
    parser.add_argument('--dizi', action='store_true', help='Sadece dizileri kazı')
    parser.add_argument('--film', action='store_true', help='Sadece filmleri kazı')
    parser.add_argument('--both', action='store_true', help='Hem film hem dizi kazı')
    parser.add_argument('--max-pages', type=int, default=None, help='Maksimum sayfa sayısı')
    parser.add_argument('--max-episodes', type=int, default=20, help='Maksimum bölüm sayısı')
    parser.add_argument('--format', choices=['json', 'yaml', 'both'], default='both', help='Çıktı formatı')
    
    args = parser.parse_args()
    
    print("🎬 HDFilmIzle Kazıyıcı Başlatılıyor...")
    print("=" * 50)
    
    veri = {
        "metadata": {
            "kazıma_tarihi": datetime.now().isoformat(),
            "kaynak": BASE_URL,
            "version": "1.0.0"
        }
    }
    
    if args.dizi or args.both or (not args.dizi and not args.film):
        print("\n📺 DİZİLER KAZINIYOR...")
        veri["diziler"] = dizi_kazı(max_sayfa=args.max_pages, max_episodes=args.max_episodes)
        print(f"\n✅ Toplam {len(veri['diziler'])} dizi kazındı")
    
    if args.film or args.both:
        print("\n🎬 FİLMLER KAZINIYOR...")
        # Film kazıma fonksiyonu buraya eklenecek
        veri["filmler"] = []
        print("⚠️ Film modu henüz implement edilmedi")
    
    save_data(veri, "data", args.format)
    print(f"\n✅ Tüm işlemler tamamlandı!")

if __name__ == "__main__":
    main()
