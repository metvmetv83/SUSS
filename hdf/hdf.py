import requests
import re
import json
import time
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin

class HDFilmIzleAPI:
    def __init__(self):
        self.base_url = "https://www.hdfilmizle.now"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
            "Referer": self.base_url
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def get_list(self, tip: str = "film", sayfa: int = 1, sadece_liste: bool = False) -> Dict:
        """
        Film veya dizi listesini çeker
        
        Args:
            tip: "film" veya "dizi"
            sayfa: Sayfa numarası
            sadece_liste: True ise sadece liste döner (detayları çekmez)
        """
        if tip == "dizi":
            target_url = f"{self.base_url}/yabanci-dizi-izle-3/page/{sayfa}/"
        else:
            target_url = f"{self.base_url}/page/{sayfa}/"
        
        try:
            response = self.session.get(target_url, timeout=30)
            response.raise_for_status()
            html = response.text
            
            # Ana içeriği al
            main_content_match = re.search(r'id="moviesListResult"([\s\S]*?)</nav>', html)
            if not main_content_match:
                return {"durum": "hata", "mesaj": "Ana içerik alanı bulunamadı"}
            
            list_html = main_content_match.group(1)
            
            # Kartları bul
            card_pattern = r'<a\s+href="([^"]+)"\s+title="([^"]+)"[^>]*class="([^"]*poster[^"]*)"[^>]*>([\s\S]*?)</a>'
            matches = re.findall(card_pattern, list_html, re.IGNORECASE)
            
            kartlar = []
            seen_urls = set()
            
            for match in matches:
                link, title, _, card_inner = match
                title = title.strip()
                
                # Poster URL
                poster = ""
                data_src_match = re.search(r'data-src="([^"]+)"', card_inner)
                if data_src_match:
                    poster = data_src_match.group(1)
                else:
                    src_match = re.search(r'src="([^"]+)"', card_inner)
                    if src_match:
                        poster = src_match.group(1)
                
                # URL temizleme
                clean_url = link if link.startswith("http") else urljoin(self.base_url, link)
                
                if tip == "dizi":
                    dizi_match = re.match(r'(https://www\.hdfilmizle\.now/dizi/[^/]+/)', clean_url)
                    if dizi_match:
                        clean_url = dizi_match.group(1)
                
                if poster and not poster.startswith("http"):
                    poster = urljoin(self.base_url, poster)
                
                if clean_url not in seen_urls:
                    seen_urls.add(clean_url)
                    kartlar.append({
                        "url": clean_url,
                        "title": title,
                        "poster": poster
                    })
            
            if sadece_liste:
                return {
                    "durum": "basarili",
                    "tip": tip,
                    "sayfa": sayfa,
                    "toplam_kart": len(kartlar),
                    "veriler": kartlar
                }
            
            # Detayları çek
            sonuclar = []
            for i, kart in enumerate(kartlar):
                print(f"İşleniyor ({i+1}/{len(kartlar)}): {kart['title']}")
                detay = self.get_detail(kart["url"], tip, kart["title"], kart["poster"])
                if detay:
                    sonuclar.append(detay)
                time.sleep(0.5)  # Rate limiting
            
            return {
                "durum": "basarili",
                "tip": tip,
                "sayfa": sayfa,
                "toplam_kart": len(kartlar),
                "basarili_cekme": len(sonuclar),
                "basarisiz_cekme": len(kartlar) - len(sonuclar),
                "veriler": sonuclar
            }
            
        except Exception as e:
            return {"durum": "hata", "mesaj": str(e)}
    
    def get_detail(self, url: str, tip: str, title: str, poster: str) -> Optional[Dict]:
        """Film veya dizi detaylarını çeker"""
        
        for deneme in range(3):  # 3 kez dene
            try:
                response = self.session.get(url, timeout=20)
                if response.status_code != 200:
                    time.sleep(1 * (deneme + 1))
                    continue
                
                html = response.text
                
                # Cloudflare kontrolü
                if "cf-browser-verification" in html or "Attention Required" in html:
                    print(f"  ⚠️ Cloudflare koruması (deneme {deneme + 1})")
                    time.sleep(2 * (deneme + 1))
                    continue
                
                if tip == "film":
                    return self._parse_film(html, title, poster, url)
                else:
                    return self._parse_dizi(html, title, poster, url)
                
            except Exception as e:
                print(f"  ⚠️ Hata (deneme {deneme + 1}): {str(e)}")
                time.sleep(1 * (deneme + 1))
        
        return None
    
    def _parse_film(self, html: str, title: str, poster: str, url: str) -> Dict:
        """Film detaylarını parse et"""
        patterns = [
            r'<iframe[^>]+(?:data-src|src)="([^"]*vidrame\.pro/vr/([a-zA-Z0-9]+)[^"]*)"',
            r'<iframe[^>]+(?:data-src|src)="([^"]*\.(?:m3u8|mp4)[^"]*)"',
            r'(?:file|source):\s*["\']([^"\']*\.m3u8[^"\']*)["\']'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                if match.group(2):  # vidrame.pro pattern
                    m3u8 = f"https://vidrame.pro/vr/get/{match.group(2)}/master.m3u8"
                else:
                    m3u8 = match.group(1)
                
                return {
                    "title": title,
                    "poster": poster,
                    "url": url,
                    "m3u8": m3u8
                }
        
        return None
    
    def _parse_dizi(self, html: str, title: str, poster: str, url: str) -> Optional[Dict]:
        """Dizi detaylarını parse et"""
        bolumler = []
        
        # Farklı pattern'lerle bölümleri bul
        patterns = [
            r'<a[^>]+href="([^"]*/sezon-\d+/bolum-\d+/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>[\s\S]*?</a>',
            r'<a[^>]+href="([^"]*/bolum-\d+/[^"]*)"[^>]*>[\s\S]*?<h3[^>]*>([\s\S]*?)</h3>[\s\S]*?</a>',
            r'<a[^>]+href="([^"]*/sezon[^"]*/bolum[^"]*)"[^>]+title="([^"]+)"[^>]*>',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for match in matches:
                bolum_url = match[0] if match[0].startswith("http") else urljoin(self.base_url, match[0])
                bolum_title = re.sub(r'<[^>]*>', '', match[1]).strip() if len(match) > 1 else f"Bölüm {len(bolumler)+1}"
                bolumler.append({"title": bolum_title, "url": bolum_url})
        
        # Benzersiz bölümler
        seen = set()
        unique_bolumler = []
        for bolum in bolumler:
            if bolum["url"] not in seen:
                seen.add(bolum["url"])
                unique_bolumler.append(bolum)
        
        if not unique_bolumler:
            return None
        
        # İlk 15 bölümü al
        max_episodes = min(len(unique_bolumler), 15)
        bolum_detaylari = []
        
        for i, bolum in enumerate(unique_bolumler[:max_episodes]):
            m3u8 = self._get_episode_video(bolum["url"])
            if m3u8:
                bolum_detaylari.append({
                    "bolum_adi": bolum["title"],
                    "bolum_url": bolum["url"],
                    "m3u8": m3u8
                })
            time.sleep(0.1)  # Rate limiting
        
        if bolum_detaylari:
            return {
                "title": title,
                "poster": poster,
                "url": url,
                "toplam_bolum": len(unique_bolumler),
                "cekilen_bolum": len(bolum_detaylari),
                "bolumler": bolum_detaylari
            }
        
        return None
    
    def _get_episode_video(self, url: str) -> Optional[str]:
        """Bölümün video linkini bul"""
        for deneme in range(2):
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code != 200:
                    continue
                
                html = response.text
                
                patterns = [
                    r'<iframe[^>]+(?:data-src|src)="([^"]*vidrame\.pro/vr/([a-zA-Z0-9]+)[^"]*)"',
                    r'<iframe[^>]+(?:data-src|src)="([^"]*\.(?:m3u8|mp4)[^"]*)"',
                    r'(?:file|source):\s*["\']([^"\']*\.m3u8[^"\']*)["\']'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, html, re.IGNORECASE)
                    if match:
                        if match.group(2):
                            return f"https://vidrame.pro/vr/get/{match.group(2)}/master.m3u8"
                        else:
                            return match.group(1)
                
            except Exception:
                pass
            
            time.sleep(0.5)
        
        return None


# Kullanım örneği
if __name__ == "__main__":
    api = HDFilmIzleAPI()
    
    # Film listesi al
    print("=== Film Listesi (Sayfa 1) ===")
    filmler = api.get_list(tip="film", sayfa=1, sadece_liste=True)
    print(json.dumps(filmler, indent=2, ensure_ascii=False))
    
    # Dizi listesi al (detaylı)
    print("\n=== Dizi Listesi (Sayfa 9) ===")
    diziler = api.get_list(tip="dizi", sayfa=9)
    print(json.dumps(diziler, indent=2, ensure_ascii=False))
    
    # Tek bir film detayı al
    print("\n=== Tek Film Detayı ===")
    film_detay = api.get_detail(
        "https://www.hdfilmizle.now/film/example-film/",
        "film",
        "Örnek Film",
        "https://www.hdfilmizle.now/poster.jpg"
    )
    if film_detay:
        print(json.dumps(film_detay, indent=2, ensure_ascii=False))
