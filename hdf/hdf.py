#!/usr/bin/env python3
import os
import json
import re
import time
import random
import argparse
from curl_cffi import requests
import yaml
from datetime import datetime

BASE_URL = "https://www.hdfilmizle.now"

def get_headers():
    random_ip = f"{random.randint(1,254)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}"
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": BASE_URL,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
        "X-Forwarded-For": random_ip,
        "CF-Connecting-IP": random_ip,
        "True-Client-IP": random_ip
    }

def fetch_with_retry(url, max_retries=3, timeout=15):
    for deneme in range(1, max_retries + 1):
        try:
            headers = get_headers()
            headers["Cookie"] = f"__cf_bm={random.randint(100000, 999999)}"
            
            response = requests.get(url, headers=headers, impersonate="chrome", timeout=timeout)
            
            if response.status_code == 200:
                html = response.text
                if "cf-browser-verification" not in html and "Attention Required" not in html:
                    return html
            print(f"      Deneme {deneme}: HTTP {response.status_code}")
            time.sleep(1 * deneme)
        except Exception as e:
            print(f"      Deneme {deneme}: {str(e)[:50]}")
            time.sleep(1 * deneme)
    return None

def dizi_kazı(max_sayfa=2, max_episodes=10):
    print(f"📊 {max_sayfa} sayfa taranacak, max {max_episodes} bölüm/dizi")
    
    tüm_diziler = []
    
    for sayfa in range(1, max_sayfa + 1):
        print(f"\n🔄 Sayfa {sayfa}/{max_sayfa}")
        target_url = f"{BASE_URL}/yabanci-dizi-izle-3/page/{sayfa}/"
        
        html = fetch_with_retry(target_url)
        if not html:
            continue
        
        main_match = re.search(r'id="moviesListResult"([\s\S]*?)</nav>', html)
        if not main_match:
            continue
        
        card_regex = r'<a\s+href="([^"]+)"\s+title="([^"]+)"'
        matches = re.findall(card_regex, main_match.group(1))
        
        print(f"   📋 {len(matches)} dizi bulundu")
        
        for link, title in matches:
            print(f"\n   🎬 {title}")
            
            temiz_url = link if link.startswith("http") else BASE_URL + link
            dizi_match = re.match(r'(https://www\.hdfilmizle\.now/dizi/[^/]+/)', temiz_url)
            if dizi_match:
                temiz_url = dizi_match.group(1)
            
            detay_html = fetch_with_retry(temiz_url, max_retries=2)
            if not detay_html:
                continue
            
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
                b_html = fetch_with_retry(b_url, max_retries=1, timeout=8)
                
                if b_html:
                    v_match = re.search(r'vidrame\.pro/vr/([a-zA-Z0-9]+)', b_html)
                    if v_match:
                        bolumler.append({
                            "bolum_adi": f"Bölüm {len(bolumler)+1}",
                            "m3u8": f"https://vidrame.pro/vr/get/{v_match.group(1)}/master.m3u8"
                        })
                        print(f"         ✅ Bölüm {len(bolumler)} eklendi")
                
                time.sleep(0.3)
            
            if bolumler:
                tüm_diziler.append({
                    "title": title,
                    "url": temiz_url,
                    "toplam_bolum": len(bolum_links),
                    "cekilen_bolum": len(bolumler),
                    "bolumler": bolumler
                })
            
            time.sleep(0.5)
        
        time.sleep(2)
    
    return tüm_diziler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-pages', type=int, default=2)
    parser.add_argument('--max-episodes', type=int, default=10)
    args = parser.parse_args()
    
    print("🎬 HDFilmIzle Dizi Kazıyıcı")
    print("=" * 40)
    
    diziler = dizi_kazı(args.max_pages, args.max_episodes)
    
    veri = {
        "metadata": {
            "tarih": datetime.now().isoformat(),
            "toplam": len(diziler)
        },
        "diziler": diziler
    }
    
    os.makedirs("hdf", exist_ok=True)
    
    with open("hdf/diziler.json", "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ {len(diziler)} dizi kaydedildi: hdf/diziler.json")

if __name__ == "__main__":
    main()
