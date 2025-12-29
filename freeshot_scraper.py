import asyncio
import json
from playwright.async_api import async_playwright

CHANNELS_FILE = "channels.json"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://www.freeshot.live/",
    "Origin": "https://www.freeshot.live"
}

def load_channels():
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

async def scrape_channel(playwright, channel):
    browser = await playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox"]
    )

    context = await browser.new_context(
        user_agent=DEFAULT_HEADERS["User-Agent"]
    )
    page = await context.new_page()

    found_m3u8 = None

    async def handle_response(response):
        nonlocal found_m3u8
        url = response.url
        if ".m3u8" in url and "token=" in url:
            found_m3u8 = url

    page.on("response", handle_response)

    print(f"\n📡 Kanal: {channel['name']}")

    try:
        await page.goto(
            channel["page_url"],
            timeout=45000,
            wait_until="networkidle"
        )

        # JS player çalışsın diye bekle
        for _ in range(15):
            if found_m3u8:
                break
            await page.wait_for_timeout(1000)

        if not found_m3u8:
            print("      ❌ m3u8 yakalanamadı")
            return None

        print("      ✅ m3u8 bulundu")
        return found_m3u8

    except Exception as e:
        print(f"      ❌ Hata: {e}")
        return None

    finally:
        await browser.close()

async def main():
    print("\n=== FreeShot Scraper – NETWORK MODE ===\n")

    channels = load_channels()
    results = []

    async with async_playwright() as playwright:
        for ch in channels:
            if "page_url" not in ch:
                continue

            m3u8 = await scrape_channel(playwright, ch)
            if m3u8:
                results.append({
                    "id": ch["id"],
                    "name": ch["name"],
                    "url": m3u8,
                    "image": ch.get("image", ""),
                    "headers": DEFAULT_HEADERS
                })

    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n🏆 channels.json başarıyla güncellendi")

if __name__ == "__main__":
    asyncio.run(main())
