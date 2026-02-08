import asyncio
import json
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth # Hata veren stealth_async yerine standart stealth

async def main():
    async with async_playwright() as p:
        # Tarayıcıyı başlat
        browser = await p.chromium.launch(headless=True)
        
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )
        
        page = await context.new_page()
        
        # Stealth korumasını uygula
        await stealth(page)

        print("🚀 Dizipal'a bağlanılıyor...")
        
        try:
            # Sayfaya git
            await page.goto("https://dizipal.uk/filmler/", wait_until="domcontentloaded", timeout=90000)
            
            # Cloudflare geçişi için bekleme
            print("⏳ Doğrulama bekleniyor (20 saniye)...")
            await asyncio.sleep(20)

            content = await page.content()
            
            # Film yakalama deseni
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
                print(f"✅ BAŞARILI: {len(movies)} film kaydedildi.")
            else:
                print("❌ HATA: Film listesi boş. Cloudflare geçilememiş olabilir.")
                with open("debug_source.txt", "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            print(f"🔥 HATA: {str(e)}")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
