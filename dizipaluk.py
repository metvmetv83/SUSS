import asyncio
import json
import re
from playwright.async_api import async_playwright
from playwright_stealth import stealth_async

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage"
            ]
        )

        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            viewport={'width': 1920, 'height': 1080}
        )

        page = await context.new_page()

        # ✅ DOĞRU STEALTH
        await stealth_async(page)

        print("🚀 Dizipal'a bağlanılıyor...")

        try:
            await page.goto(
                "https://dizipal.uk/filmler/",
                wait_until="networkidle",
                timeout=90000
            )

            print("⏳ Cloudflare bekleniyor (20 sn)...")
            await asyncio.sleep(20)

            content = await page.content()

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
                print("❌ Film bulunamadı, Cloudflare geçilemedi.")
                with open("debug_source.txt", "w", encoding="utf-8") as f:
                    f.write(content)

        except Exception as e:
            print(f"🔥 HATA: {e}")

        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
