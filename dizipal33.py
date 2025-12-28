# Bu araç @keyiflerolsun tarafından | @KekikAkademi için yazılmıştır.
# DiziPal33 - Full Fix | Mehmet EYİGÜN

from KekikStream.Core import (
    PluginBase, MainPageResult, SearchResult,
    MovieInfo, SeriesInfo, Episode, Subtitle, ExtractResult
)
from selectolax.parser import HTMLParser
import re

class DiziPal33(PluginBase):
    name        = "DiziPal33"
    language    = "tr"
    main_url    = "https://dizipal1224.com"
    favicon     = f"https://www.google.com/s2/favicons?domain={main_url}&sz=64"
    description = "DiziPal tüm dizi ve filmler (full fix)"

    main_page = {
        f"{main_url}/diziler/son-bolumler": "Son Bölümler",
        f"{main_url}/diziler": "Yeni Diziler",
        f"{main_url}/filmler": "Filmler",
        f"{main_url}/koleksiyon/netflix": "Netflix",
        f"{main_url}/koleksiyon/exxen": "Exxen",
        f"{main_url}/koleksiyon/blutv": "BluTV",
        f"{main_url}/koleksiyon/disney": "Disney+",
        f"{main_url}/koleksiyon/amazon-prime": "Amazon Prime",
        f"{main_url}/koleksiyon/tod-bein": "TOD (beIN)",
        f"{main_url}/koleksiyon/gain": "Gain",
        f"{main_url}/tur/mubi": "Mubi",
    }

    # ======================================================
    # MAIN PAGE
    # ======================================================
    async def get_main_page(self, page: int, url: str, category: str):
        # 🔥 DiziPal film/koleksiyon sayfaları page=1 olmadan boş dönebiliyor
        if "filmler" in url or "koleksiyon" in url or "diziler" in url:
            url = f"{url}?page={page}"
        elif page > 1:
            url = f"{url}?page={page}"

        r = await self.httpx.get(url)
        dom = HTMLParser(r.text)
        results = []

        # =========================
        # SON BÖLÜMLER
        # =========================
        if "son-bolumler" in url:
            for item in dom.css("div.episode-item"):
                name = item.css_first("div.name")
                ep   = item.css_first("div.episode")
                a    = item.css_first("a")
                img  = item.css_first("img")

                if not name or not a:
                    continue

                ep_txt = ep.text(strip=True) if ep else ""
                ep_txt = ep_txt.replace(". Sezon ", "x").replace(". Bölüm", "")
                dizi_url = re.sub(r'/sezon.*', '', a.attrs.get("href"))

                results.append(MainPageResult(
                    category=category,
                    title=f"{name.text(strip=True)} {ep_txt}",
                    url=self.fix_url(dizi_url),
                    poster=self.fix_url(
                        img.attrs.get("src") or img.attrs.get("data-src")
                    ) if img else None
                ))
            return results

        # =========================
        # DİZİ + FİLM + KOLEKSİYON
        # =========================
        for li in dom.css("article ul li"):
            a = li.css_first("a[href]")
            t = li.css_first("span.title") or li.css_first("div.name")
            i = li.css_first("img")

            if not a or not t:
                continue

            poster = None
            if i:
                poster = i.attrs.get("src") or i.attrs.get("data-src")

            results.append(MainPageResult(
                category=category,
                title=t.text(strip=True),
                url=self.fix_url(a.attrs["href"]),
                poster=self.fix_url(poster) if poster else None
            ))

        return results

    # ======================================================
    # SEARCH
    # ======================================================
    async def search(self, query: str):
        self.httpx.headers.update({
            "Accept": "application/json",
            "X-Requested-With": "XMLHttpRequest"
        })

        r = await self.httpx.post(
            f"{self.main_url}/api/search-autocomplete",
            data={"query": query}
        )

        try:
            data = r.json()
        except:
            return []

        items = data.values() if isinstance(data, dict) else data
        results = []

        for i in items:
            if not isinstance(i, dict):
                continue

            if i.get("title") and i.get("url"):
                results.append(SearchResult(
                    title=i["title"],
                    url=self.main_url + i["url"],
                    poster=self.fix_url(i.get("poster"))
                ))
        return results

    # ======================================================
    # LOAD ITEM
    # ======================================================
    async def load_item(self, url: str):
        self.httpx.headers.clear()
        self.httpx.headers.update({"User-Agent": "Mozilla/5.0"})

        r = await self.httpx.get(url)
        dom = HTMLParser(r.text)
        html = r.text

        poster = None
        og = dom.css_first("meta[property='og:image']")
        if og:
            poster = self.fix_url(og.attrs.get("content"))

        year     = self._re(html, r'Yapım Yılı.*?<div[^>]*>(\d{4})')
        rating   = self._re(html, r'IMDB Puanı.*?<div[^>]*>([\d.]+)')
        duration = self._re(html, r'Ortalama Süre.*?<div[^>]*>(\d+)', int)

        desc = dom.css_first("div.summary p")
        desc = desc.text(strip=True) if desc else None

        tags_raw = self._re(html, r'Türler.*?<div[^>]*>([^<]+)')
        tags = [t.strip() for t in re.split(r',|\|', tags_raw)] if tags_raw else None

        # =========================
        # SERIES
        # =========================
        if "/dizi/" in url:
            title = dom.css_first("div.cover h5")
            title = title.text(strip=True) if title else None

            episodes = []
            for ep in dom.css("div.episode-item"):
                a = ep.css_first("a")
                n = ep.css_first("div.name")
                e = ep.css_first("div.episode")

                if not a or not n:
                    continue

                season = episode = None
                if e:
                    m = re.search(r'(\d+)\.\s*Sezon.*?(\d+)\.\s*Bölüm', e.text())
                    if m:
                        season = int(m.group(1))
                        episode = int(m.group(2))

                episodes.append(Episode(
                    season=season,
                    episode=episode,
                    title=n.text(strip=True),
                    url=self.fix_url(a.attrs["href"])
                ))

            return SeriesInfo(
                url=url,
                poster=poster,
                title=title,
                description=desc,
                tags=tags,
                rating=rating,
                year=year,
                duration=duration,
                episodes=episodes
            )

        # =========================
        # MOVIE
        # =========================
        g = dom.css("div.g-title div")
        title = g[1].text(strip=True) if len(g) >= 2 else None

        return MovieInfo(
            url=url,
            poster=poster,
            title=title,
            description=desc,
            tags=tags,
            rating=rating,
            year=year,
            duration=duration
        )

    # ======================================================
    # LOAD LINKS
    # ======================================================
    async def load_links(self, url: str):
        self.httpx.headers.clear()
        self.httpx.headers.update({"User-Agent": "Mozilla/5.0"})

        r = await self.httpx.get(url)
        dom = HTMLParser(r.text)

        iframe = dom.css_first("iframe")
        if not iframe:
            return []

        iframe_url = self.fix_url(iframe.attrs.get("src"))
        self.httpx.headers.update({"Referer": self.main_url})

        ir = await self.httpx.get(iframe_url)
        text = ir.text

        m3u = re.search(r'(https?://[^"\']+\.m3u8)', text)
        if not m3u:
            return []

        subs = []
        for s in re.findall(r'"subtitle":"([^"]+)"', text):
            lang = "Türkçe"
            if "[" in s:
                lang = s.split("[")[1].split("]")[0]
                s = s.replace(f"[{lang}]", "")
            subs.append(Subtitle(name=lang, url=self.fix_url(s)))

        return [ExtractResult(
            name=self.name,
            url=m3u.group(1),
            referer=self.main_url,
            subtitles=subs
        )]

    # ======================================================
    # REGEX HELPER
    # ======================================================
    def _re(self, text, pattern, cast=str):
        m = re.search(pattern, text, re.S | re.I)
        return cast(m.group(1)) if m else None
