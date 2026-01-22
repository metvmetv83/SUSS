"""
Ortak Kullanımlar Modülü
========================
Bu modül, projedeki tüm Python dosyaları tarafından paylaşılan
fonksiyonları ve sabitleri içerir.

Kullanılan dosyalar:
- github.pyw
- server.pyw
- status_md.py
"""

import re
import os
import json
import html
import requests
import urllib3
from datetime import datetime
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin
from bs4 import BeautifulSoup
import subprocess
import socket

# SSL sertifika hatalarını konsola basmamak için
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Subprocess için Windows'ta pencere açılmasını engelleme flag'i
SUBPROCESS_FLAGS = subprocess.CREATE_NO_WINDOW

# ==================== SABİTLER ====================

CONFIG_FILE = "config.json"
M3U8_DIR = "m3u8"
TV_M3U8_FILE = "tv.m3u8"
LOG_FILE = "log.txt"
TIME_FORMAT = "%d.%m.%Y %H:%M:%S"

# Türkçe karakter dönüşüm tablosu
TURKISH_CHAR_MAP = {
    'ç': 'c', 'ğ': 'g', 'ı': 'i', 'ö': 'o', 'ş': 's', 'ü': 'u',
    'Ç': 'C', 'Ğ': 'G', 'İ': 'I', 'Ö': 'O', 'Ş': 'S', 'Ü': 'U'
}

# YouTube API sabitleri
YOUTUBE_HEADERS = {
    'origin': 'https://www.youtube.com',
    'referer': 'https://www.youtube.com/',
    'user-agent': 'Mozilla/5.0'
}
YOUTUBE_API_KEY = 'AIzaSyAO_FJ2SlqU8Q4STEHLGCilw_Y9_11qcW8'

# HTTP istekleri için varsayılan header
DEFAULT_HEADERS = {'user-agent': 'Mozilla/5.0'}

# ==================== LOG FONKSİYONU ====================

def log(message, to_file=True, to_console=True):
    """
    Mesajı log dosyasına ve/veya konsola yazar.
    
    Args:
        message: Log mesajı
        to_file: Dosyaya yaz (varsayılan: True)
        to_console: Konsola yaz (varsayılan: True)
    """
    timestamp = datetime.now().strftime(TIME_FORMAT)
    formatted = f"[{timestamp}] {message}"
    
    if to_console:
        print(f"[Log] {message}")
    
    if to_file:
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"{formatted}\n")
        except IOError as e:
            print(f"Log dosyasına yazma hatası: {e}")

# ==================== GÜNCELLEME İŞLEMLERİ ====================

def update_yt_dlp():
    """yt-dlp kütüphanesini günceller."""
    log("yt-dlp güncelleme kontrolü yapılıyor...")
    try:
        result = subprocess.run(
            ["yt-dlp", "-U"],
            capture_output=True,
            text=True,
            creationflags=SUBPROCESS_FLAGS,
            timeout=60
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if "up to date" in output:
                log("yt-dlp zaten güncel.")
            else:
                log(f"yt-dlp güncellendi: {output}")
        else:
            log(f"yt-dlp güncelleme hatası: {result.stderr.strip() or result.stdout.strip()}")
    except Exception as e:
        log(f"yt-dlp güncellenirken bir hata oluştu: {e}")

# ==================== DOSYA İŞLEMLERİ ====================

def sanitize_filename(filename):
    """
    Dosya adını güvenli hale getirir.
    - Türkçe karakterleri İngilizce karşılıklarına çevirir
    - Boşlukları alt çizgiye çevirir
    - Geçersiz karakterleri kaldırır
    
    Args:
        filename: Temizlenecek dosya adı
        
    Returns:
        str: Temizlenmiş dosya adı
    """
    for turkish, english in TURKISH_CHAR_MAP.items():
        filename = filename.replace(turkish, english)
    filename = re.sub(r'\s+', '_', filename)
    filename = re.sub(r'[^A-Za-z0-9_.-]', '', filename)
    return filename

def clean_link(link):
    """
    HTML entity'leri decode eder ve gereksiz karakterleri temizler.
    
    Args:
        link: Temizlenecek URL
        
    Returns:
        str: Temizlenmiş URL
    """
    decoded_link = html.unescape(link)
    stripped_link = decoded_link.strip().rstrip("'\",)")
    return stripped_link

def remove_nimblesessionid(url):
    """
    URL'den nimblesessionid parametresini kaldırır.
    
    Args:
        url: İşlenecek URL
        
    Returns:
        str: Temizlenmiş URL
    """
    if 'nimblesessionid' not in url:
        return url
    parsed = urlparse(url)
    qs = parse_qs(parsed.query, keep_blank_values=True)
    if 'nimblesessionid' in qs:
        del qs['nimblesessionid']
    new_query = urlencode(qs, doseq=True)
    return urlunparse(parsed._replace(query=new_query))

# ==================== CONFIG İŞLEMLERİ ====================

def load_config():
    """
    Config dosyasını yükler ve kanalları döndürür.
    Eski liste formatını yeni dict formatına dönüştürür.
    
    Returns:
        tuple: (channels_list, only_highest, view_mode)
    """
    if not os.path.exists(CONFIG_FILE):
        return [], 1, 0
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            only_highest = data.get("ONLY_HIGHEST", 1)
            view_mode = data.get("VIEW_MODE", 0)
            
            channels_raw = data.get("channels", [])
            migrated_channels = []
            
            for ch in channels_raw:
                if isinstance(ch, list):
                    # Eski format: ["NAME", "URL", AUTO_BOOL]
                    migrated_channels.append({
                        "name": ch[0] if len(ch) > 0 else "",
                        "url": ch[1] if len(ch) > 1 else "",
                        "auto": ch[2] if len(ch) > 2 else False
                    })
                elif isinstance(ch, dict):
                    # Yeni format: {"name": ..., "url": ..., "auto": ...}
                    migrated_channels.append({
                        "name": ch.get("name", ""),
                        "url": ch.get("url", ""),
                        "auto": ch.get("auto", False)
                    })
            
            return migrated_channels, only_highest, view_mode
            
    except Exception as e:
        log(f"Config dosyasından kanallar okunamadı: {e}")
        return [], 1, 0

def save_config(channels, only_highest=1, view_mode=0):
    """
    Kanal listesini ve ayarları config dosyasına kaydeder.
    
    Args:
        channels: Kanal listesi
        only_highest: Sadece en yüksek kalite ayarı
        view_mode: Görünüm modu
    """
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            config_data = {
                "ONLY_HIGHEST": only_highest,
                "VIEW_MODE": view_mode,
                "channels": channels
            }
            json.dump(config_data, f, indent=4, ensure_ascii=False)
            log("Config dosyası kaydedildi.")
    except Exception as e:
        log(f"Config kaydetme hatası: {e}")

def get_github_url(channel_name):
    """
    Kanal için GitHub raw URL'ini döndürür.
    
    Args:
        channel_name: Kanal adı
        
    Returns:
        str veya None: GitHub URL veya bulunamazsa None
    """
    filename = f"{sanitize_filename(channel_name).upper()}.m3u8"
    if os.path.exists(TV_M3U8_FILE):
        try:
            with open(TV_M3U8_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    if filename in line and line.strip().startswith("http"):
                        return line.strip()
        except:
            pass
    return None

# ==================== YOUTUBE FONKSİYONLARI ====================

def search_youtube_innertube(query):
    """
    YouTube InnerTube API kullanarak canlı yayın araması yapar.
    
    Args:
        query: Arama sorgusu
        
    Returns:
        str veya None: Bulunan video ID veya None
    """
    payload = {
        'context': {
            'client': {'clientName': 'WEB', 'clientVersion': '2.20240101.00.00'}
        },
        'query': query,
        'params': 'EgJAAQ%3D%3D'  # Canlı yayın filtresi
    }
    
    try:
        response = requests.post(
            'https://www.youtube.com/youtubei/v1/search',
            headers=YOUTUBE_HEADERS,
            json=payload,
            timeout=20
        )
        response.raise_for_status()
        data = response.json()
        
        contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [{}])[0].get('itemSectionRenderer', {}).get('contents', [])
        
        # Önce canlı yayınları ara
        for item in contents:
            if 'videoRenderer' in item:
                video_id = item['videoRenderer'].get('videoId')
                badges = item['videoRenderer'].get('badges', [])
                is_live = any(
                    b.get('metadataBadgeRenderer', {}).get('style') == 'BADGE_STYLE_TYPE_LIVE_NOW'
                    for b in badges
                )
                if video_id and is_live:
                    log(f"Canlı yayın bulundu: Video ID = {video_id}")
                    return video_id
        
        # Canlı yayın bulunamazsa ilk sonucu döndür
        for item in contents:
            if 'videoRenderer' in item and item['videoRenderer'].get('videoId'):
                video_id = item['videoRenderer']['videoId']
                log(f"Canlı yayın bulunamadı, ilk sonuç döndürülüyor: Video ID = {video_id}")
                return video_id
                
    except Exception as e:
        log(f"YouTube arama (InnerTube) hatası: {e}")
    
    return None

def search_youtube_channel(query):
    """
    YouTube'da kanal araması yapar.
    
    Args:
        query: Arama sorgusu
        
    Returns:
        str veya None: Bulunan kanal ID veya None
    """
    payload = {
        'context': {
            'client': {'clientName': 'WEB', 'clientVersion': '2.20240101.00.00'}
        },
        'query': query,
        'params': 'EgIQAg=='  # Kanal filtresi
    }
    
    try:
        response = requests.post(
            'https://www.youtube.com/youtubei/v1/search',
            headers=YOUTUBE_HEADERS,
            json=payload,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        contents = data.get('contents', {}).get('twoColumnSearchResultsRenderer', {}).get('primaryContents', {}).get('sectionListRenderer', {}).get('contents', [{}])[0].get('itemSectionRenderer', {}).get('contents', [])
        
        for item in contents:
            if 'channelRenderer' in item:
                return item['channelRenderer'].get('channelId')
                
    except Exception as e:
        log(f"YouTube Kanal Arama hatası: {e}")
    
    return None

def get_youtube_m3u8_url(video_or_channel_id):
    """
    YouTube video veya kanal ID'sinden m3u8 URL'ini alır.
    Öncelikle yt-dlp kullanarak deneme yapar, başarısız olursa Player API kullanır.
    
    Args:
        video_or_channel_id: Video ID, Kanal ID (@handle veya UCxxx) veya arama sorgusu
        
    Returns:
        str veya None: m3u8 URL veya None
    """
    target_url = video_or_channel_id
    video_id = None
    
    # 1. URL Hazırlama
    if not target_url.startswith('http'):
        if target_url.startswith('@'):
            target_url = f"https://www.youtube.com/{target_url}/live"
        elif target_url.startswith('UC'):
            target_url = f"https://www.youtube.com/channel/{target_url}/live"
        elif re.match(r'^[a-zA-Z0-9_-]{11}$', target_url):
            video_id = target_url
            target_url = f"https://www.youtube.com/watch?v={video_id}"
        else:
            # Arama sorgusu ise video ID bul
            video_id = search_youtube_innertube(target_url)
            if video_id:
                target_url = f"https://www.youtube.com/watch?v={video_id}"
            else:
                return None
    else:
        # URL'den video_id ayıkla (eğer varsa)
        match = re.search(r"v=([a-zA-Z0-9_-]{11})", target_url)
        if match:
            video_id = match.group(1)

    # 2. YT-DLP ile Deneme (Kullanıcı İsteği)
    try:
        # log(f"yt-dlp ile link alınıyor: {target_url}")
        result = subprocess.run(
            ["yt-dlp", "--print", "manifest_url", target_url],
            capture_output=True,
            text=True,
            creationflags=SUBPROCESS_FLAGS,
            timeout=15
        )
        if result.returncode == 0:
            output = result.stdout.strip()
            if output:
                # Birden fazla link dönerse ilkini al
                m3u8_url = output.splitlines()[0].strip()
                if m3u8_url and ("m3u8" in m3u8_url or m3u8_url.startswith('http')):
                    # log(f"yt-dlp başarılı: {target_url}")
                    return m3u8_url
    except Exception as e:
        log(f"yt-dlp hatası ({target_url}): {e}")

    # 3. YEDEK: Player API (InnerTube)
    if not video_id:
        # Eğer video_id hala yoksa (kanal URL'si ise) video_id'yi bulmaya çalış
        try:
            r = requests.get(target_url, headers=YOUTUBE_HEADERS, timeout=10)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            canonical_link = soup.find("link", rel="canonical")
            if canonical_link and canonical_link.get("href"):
                match = re.search(r"v=([a-zA-Z0-9_-]{11})", canonical_link.get("href"))
                if match:
                    video_id = match.group(1)
        except Exception:
            pass

    if video_id:
        params = {'key': YOUTUBE_API_KEY}
        json_data = {
            'context': {
                'client': {'clientName': 'WEB', 'clientVersion': '2.20231101.05.00'}
            },
            'videoId': video_id
        }
        
        try:
            response = requests.post(
                'https://www.youtube.com/youtubei/v1/player',
                params=params,
                headers=YOUTUBE_HEADERS,
                json=json_data,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            hls_url = data.get("streamingData", {}).get("hlsManifestUrl")
            if hls_url:
                log(f"Player API başarılı: {video_id}")
                return hls_url
        except requests.RequestException as e:
            log(f"m3u8 URL alma hatası (API): {e}")

    return None

# ==================== WEB SCRAPING ====================

def scrape_m3u8_from_website(url, channel_name=""):
    """
    Web sitesinden m3u8 linkini bulur.
    
    Args:
        url: Taranacak web sitesi URL'i
        channel_name: Log için kanal adı (opsiyonel)
        
    Returns:
        str veya None: Bulunan m3u8 URL veya None
    """
    try:
        log(f"Web sitesi taranıyor: {url}")
        r = requests.get(
            url,
            timeout=15,
            verify=False,
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        r.raise_for_status()
        content = r.text
        
        # m3u8 URL pattern'leri (öncelik sırasına göre)
        regex_patterns = [
            r'(https?://[^\s"\'`<>]+?\.m3u8\?[^\s"\'`<>]*app=[^\s"\'`<>]+)',
            r'(https?://[^\s"\'`<>]+?\.m3u8\?[^\s"\'`<>]+)',
            r'(https?://[^\s"\'`<>]+?\.m3u8)'
        ]
        
        found_links = set()
        for pattern in regex_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                found_links.add(clean_link(match))
            if found_links:
                break
        
        if channel_name:
            log(f"{channel_name} için {len(found_links)} adet M3U8 linki bulundu.")
        else:
            log(f"{len(found_links)} adet M3U8 linki bulundu.")
        
        return list(found_links)[0] if found_links else None
        
    except requests.RequestException as e:
        log(f"Web sitesi kazıma hatası ({url}): {e}")
        return None

# ==================== KANAL URL ÇÖZÜMLEME ====================

def resolve_channel_url(channel_info_or_url):
    """
    Kanal bilgisinden veya URL'den m3u8 linkini çözer.
    
    Args:
        channel_info_or_url: Kanal dict'i {"name": ..., "url": ...} veya string URL/ID
        
    Returns:
        tuple: (m3u8_url, channel_name)
    """
    # Dict ise config objesi
    if isinstance(channel_info_or_url, dict):
        channel_name = channel_info_or_url.get('name', 'İsimsiz')
        channel_id = channel_info_or_url.get('url', '')
    else:
        # String ise dinamik istek
        channel_name = "Dynamic Stream"
        channel_id = channel_info_or_url
    
    m3u8_url = None
    
    # Direkt m3u8 linki
    if channel_id.endswith('.m3u8'):
        m3u8_url = channel_id
    
    # HTTP URL (web sitesi)
    elif channel_id.startswith(('http://', 'https://')):
        m3u8_url = scrape_m3u8_from_website(channel_id, channel_name)
    
    # www. ile başlayan veya website formatında
    elif channel_id.startswith('www.') or ('.' in channel_id and ' ' not in channel_id and '/' in channel_id):
        if not channel_id.startswith(('http://', 'https://')):
            channel_id = "https://" + channel_id
        m3u8_url = scrape_m3u8_from_website(channel_id, channel_name)
    
    # YouTube ID veya arama sorgusu
    else:
        m3u8_url = get_youtube_m3u8_url(channel_id)
    
    return m3u8_url, channel_name

# ==================== YARDIMCI FONKSİYONLAR ====================

def get_resolution_label(height):
    """
    Çözünürlük yüksekliğine göre etiket döndürür.
    
    Args:
        height: Çözünürlük yüksekliği (piksel)
        
    Returns:
        str: " FULL HD", " HD", " SD" veya boş string
    """
    if not isinstance(height, int) or height <= 0:
        return ""
    if height >= 1080:
        return " FULL HD"
    elif height >= 720:
        return " HD"
    else:
        return " SD"

def get_m3u8_filename(channel_name):
    """
    Kanal adından m3u8 dosya adı oluşturur.
    
    Args:
        channel_name: Kanal adı
        
    Returns:
        str: Dosya adı (örn: "KANAL_ADI.m3u8")
    """
    return f"{sanitize_filename(channel_name).upper()}.m3u8"

def extract_stream_url(m3u8_content):
    """
    m3u8 içeriğinden ilk stream URL'ini çıkarır.
    
    Args:
        m3u8_content: m3u8 dosya içeriği (string)
        
    Returns:
        str veya None: Bulunan stream URL veya None
    """
    for line in m3u8_content.splitlines():
        line = line.strip()
        if line and not line.startswith('#') and line.startswith('http'):
            return line
    return None

# ==================== DURUM KONTROLÜ (STATUS CHECKS) ====================

def check_source_status(channel_data):
    """
    Kanalın kaynak (M3U8) durumunu kontrol eder.
    
    Args:
        channel_data: Kanal konfigürasyon dict'i
        
    Returns:
        tuple: (status ["operational"|"outage"], error_msg [str])
    """
    try:
        m3u8, _ = resolve_channel_url(channel_data)
        if m3u8:
            return "operational", ""
        return "outage", "Bulunamadı"
    except Exception as e:
        return "outage", str(e)

def check_github_status(github_url):
    """
    GitHub'daki dosyanın erişilebilirliğini kontrol eder.
    
    Args:
        github_url: GitHub raw dosya URL'i
        
    Returns:
        tuple: (status ["operational"|"outage"], error_msg [str])
    """
    if not github_url:
        return "outage", "Playlist'te Yok"
        
    try:
        # Cache busting için timestamp ekle
        url = f"{github_url}?t={int(datetime.now().timestamp())}"
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=5)
        if r.status_code == 200:
            return "operational", ""
        return "outage", str(r.status_code)
    except Exception as e:
        return "outage", str(e)

def check_stream_status(github_url):
    """
    GitHub'daki dosya içeriğinden asıl yayın linkini bulup test eder.
    
    Args:
        github_url: GitHub raw dosya URL'i
        
    Returns:
        tuple: (status ["operational"|"outage"], error_msg [str])
    """
    if not github_url:
        return "outage", "Dosya Yok"
        
    try:
        # Önce GitHub'dan içeriği al
        url = f"{github_url}?t={int(datetime.now().timestamp())}"
        r = requests.get(url, headers=DEFAULT_HEADERS, timeout=5)
        
        if r.status_code != 200:
            return "outage", "Github Dosya Hatası"

        stream_url = extract_stream_url(r.text)
        
        if not stream_url:
            return "outage", "Boş İçerik"

        # Yayını test et
        try:
            r_stream = requests.get(
                stream_url, 
                headers=DEFAULT_HEADERS, 
                stream=True, 
                timeout=5, 
                verify=False
            )
            if r_stream.status_code < 400:
                return "operational", ""
            else:
                return "outage", f"Hata ({r_stream.status_code})"
        except requests.exceptions.Timeout:
            return "outage", "Timeout"
        except Exception as e:
            return "outage", str(e)

    except Exception as e:
        return "outage", str(e)

def get_ipv4_address():
    """
    Yerel IPv4 adresini döndürür.
    
    Returns:
        str: IPv4 adresi
    """
    try:
        hostname = socket.gethostname()
        ip = socket.gethostbyname(hostname)
        if ip and not ip.startswith("127."):
            return ip
    except Exception:
        pass
    try:
        result = subprocess.run(
             ["ipconfig"],
            capture_output=True,
            text=True,
             creationflags=SUBPROCESS_FLAGS
        )
        matches = re.findall(r"(?:IPv4.*?:\s*)(\d+\.\d+\d+\.\d+)", result.stdout)
        if matches:
            return matches[0]
    except Exception:
        pass
    return "127.0.0.1"

def get_server_url(path, port=5000):
    """
    Verilen yol ve port için tam sunucu URL'ini oluşturur.
    
    Args:
        path: URL yolu (örn: 'kanal_id')
        port: Port numarası (varsayılan: 5000)
        
    Returns:
        str: Tam URL (örn: 'http://192.168.1.1:5000/kanal_id')
    """
    host = get_ipv4_address()
    # Path başında / varsa kaldır
    path = path.lstrip('/')
    return f"http://{host}:{port}/{path}"

def get_git_remote_url():
    """
    Git remote origin URL'sini alır.
    
    Returns:
        str veya None: Git remote URL veya bulunamazsa None
    """
    try:
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            capture_output=True,
            text=True,
            creationflags=SUBPROCESS_FLAGS
        )
        url = result.stdout.strip()
        # .git uzantısını kaldır
        if url and url.endswith('.git'):
            url = url[:-4]
        return url if url else None
    except Exception as e:
        log(f"Git remote URL alınamadı: {e}")
        return None
