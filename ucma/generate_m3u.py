#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import sys
import time
import random
import shutil
import os
from datetime import datetime

def get_hls_with_ytdlp_ytse(video_id):
    """
    yt-dlp kullanarak YouTube canlı yayınından HLS bağlantısını al
    """
    # GitHub Actions ortamında doğrudan 'yt-dlp' komutunu kullanmak en güvenlisidir
    # Çünkü pip install ile PATH'e otomatik eklenir.
    yt_dlp_cmd = 'yt-dlp'
    
    # Eğer özel bir path gerekirse shutil.which kontrolü yeterlidir
    if not shutil.which(yt_dlp_cmd):
        yt_dlp_cmd = sys.executable + " -m yt_dlp" # Modül olarak çağırma yedeği

    cmd = [
        yt_dlp_cmd,
        '--no-warnings',
        '--no-cache-dir',
        '-g', 
        '-f', 'best',
        f'https://www.youtube.com/watch?v={video_id}'
    ]
    
    try:
        # stdout=PIPE ve stderr=PIPE kullanarak çıktıları yakalıyoruz
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=40 # YouTube bazen yavaş yanıt verebilir, süreyi biraz artırdık
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            # Bazı durumlarda birden fazla link dönebilir, ilk m3u8 linkini alalım
            links = output.split('\n')
            for link in links:
                if '.m3u8' in link or 'manifest' in link:
                    return link
            return links[0] if links else None
        else:
            print(f"      ⚠️ Hata çıktısı: {result.stderr[:100]}")
                
    except Exception as e:
        print(f"      ⚠️ Beklenmedik Hata: {str(e)[:50]}")
    
    return None

def generate_m3u():
    print(f"\n🎬 YouTube M3U Jeneratör - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    input_file = 'ids.txt'
    output_file = 'metube.m3u' # YAML dosyanızdaki isimle uyumlu hale getirdik
    
    if not os.path.exists(input_file):
        print(f"❌ {input_file} bulunamadı!")
        return False
    
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    m3u_content = ['#EXTM3U']
    success_count = 0
    total = len(lines)
    
    for idx, line in enumerate(lines, 1):
        parts = line.split('|')
        if len(parts) < 2: # Logo opsiyonel olabilir
            continue
        
        name = parts[0]
        url = parts[1]
        logo = parts[2] if len(parts) > 2 else ""
        
        # URL'den ID çıkarma (farklı URL formatlarını desteklemek için)
        if 'v=' in url:
            video_id = url.split('v=')[1].split('&')[0]
        elif 'youtu.be/' in url:
            video_id = url.split('youtu.be/')[1].split('?')[0]
        else:
            video_id = url

        print(f"📺 [{idx}/{total}] {name} (ID: {video_id})")
        
        hls_url = get_hls_with_ytdlp_ytse(video_id)
        
        if hls_url:
            m3u_content.append(f'#EXTINF:-1 tvg-id="{video_id}" tvg-name="{name}" tvg-logo="{logo}" group-title="Canlı TV",{name}')
            m3u_content.append(hls_url)
            print(f"   ✅ BAŞARILI!")
            success_count += 1
        else:
            print(f"   ❌ BAŞARISIZ")
        
        # GitHub Actions'ta çok fazla bekleme yapmak süreyi uzatır. 
        # Eğer kanal sayınız azsa (10-20) süreyi 3-5 saniyeye çekebilirsiniz.
        if idx < total:
            wait_time = random.randint(3, 7) 
            time.sleep(wait_time)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(m3u_content))
    
    print(f"\n📊 ÖZET: {success_count}/{total} kanal başarılı. Dosya: {output_file}")
    return success_count > 0

if __name__ == '__main__':
    generate_m3u()
