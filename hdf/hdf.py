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
    """Gerçek bir tarayıcı gibi görün"""
    random_ip = f"{random.randint(1,254)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,254)}"
    return {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "accept-language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
        "accept-encoding": "gzip, deflate, br",
        "referer": "https://www.google.com/",
        "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "cross-site",
        "upgrade-insecure-requests": "1",
        "x-forwarded-for": random_ip,
        "cf-connecting-ip": random_ip,
        "true-client-ip": random_ip,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def get_with_retry(url, max_retries=5):
    """Retry mekanizmalı istek"""
    for i in range(max_retries):
        try:
            # Farklı impersonate dene
            impersonate_list = ["chrome", "chrome110", "chrome116", "safari15_5", "edge101"]
            impersonate = random.choice(impersonate_list)
            
            response = requests.get(
                url, 
                headers=get_headers(), 
                impersonate=impersonate,
                timeout=30,
                verify=False  # SSL sorunları için
            )
            
            if response.status_code == 200:
                return response
            
            print(f"   Deneme {i+1}/{max_retries}: HTTP {response.status_code}")
            
            # Rate limiting için bekle
            time.sleep(random.uniform(3, 7))
            
        except Exception as e:
            print(f"   Deneme {i+1}/{max_retries} başarısız: {str(e)[:50]}")
            time.sleep(random.uniform(3, 7))
    
    return None

def get_total_pages(tip: str = "dizi") -> int:
    """Toplam sayfa sayısını bul"""
    if tip == "dizi":
        url = f"{BASE_URL}/yabanci-dizi-izle-3/"
    else:
        url = f"{BASE_URL}/"
    
    response = get_with_retry(url)
    if response and response.status_code == 200:
        page_links = re.findall(r'/page/(\d+)/', response.text)
        if page_links:
            return max(int(p) for p in page_links)
    
    return 2  # Varsayılan olarak 2 sayfa dene

def dizi_kazı(max_sayfa: int = None, max_episodes: int = 20):
    """Tüm dizileri kazı"""
    if max_sayfa is None:
        max_sayfa = get_total_pages("dizi")
        print(f"📊 Toplam {max_sayfa} sayfa bulundu")
    
    tüm_diziler = []
    
    for sayfa in range(1, max_sayfa + 1):
        print(f"\n🔄 [DİZİ] Sayfa {sayfa}/{max_sayfa} taranıyor...")
        target_url = f"{BASE_URL}/yabanci-dizi-izle-3/page/{sayfa}/"
        
        response = get_with_retry(target_url)
        if not response or response.status_code != 200:
            print(f"⚠️ Sayfa {sayfa} {max_sayfa} denemeden sonra yüklenemedi")
            continue
        
        html = response.text
        
        # Önce Cloudflare kontrolü
        if "cf-browser-verification" in html or "Attention Required" in html:
            print(f"⚠️ Sayfa {sayfa} Cloudflare korumasında")
            continue
        
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
            
            print(f"   🎬 {title}")
            
            # Her dizi için uzun bekleme
            time.sleep(random.uniform(3, 5))
            
            dizi_response = get_with_retry(temiz_url)
            if not dizi_response:
                print(f"      ❌ Detay sayfası alınamadı")
                continue
            
            detay_html = dizi_response.text
            
            # Bölümleri bul
            bolum_pattern = r'<a[^>]+href="([^"]*/sezon-\d+/bolum-\d+/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>'
            bolum_matches = re.findall(bolum_pattern, detay_html, re.IGNORECASE)
            
            if not bolum_matches:
                bolum_pattern = r'<a[^>]+href="([^"]*/bolum-\d+/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>'
                bolum_matches = re.findall(bolum_pattern, detay_html, re.IGNORECASE)
            
            if not bolum_matches:
                print(f"      ⚠️ Bölüm bulunamadı")
                continue
            
            print(f"      📺 {len(bolum_matches)} bölüm bulundu")
            
            bolum_detaylari = []
            for b_link, b_title in bolum_matches[:max_episodes]:
                b_url = b_link if b_link.startswith("http") else BASE_URL + b_link
                
                time.sleep(random.uniform(1, 2))
                
                b_response = get_with_retry(b_url)
                if b_response:
                    v_match = re.search(r'<iframe[^>]+(?:data-src|src)="([^"]*vidrame\.pro/vr/([a-zA-Z0-9]+)[^"]*)"', b_response.text, re.IGNORECASE)
                    if v_match:
                        bolum_detaylari.append({
                            "bolum_adi": b_title.strip(),
                            "bolum_url": b_url,
                            "m3u8": f"https://vidrame.pro/vr/get/{v_match.group(2)}/master.m3u8"
                        })
                        print(f"         ✅ {b_title.strip()}")
                    else:
                        print(f"         ⚠️ {b_title.strip()} - video bulunamadı")
            
            if bolum_detaylari:
                tüm_diziler.append({
                    "title": title,
                    "poster": poster,
                    "url": temiz_url,
                    "toplam_bolum": len(bolum_matches),
                    "cekilen_bolum": len(bolum_detaylari),
                    "bolumler": bolum_detaylari
                })
                print(f"      ✅ Eklendi: {len(bolum_detaylari)} bölüm")
        
        # Sayfalar arası uzun bekleme
        if sayfa < max_sayfa:
            wait_time = random.uniform(10, 20)
            print(f"   ⏳ {wait_time:.1f} saniye bekleniyor...")
            time.sleep(wait_time)
    
    return tüm_diziler

def main():
    parser = argparse.ArgumentParser(description='HDFilmIzle Kazıyıcı')
    parser.add_argument('--dizi', action='store_true', help='Sadece dizileri kazı')
    parser.add_argument('--both', action='store_true', help='Her ikisi')
    parser.add_argument('--max-pages', type=int, default=None)
    parser.add_argument('--max-episodes', type=int, default=10)
    
    args = parser.parse_args()
    
    print("🎬 HDFilmIzle Kazıyıcı Başlatılıyor...")
    print("=" * 50)
    
    veri = {
        "metadata": {
            "kazıma_tarihi": datetime.now().isoformat(),
            "kaynak": BASE_URL
        }
    }
    
    if args.dizi or args.both:
        print("\n📺 DİZİLER KAZINIYOR...")
        veri["diziler"] = dizi_kazı(max_sayfa=args.max_pages, max_episodes=args.max_episodes)
        print(f"\n✅ Toplam {len(veri['diziler'])} dizi kazındı")
    
    # Kaydet
    os.makedirs("hdf", exist_ok=True)
    
    with open("hdf/data.json", "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False, indent=2)
    
    with open("hdf/data.yaml", "w", encoding="utf-8") as f:
        yaml.dump(veri, f, allow_unicode=True, default_flow_style=False)
    
    print("\n✅ Kaydedildi: hdf/data.json, hdf/data.yaml")

if __name__ == "__main__":
    main()
