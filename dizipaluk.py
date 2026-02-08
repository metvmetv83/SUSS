import asyncio
import json
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        # Tarayıcıyı başlat (Gizli Mod)
        browser = await p.chromium.launch(headless=True)
        
        # Gerçek bir tarayıcı profili simüle et
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080},
            device_scale_factor=1,
        )
        
        page = await context.new_page()
        
        # Stealth eklentisini uygula (Bot korumalarını aşmak için)
        await stealth_async(page)

        print("🚀 Dizipal'a bağlanılıyor...")
        
        try:
            # Sayfaya git (Timeout süresini 90 saniyeye çıkardık)
            await page.goto("https://dizipal.uk/filmler/", wait_until="domcontentloaded", timeout=90000)
            
            # Cloudflare'in "İnsan mısın?" kontrolünü geçmesi için bekleme süresi
            print("⏳ Cloudflare doğrulaması bekleniyor (20 saniye)...")
            await asyncio.sleep(20)

            # Sayfa kaynağını al
            content = await page.content()
            
            # Film linklerini ve başlıklarını yakala
            # Desen: href=".../film/..." ve title="..."
            pattern = r'href="(https://dizipal\.uk/film/[^"]+)"[^>]*title="([^"]+)"'
            matches = re.findall(pattern, content)

            movies = []
            seen = set()
            for url, title in matches:
                if url not in seen:
                    movies.append({
                        "title": title.strip(),
                        "url": url
                    })
                    seen.add(url)

            if movies:
                with open("filmler.json", "w", encoding="utf-8") as f:
                    json.dump(movies, f, ensure_ascii=False, indent=4)
                print(f"✅ İŞLEM TAMAM: {len(movies)} film filmler.json dosyasına yazıldı.")
            else:
                print("❌ HATA: Sayfaya girildi ama film listesi boş döndü.")
                # Hata analizi için sayfa yapısını debug.txt olarak kaydet
                with open("debug.txt", "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            print(f"🔥 KRİTİK HATA: {str(e)}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
