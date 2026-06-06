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
    """Dinamik headers - Worker'daki gibi"""
    random_ip = f"{random.randint(1,254)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}"
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": BASE_URL,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Cache-Control": "max-age=0",
        "X-Forwarded-For": random_ip,
        "CF-Connecting-IP": random_ip,
        "True-Client-IP": random_ip
    }

def fetch_with_retry(url: str, max_retries: int = 3, timeout: int = 15) -> Optional[str]:
    """Worker'daki gibi retry mekanizmalı fetch"""
    for deneme in range(1, max_retries + 1):
        try:
            headers = get_headers()
            headers["Cookie"] = f"__cf_bm={random.randint(100000, 999999)}"
            
            response = requests.get(
                url, 
                headers=headers, 
                impersonate="chrome",
                timeout=timeout
            )
            
            if response.status_code == 200:
                html = response.text
                
                # Cloudflare kontrolü
                if "cf-browser-verification" in html or "Attention Required" in html or "DDOS" in html:
                    print(f"      ⚠️ Deneme {deneme}: Cloudflare koruması")
                    time.sleep(2 * deneme)
                    continue
                
                return html
            
            print(f"      ⚠️ Deneme {deneme}: HTTP {response.status_code}")
            time.sleep(1 * deneme)
            
        except Exception as e:
            print(f"      ⚠️ Deneme {deneme}: {str(e)[:50]}")
            time.sleep(1 * deneme)
    
    return None

def extract_episodes(detay_html: str) -> List[Dict]:
    """Bölümleri extracted et"""
    bolumler = []
    
    patterns = [
        r'<a[^>]+href="([^"]*/sezon-\d+/bolum-\d+/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>[\s\S]*?</a>',
        r'<a[^>]+href="([^"]*/bolum-\d+/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>[\s\S]*?</a>',
        r'<a[^>]+href="([^"]*/sezon[^"]*/bolum[^"]*)"[^>]+title="([^"]+)"[^>]*>'
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, detay_html, re.IGNORECASE)
        for match in matches:
            ep_url = match[0] if match[0].startswith("http") else BASE_URL + match[0]
            ep_title = match[1] if len(match) > 1 else f"Bölüm {len(bolumler)+1}"
            ep_title = re.sub(r'<[^>]*>', '', ep_title).strip()
            ep_title = re.sub(r'\s+', ' ', ep_title)
            
            bolumler.append({"title": ep_title, "url": ep_url})
    
    # Benzersiz bölümleri filtrele
    unique = {}
    for b in bolumler:
        if b["url"] not in unique:
            unique[b["url"]] = b
    
    return list(unique.values())

def get_episode_video(episode_url: str) -> Optional[str]:
    """Bölümün video linkini bul"""
    ep_html = fetch_with_retry(episode_url, max_retries=2, timeout=10)
    if not ep_html:
        return None
    
    patterns = [
        r'<iframe[^>]+(?:data-src|src)="([^"]*vidrame\.pro/vr/([a-zA-Z0-9]+)[^"]*)"',
        r'<iframe[^>]+(?:data-src|src)="([^"]*\.(?:m3u8|mp4)[^"]*)"'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, ep_html, re.IGNORECASE)
        if match:
            if match.group(2):
                return f"https://vidrame.pro/vr/get/{match.group(2)}/master.m3u8"
            elif match.group(1):
                return match.group(1)
    
    return None

def get_total_pages() -> int:
    """Toplam sayfa sayısını bul"""
    url = f"{BASE_URL}/yabanci-dizi-izle-3/"
    html = fetch_with_retry(url, max_retries=2)
    
    if html:
        page_links = re.findall(r'/page/(\d+)/', html)
        if page_links:
            return max(int(p) for p in page_links)
    
    return 2  # Varsayılan 2 sayfa

def dizi_kazı(max_sayfa: int = None, max_episodes: int = 10):
    """Tüm dizileri kazı"""
    
    if max_sayfa is None:
        max_sayfa = get_total_pages()
        print(f"📊 Toplam {max_sayfa} sayfa bulundu")
    else:
        print(f"📊 {max_sayfa} sayfa taranacak")
    
    tüm_diziler = []
    basarili = 0
    basarisiz = 0
    
    for sayfa in range(1, max_sayfa + 1):
        print(f"\n🔄 [DİZİ] Sayfa {sayfa}/{max_sayfa} taranıyor...")
        target_url = f"{BASE_URL}/yabanci-dizi-izle-3/page/{sayfa}/"
        
        html = fetch_with_retry(target_url, max_retries=3, timeout=20)
        if not html:
            print(f"   ❌ Sayfa {sayfa} alınamadı")
            basarisiz += 1
            continue
        
        main_match = re.search(r'id="moviesListResult"([\s\S]*?)</nav>', html)
        if not main_match:
            print(f"   ⚠️ Sayfa {sayfa}: moviesListResult bulunamadı")
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
            dizi_match = re.match(r'(https://www\.hdfilmizle\.now/dizi/[^/]+/)', temiz_url)
            if dizi_match:
                temiz_url = dizi_match.group(1)
            
            if poster and not poster.startswith("http"):
                poster = BASE_URL + poster
            
            print(f"\n   🎬 {title}")
            
            detay_html = fetch_with_retry(temiz_url, max_retries=2, timeout=15)
            if not detay_html:
                print(f"      ❌ Detay sayfası alınamadı")
                basarisiz += 1
                continue
            
            bolumler = extract_episodes(detay_html)
            
            if not bolumler:
                print(f"      ⚠️ Bölüm bulunamadı")
                basarisiz += 1
                continue
            
            print(f"      📺 {len(bolumler)} bölüm bulundu, ilk {max_episodes} işleniyor...")
            
            unique_bolumler = []
            seen_urls = set()
            for bolum in bolumler:
                if bolum["url"] not in seen_urls:
                    seen_urls.add(bolum["url"])
                    unique_bolumler.append(bolum)
            
            bolum_detaylari = []
            max_eps = min(len(unique_bolumler), max_episodes)
            
            for i, bolum in enumerate(unique_bolumler[:max_eps]):
                print(f"         Bölüm {i+1}/{max_eps}: {bolum['title'][:40]}...")
                
                m3u8 = get_episode_video(bolum["url"])
                if m3u8:
                    bolum_detaylari.append({
                        "bolum_adi": bolum["title"],
                        "bolum_url": bolum["url"],
                        "m3u8": m3u8
                    })
                    print(f"            ✅ Video bulundu")
                else:
                    print(f"            ⚠️ Video bulunamadı")
                
                time.sleep(random.uniform(0.3, 0.7))
            
            if bolum_detaylari:
                bolum_detaylari.sort(key=lambda x: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', x['bolum_adi'])])
                
                tüm_diziler.append({
                    "title": title,
                    "poster": poster,
                    "url": temiz_url,
                    "toplam_bolum": len(unique_bolumler),
                    "cekilen_bolum": len(bolum_detaylari),
                    "bolumler": bolum_detaylari
                })
                basarili += 1
                print(f"      ✅ Eklendi! ({len(bolum_detaylari)}/{len(unique_bolumler)} bölüm)")
            else:
                basarisiz += 1
                print(f"      ❌ Video bulunamadı")
            
            time.sleep(random.uniform(0.5, 1.5))
        
        if sayfa < max_sayfa:
            wait_time = random.uniform(3, 6)
            print(f"\n   ⏳ {wait_time:.1f} saniye bekleniyor...")
            time.sleep(wait_time)
    
    print(f"\n📊 İSTATİSTİKLER:")
    print(f"   ✅ Başarılı: {basarili} dizi")
    print(f"   ❌ Başarısız: {basarisiz} dizi")
    print(f"   📈 Toplam: {len(tüm_diziler)} dizi")
    
    return tüm_diziler

def main():
    parser = argparse.ArgumentParser(description='HDFilmIzle Dizi Kazıyıcı')
    parser.add_argument('--max-pages', type=int, default=None, help='Maksimum sayfa sayısı')
    parser.add_argument('--max-episodes', type=int, default=10, help='Maksimum bölüm sayısı')
    parser.add_argument('--output', type=str, default='hdf/diziler', help='Çıktı dosya adı (uzantısız)')
    
    args = parser.parse_args()
    
    print("🎬 HDFilmIzle Dizi Kazıyıcı Başlatılıyor...")
    print("=" * 50)
    
    # Dizileri kazı
    diziler = dizi_kazı(max_sayfa=args.max_pages, max_episodes=args.max_episodes)
    
    # Veriyi hazırla
    veri = {
        "metadata": {
            "kazıma_tarihi": datetime.now().isoformat(),
            "kaynak": BASE_URL,
            "toplam_dizi": len(diziler),
            "max_episodes": args.max_episodes,
            "max_pages": args.max_pages
        },
        "diziler": diziler
    }
    
    # Kaydet
    os.makedirs("hdf", exist_ok=True)
    
    # JSON kaydet
    json_path = f"{args.output}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    print(f"\n✅ JSON kaydedildi: {json_path}")
    
    # YAML kaydet
    yaml_path = f"{args.output}.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(veri, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    print(f"✅ YAML kaydedildi: {yaml_path}")
    
    print(f"\n🎉 İşlem tamamlandı! {len(diziler)} dizi kazındı.")

if __name__ == "__main__":
    main()
