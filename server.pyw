import re
import requests
from flask import Flask, Response, abort, render_template_string, request, jsonify, send_from_directory
from datetime import datetime
import os
import signal
import threading
import time
import subprocess

# Ortak modülü import et
from common import (
    log, load_config, save_config,
    clean_link, scrape_m3u8_from_website, get_youtube_m3u8_url,
    search_youtube_innertube, search_youtube_channel, resolve_channel_url,
    remove_nimblesessionid, CONFIG_FILE, get_github_url,
    DEFAULT_HEADERS, get_m3u8_filename, extract_stream_url,
    check_source_status, check_github_status, check_stream_status,
    get_ipv4_address, get_server_url, SUBPROCESS_FLAGS
)
from urllib.parse import urljoin

app = Flask(__name__)

def flask_load_config():
    """Flask app config'ine kanal verilerini yükler."""
    channels, only_highest, view_mode = load_config()
    app.config["CHANNELS"] = channels
    app.config["ONLY_HIGHEST"] = only_highest
    app.config["VIEW_MODE"] = view_mode

def flask_save_config():
    """Flask app config'inden verileri dosyaya kaydeder."""
    save_config(
        app.config.get("CHANNELS", []),
        app.config.get("ONLY_HIGHEST", 1),
        app.config.get("VIEW_MODE", 0)
    )

@app.route('/')
def index():
    flask_load_config()
    # server_ip = get_ipv4_address() # get_server_url içinde çağrılıyor artık
    kanal_links = []
    for channel_data in app.config.get('CHANNELS', []):
        name = channel_data.get('name', 'İsimsiz')
        url = channel_data.get('url', '')
        full_url = get_server_url(url)
        kanal_links.append((name, full_url))
    
    view_mode = app.config.get("VIEW_MODE", 0)

    # --- HTML ŞABLONU GÜNCELLENDİ (OTOMASYON, EMOJİSİZ, TÜRKÇE) ---
    html_template = '''
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>IPTV Server</title>
        <style>
            body { background: #181818; color: #f1f1f1; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; margin: 0; padding: 0; }
            .container { background: #232323; padding: 20px; min-height: 100vh; max-width: 1200px; margin: 0 auto; }
            h1 { color: #ff5252; text-align: center; margin-top: 0; padding-top: 10px; }
            a { color: #90caf9; text-decoration: none; }
            
            /* TABLO STİLLERİ */
            .channel-table { width: 100%; border-collapse: separate; border-spacing: 0; margin-top: 20px; background: #333; border-radius: 8px; overflow: hidden; }
            .channel-table th, .channel-table td { padding: 12px 15px; text-align: left; border-bottom: 1px solid #444; vertical-align: middle; }
            .channel-table th { background: #2c2c2c; color: #ff5252; text-transform: uppercase; font-size: 0.85em; letter-spacing: 1px; }
            .channel-table tr:hover { background: #3a3a3a; transition: background 0.2s; }
            .channel-table td a { font-weight: 600; font-size: 1.1em; display: block; }
            
            /* DETAYLI MOD (3 Sütun) */
            .status-cell { display: flex; align-items: center; gap: 8px; font-size: 0.9em; }
            .dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
            .dot.operational { background: #238636; box-shadow: 0 0 5px #238636; }
            .dot.outage { background: #da3633; box-shadow: 0 0 5px #da3633; }
            .dot.checking { background: #e3b341; animation: pulse 1s infinite; }

            /* EYLEM ODAKLI MOD */
            .action-badge {
                display: inline-flex; flex-direction: column; align-items: center; justify-content: center;
                padding: 6px 12px; border-radius: 6px; min-width: 110px; text-align: center;
                transition: transform 0.2s; cursor: default;
            }
            .action-badge:hover { transform: scale(1.02); }
            
            .action-title { font-weight: 800; font-size: 0.95em; text-transform: uppercase; letter-spacing: 0.5px; line-height: 1.2; }
            .action-reason { font-weight: 400; font-size: 0.75em; opacity: 0.9; margin-top: 2px; }

            /* Renk Temaları */
            .theme-success { background: rgba(35, 134, 54, 0.2); border: 1px solid #238636; color: #4cd964; }
            .theme-purple  { background: rgba(142, 68, 173, 0.2); border: 1px solid #8e44ad; color: #d2b4de; }
            .theme-orange  { background: rgba(211, 84, 0, 0.2); border: 1px solid #d35400; color: #e59866; }
            .theme-red     { background: rgba(192, 57, 43, 0.2); border: 1px solid #c0392b; color: #e6b0aa; }
            .theme-gray    { background: rgba(127, 140, 141, 0.2); border: 1px solid #7f8c8d; color: #bdc3c7; }
            .theme-check   { background: rgba(241, 196, 15, 0.1); border: 1px solid #f1c40f; color: #f1c40f; animation: pulse 1.5s infinite; }

            @keyframes pulse { 0% { opacity: 0.6; } 50% { opacity: 1; } 100% { opacity: 0.6; } }

            .btn-group { margin-top: 30px; text-align: center; display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; }
            .btn { padding: 10px 20px; border-radius: 5px; font-weight: bold; background: #333; color: white; border: 1px solid #555; }
            .btn:hover { background: #444; }
            .btn-red { background: #922b21; border-color: #c0392b; }
            .btn-red:hover { background: #c0392b; }

            /* ARAMA ÇUBUĞU */
            .search-container { margin-top: 25px; display: flex; gap: 10px; background: #2c2c2c; padding: 10px; border-radius: 8px; border: 1px solid #444; }
            #dynamicSearch { 
                flex: 1; padding: 12px; border-radius: 6px; border: 1px solid #555; 
                background: #181818; color: white; font-size: 1em; outline: none;
            }
            #dynamicSearch:focus { border-color: #ff5252; }
            .search-btn { 
                padding: 10px 20px; border-radius: 6px; border: none; 
                background: #ff5252; color: white; font-weight: bold; cursor: pointer;
                transition: background 0.2s;
            }
            .search-btn:hover { background: #ff1744; }

            /* MOBİL UYUMLULUK */
            @media (max-width: 768px) {
                .container { padding: 10px 5px; width: 100%; box-sizing: border-box; }
                h1 { font-size: 1.5em; margin-bottom: 15px; }
                
                /* TABLO GENEL */
                .channel-table { table-layout: fixed; width: 100%; border-radius: 0; }
                .channel-table td { padding: 12px 6px; border-bottom: 1px solid #444; vertical-align: middle; }
                
                /* 1. Sütun: # SIRA NO - GİZLE (Yer açmak için) */
                .col-index, .channel-table th:first-child, .channel-table td:first-child { display: none; }

                /* 2. Sütun: KANAL ADI (Esnek Genişlik) */
                .channel-table td:nth-child(2) { 
                    width: auto; 
                    padding-left: 10px;
                }
                .channel-table td a { 
                    font-size: 1.1em; /* Kanal isimleri büyük ve okunabilir kalsın */
                    font-weight: 600;
                    white-space: normal; 
                    line-height: 1.3;
                    word-wrap: break-word;
                }

                /* --- EYLEM ODAKLI MOD (ACTION) --- */
                /* Başlık */
                .th-action { 
                    width: 125px !important; /* Geniş alan ayır */
                    text-align: center;
                }

                /* EYLEM KARTI TASARIMI */
                .action-badge { 
                    min-width: unset; 
                    width: 100%; 
                    box-sizing: border-box;
                    padding: 8px 4px; 
                    border-radius: 8px; /* Yuvarlak köşeler */
                    display: flex;
                    flex-direction: column;
                    justify-content: center;
                    border: none; /* Kenarlık yok, temiz görünüm */
                    box-shadow: 0 2px 4px rgba(0,0,0,0.3); /* Hafif gölge */
                }
                
                /* EYLEM YAZILARI */
                .action-title { 
                    font-size: 1em !important; /* ~16px */
                    font-weight: 800; 
                    letter-spacing: 0.5px;
                    margin-bottom: 3px;
                    line-height: 1.1;
                    display: block;
                }
                .action-reason { 
                    font-size: 0.75em !important; /* ~12px (Okunabilir alt sınır) */
                    font-weight: 500; 
                    opacity: 0.9; 
                    display: block; 
                    white-space: nowrap; /* Alt alta geçmesin, sığmazsa taşsın */
                    overflow: hidden;
                    text-overflow: ellipsis;
                }
                
                /* Renk Temaları (Masaüstü ile aynı yazı renkleri) */
                .theme-success { background: #1b5e20; color: #4cd964; }
                .theme-purple  { background: #4a148c; color: #d2b4de; }
                .theme-orange  { background: #7e5109; color: #e59866; }
                .theme-red     { background: #641e16; color: #e6b0aa; }
                .theme-gray    { background: #424242; color: #bdc3c7; }
                .theme-check   { background: #827717; color: #f1c40f; }

                /* --- DETAYLI MOD (DETAILED) --- */
                /* Başlıkları Kısalt (K, G, Y) */
                .th-source, .th-github, .th-stream { 
                    width: 32px !important; 
                    text-align: center !important; 
                    padding: 5px 0 !important;
                    font-size: 0 !important; 
                }
                .th-source::after { content: 'K'; font-size: 14px; font-weight:bold; color:#aaa; }
                .th-github::after { content: 'G'; font-size: 14px; font-weight:bold; color:#aaa; }
                .th-stream::after { content: 'Y'; font-size: 14px; font-weight:bold; color:#aaa; }

                /* Hücre İçeriği (Sadece Büyük Noktalar) */
                .status-cell { justify-content: center; width: 100%; }
                .status-cell .text { display: none; } 
                .dot { width: 16px; height: 16px; border: 1px solid rgba(255,255,255,0.2); }

                /* Butonlar */
                .btn-group { flex-direction: column; width: 100%; gap: 12px; margin-top: 25px; }
                .btn { width: 100%; padding: 15px; font-size: 1.1em; }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>IPTV Server</h1>
            
            <!-- DİNAMİK ARAMA ÇUBUĞU -->
            <div class="search-container">
                <input type="text" id="dynamicSearch" placeholder="Kanal adı, Video ID veya Web Adresi girin..." onkeypress="if(event.key === 'Enter') handleDynamicSearch()">
                <button class="search-btn" onclick="handleDynamicSearch()">İZLE</button>
            </div>

            <table class="channel-table">
                <thead>
                    <tr>
                        <th class="col-index" style="width: 30px; text-align: center;">#</th>
                        <th>Kanal</th>
                        {% if view_mode == 0 %}
                            <th class="th-source">Kaynak</th>
                            <th class="th-github">GitHub</th>
                            <th class="th-stream">Yayın</th>
                        {% else %}
                            <th class="th-action" style="text-align: center; width: 140px;">Durum & Eylem</th>
                        {% endif %}
                    </tr>
                </thead>
                <tbody>
                {% for kanal_adi, dosya_adi in kanal_links %}
                    <tr>
                        <td style="text-align: center; color: #666;">{{ loop.index }}</td>
                        <td>
                            <a href="{{ dosya_adi }}" target="_blank">{{ kanal_adi }}</a>
                        </td>
                        
                        {% if view_mode == 0 %}
                            <td><div class="status-cell" id="status-source-{{ loop.index }}"><span class="dot checking"></span><span class="text">...</span></div></td>
                            <td><div class="status-cell" id="status-github-{{ loop.index }}"><span class="dot checking"></span><span class="text">...</span></div></td>
                            <td><div class="status-cell" id="status-stream-{{ loop.index }}"><span class="dot checking"></span><span class="text">...</span></div></td>
                        {% else %}
                            <td style="text-align: center;">
                                <div id="status-action-{{ loop.index }}">
                                    <div class="action-badge theme-check">
                                        <span class="action-title">ANALİZ</span>
                                        <span class="action-reason">Kontrol Ediliyor...</span>
                                    </div>
                                </div>
                            </td>
                        {% endif %}
                    </tr>
                {% endfor %}
                </tbody>
            </table>

            <div class="btn-group">
                <a href="/editor" class="btn">Ayarlar & Görünüm</a>
                
                <button id="manualUpdateBtn" onclick="runUpdate(false)" class="btn" style="display:none; background:#e67e22; border-color:#d35400; cursor:pointer;">
                    Manuel Güncelle (Zorla)
                </button>

                <a href="/kapat" class="btn btn-red" onclick="return confirm('Sunucu kapatılsın mı?');">Sunucuyu Kapat</a>
            </div>
            
            <div id="auto-status" style="text-align:center; margin-top:15px; font-weight:bold; color:#f1c40f; display:none;"></div>
        </div>

        <script>
            function handleDynamicSearch() {
                const val = document.getElementById('dynamicSearch').value.trim();
                if(!val) return;
                // Boşlukları + yap veya olduğu gibi bırak (URL encode edilir)
                window.open('/' + encodeURIComponent(val), '_blank');
            }

            const channels = {{ kanal_links | tojson }};
            const VIEW_MODE = {{ view_mode }};
            let autoHealTriggered = false; // Tekrarı önlemek için session flag

            function updateDetailedUI(index, type, status, msg) {
                const el = document.getElementById(`status-${type}-${index}`);
                if(!el) return;
                const dot = el.querySelector('.dot');
                const txt = el.querySelector('.text');
                if(status === 'operational') {
                    dot.className = 'dot operational';
                    txt.textContent = 'OK';
                    txt.style.color = '#4cd964';
                } else {
                    dot.className = 'dot outage';
                    txt.textContent = msg || 'Hata';
                    txt.style.color = '#e74c3c';
                }
            }

            // Eylem Modu UI Güncelleme (Action + Reason) + OTO İYİLEŞTİRME TETİĞİ
            function updateActionUI(index, data) {
                const el = document.getElementById(`status-action-${index}`);
                if(!el) return;
                
                el.innerHTML = `
                    <div class="action-badge ${data.theme}">
                        <span class="action-title">${data.action}</span>
                        <span class="action-reason">${data.reason}</span>
                    </div>
                `;

                // --- OTO İYİLEŞTİRME MANTIĞI ---
                // Eğer Eylem "YENİLE" veya "YÜKLE" içeriyorsa ve henüz bu oturumda tetiklemediysek
                if (VIEW_MODE === 1 && (data.action.includes('YENİLE') || data.action.includes('YÜKLE')) && !autoHealTriggered ) {
                    attemptAutoHeal();
                }
            }

            function attemptAutoHeal() {
                autoHealTriggered = true; // Flag'i kaldır, bir daha deneme
                
                const lastRun = localStorage.getItem('lastAutoHealTime');
                const now = Date.now();
                const COOLDOWN = 300000; // 5 Dakika (Milisaniye cinsinden)

                // Eğer son 5 dakikada zaten çalıştırdıysak tekrar yapma, Butonu göster
                if (lastRun && (now - lastRun < COOLDOWN)) {
                    document.getElementById('manualUpdateBtn').style.display = 'inline-block';
                    const sDiv = document.getElementById('auto-status');
                    sDiv.style.display = 'block';
                    // Emoji yok, Türkçe var:
                    sDiv.innerText = "Otomatik onarım yakın zamanda denendi. Sorun devam ediyorsa butona basın.";
                    return;
                }

                // Süre geçmiş veya ilk kez deneniyor: OTO BAŞLAT
                runUpdate(true);
            }

            async function runUpdate(isAuto) {
                if (!isAuto) {
                    if(!confirm("Güncelleme betiği manuel çalıştırılsın mı?\\n\\nBu işlem sunucuyu kapatacaktır.")) return;
                } else {
                    // Otomatik modda kullanıcıya bilgi ver
                    const statusDiv = document.getElementById('auto-status');
                    statusDiv.style.display = 'block';
                    // Emoji yok, Türkçe var:
                    statusDiv.innerHTML = "Sorun tespit edildi. Otomatik onarım başlatılıyor... <br> (Sunucu birazdan kapanacak)";
                }

                // Zaman damgasını kaydet
                localStorage.setItem('lastAutoHealTime', Date.now());

                try {
                    await fetch('/api/trigger_update');
                    if (!isAuto) alert("İşlem başlatıldı. Sunucu kapanacak.");
                } catch(e) {
                    console.error("API Hatası:", e);
                    // Hata olursa butonu yine de göster
                    document.getElementById('manualUpdateBtn').style.display = 'inline-block';
                }
            }

            async function checkChannel(name, index) {
                let sSrc = { status: 'checking' };
                let sGit = { status: 'checking' };
                let sStrm = { status: 'checking' };
                
                // 1. Kaynak Kontrolü
                try {
                    let r = await fetch('/api/check_status', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: name, type: 'source' }) });
                    sSrc = await r.json();
                    if(VIEW_MODE === 0) updateDetailedUI(index, 'source', sSrc.status, 'Yok');
                } catch(e) { sSrc.status = 'outage'; }

                // 2. GitHub Kontrolü
                try {
                    let r = await fetch('/api/check_status', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: name, type: 'github' }) });
                    sGit = await r.json();
                    if(VIEW_MODE === 0) updateDetailedUI(index, 'github', sGit.status, 'Yok');
                } catch(e) { sGit.status = 'outage'; }

                // 3. Yayın Kontrolü
                try {
                    let r = await fetch('/api/check_status', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ name: name, type: 'stream' }) });
                    sStrm = await r.json();
                    if(VIEW_MODE === 0) updateDetailedUI(index, 'stream', sStrm.status, sStrm.error);
                } catch(e) { sStrm.status = 'outage'; sStrm.error = 'Hata'; }

                // --- EYLEM KARAR MOTORU ---
                if (VIEW_MODE === 1) {
                    let result = { action: '?', reason: '?', theme: 'theme-gray' };
                    const isSrcOK = sSrc.status === 'operational';
                    const isGitOK = sGit.status === 'operational';
                    const isStrmOK = sStrm.status === 'operational';
                    const is403 = sStrm.error && sStrm.error.includes('403');
                    const is404 = sStrm.error && sStrm.error.includes('404');
                    
                    if (isSrcOK && isGitOK && isStrmOK) {
                        result = { action: 'OYNAT', reason: 'Yayın Aktif', theme: 'theme-success' };
                    }
                    else if (isSrcOK && isGitOK && !isStrmOK) {
                        if (is403) {
                            result = { action: 'YENİLE', reason: 'Token Bitti', theme: 'theme-purple' };
                        } else if (is404) {
                            result = { action: 'ID BUL', reason: 'Video Silindi', theme: 'theme-red' };
                        } else {
                            result = { action: 'YENİLE', reason: 'Yayın Hatası', theme: 'theme-purple' };
                        }
                    }
                    else if (isSrcOK && !isGitOK) {
                        result = { action: 'YÜKLE', reason: 'Dosya Yok', theme: 'theme-orange' };
                    }
                    else if (!isSrcOK && isGitOK && !isStrmOK) {
                        result = { action: 'BEKLE', reason: 'Kanal Kapalı', theme: 'theme-red' };
                    }
                    else if (!isSrcOK && isGitOK && isStrmOK) {
                        result = { action: 'İZLE', reason: 'Kaynak Koptu', theme: 'theme-success' };
                    }
                    else {
                         result = { action: 'DÜZELT', reason: 'Kaynak Yok', theme: 'theme-gray' };
                    }

                    updateActionUI(index, result);
                }
            }

            channels.forEach((ch, i) => {
                setTimeout(() => checkChannel(ch[0], i + 1), i * 300);
            });
        </script>
    </body>
    </html>
    '''
    return render_template_string(html_template, kanal_links=kanal_links, view_mode=view_mode)

@app.route('/editor')
def editor():
    return send_from_directory('.', 'editor.html')

@app.route('/api/channels', methods=['GET', 'POST'])
def api_channels():
    if request.method == 'GET':
        flask_load_config()
        return jsonify({
            "channels": app.config.get("CHANNELS", []),
            "ONLY_HIGHEST": app.config.get("ONLY_HIGHEST", 1),
            "VIEW_MODE": app.config.get("VIEW_MODE", 0)
        })

    if request.method == 'POST':
        data = request.get_json()
        if data and 'channels' in data and isinstance(data['channels'], list):
            new_channels = []
            for item in data.get('channels', []):
                if isinstance(item, dict) and 'name' in item and 'url' in item:
                    new_channels.append({
                        "name": item.get("name", "").strip(),
                        "url": item.get("url", "").strip(),
                        "auto": item.get("auto", False)
                    })
            app.config['CHANNELS'] = new_channels
            app.config['ONLY_HIGHEST'] = data.get('ONLY_HIGHEST', 1)
            app.config['VIEW_MODE'] = data.get('VIEW_MODE', 0)
            flask_save_config()
            flask_load_config()
            return jsonify({"message": "Config başarıyla güncellendi."}), 200
        return jsonify({"error": "Geçersiz veri formatı."}), 400

@app.route('/api/youtube-search', methods=['POST'])
def api_youtube_search():
    data = request.get_json()
    query = data.get('query')
    if not query: return jsonify({"error": "Eksik"}), 400
    video_id = search_youtube_innertube(query)
    if video_id: return jsonify({"videoId": video_id}), 200
    return jsonify({"error": "Bulunamadı"}), 404

@app.route('/api/youtube-channel-search', methods=['POST'])
def api_youtube_channel_search():
    data = request.get_json()
    query = data.get('query')
    if not query: return jsonify({"error": "Eksik"}), 400
    channel_id = search_youtube_channel(query)
    if channel_id: return jsonify({"channelId": channel_id}), 200
    return jsonify({"error": "Bulunamadı"}), 404

@app.route('/api/check_status', methods=['POST'])
def api_check_status():
    data = request.get_json()
    channel_name = data.get('name')
    check_type = data.get('type', 'github')
    
    if not channel_name: return jsonify({"status": "outage", "error": "No name"}), 400

    github_url = get_github_url(channel_name)

    if check_type == 'github':
        status, error = check_github_status(github_url)
        if status == "operational":
            return jsonify({"status": "operational"}), 200
        return jsonify({"status": "outage", "error": error}), 200

    elif check_type == 'stream':
        status, error = check_stream_status(github_url)
        if status == "operational":
            return jsonify({"status": "operational"}), 200
        return jsonify({"status": "outage", "error": error}), 200

    elif check_type == 'source':
        flask_load_config()
        ch = next((c for c in app.config.get('CHANNELS', []) if c.get('name') == channel_name), None)
        if not ch: return jsonify({"status": "outage", "error": "Config Yok"}), 200
        
        status, error = check_source_status(ch)
        if status == "operational":
            return jsonify({"status": "operational"}), 200
        return jsonify({"status": "outage", "error": error}), 200
            
    return jsonify({"status": "outage", "error": "Geçersiz"}), 400

@app.route('/<path:stream_path>')
def stream_m3u8(stream_path):
    # 1. Önemsiz/Sistem dosyalarını yoksay
    if stream_path in ['favicon.ico', 'robots.txt', 'sitemap.xml']:
        abort(404)

    # 2. Dinamik İstek (YouTube ID, Handle, Web Sitesi URL)
    # Artık .m3u8 kontrolü yok, gelen path doğrudan kaynak olarak kabul edilir.
    target_input = stream_path

    m3u8_url, _ = resolve_channel_url(target_input)
    
    if not m3u8_url:
        abort(404)

    try:
        r = requests.get(m3u8_url, headers=DEFAULT_HEADERS, timeout=15, verify=False)
        r.raise_for_status()
        
        processed_lines = []
        base_to_use = m3u8_url
        for line in r.text.splitlines():
            line = line.strip()
            if not line: continue
            
            # URL ise (absolute veya relative)
            if not line.startswith('#'):
                if not line.startswith('http'):
                    line = urljoin(base_to_use, line)
                
                # nimblesessionid temizle
                line = remove_nimblesessionid(line)

            processed_lines.append(line)

        streams = []
        for i, line in enumerate(processed_lines):
            if line.startswith('#EXT-X-STREAM-INF'):
                resolution_match = re.search(r'RESOLUTION=(\d+x\d+)', line)
                resolution_str = resolution_match.group(1) if resolution_match else "0x0"
                if i + 1 < len(processed_lines) and not processed_lines[i+1].startswith('#'):
                    streams.append((line, processed_lines[i+1], resolution_str))

        if not streams:
            return Response('\n'.join(processed_lines), content_type='application/vnd.apple.mpegurl')
        
        only_highest = app.config.get("ONLY_HIGHEST", 1)

        if only_highest == 1 and streams:
            def parse_res(res_str):
                parts = res_str.split('x')
                return int(parts[0]) * int(parts[1]) if len(parts) == 2 else 0
            streams.sort(key=lambda x: parse_res(x[2]), reverse=True)
            highest_info, highest_url, _ = streams[0]
            return Response(f'{highest_info}\n{highest_url}', content_type='application/vnd.apple.mpegurl')
        else:
            return Response('\n'.join(processed_lines), content_type='application/vnd.apple.mpegurl')

    except requests.RequestException as e:
        log(f"Stream hatası ({stream_path}): {e}")
        abort(502)

# --- YENİ EKLENEN API: OTOMATİK GÜNCELLEME TETİKLEYİCİSİ ---
@app.route('/api/trigger_update')
def trigger_update():
    log("Otomatik güncelleme tetiklendi. github.pyw çalıştırılıyor...")
    try:
        subprocess.Popen(["pythonw", "github.pyw"], creationflags=SUBPROCESS_FLAGS)
    except Exception as e:
        log(f"github.pyw başlatma hatası: {e}")
    return jsonify({"status": "triggered"}), 200

def delayed_shutdown():
    time.sleep(1)
    os.kill(os.getpid(), signal.SIGTERM)

@app.route('/kapat')
def shutdown():
    threading.Thread(target=delayed_shutdown).start()
    return "Sunucu kapatılıyor..."

@app.errorhandler(404)
def page_not_found(e):
    return "404 - Sayfa bulunamadı", 404

if __name__ == "__main__":
    flask_load_config()
    app.run(host="0.0.0.0", port=5000)
