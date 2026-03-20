"""
Trend Affiliate Scraper
========================
Sammelt täglich Trends von Google Trends, Reddit & Amazon (simuliert)
und generiert eine fertige HTML-Seite mit Affiliate-Links.

Setup:
  pip install pytrends requests jinja2

Amazon Affiliate:
  1. Anmelden: https://affiliate-program.amazon.de
  2. AMAZON_AFFILIATE_TAG unten ersetzen (z.B. "meinblog-21")
"""

import json
import time
import random
import requests
from datetime import datetime
from pathlib import Path
from pytrends.request import TrendReq

# ─── KONFIGURATION ────────────────────────────────────────────────────────────

AMAZON_AFFILIATE_TAG = "DEIN-TAG-21"   # ← hier deinen Tag eintragen
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

CATEGORIES = {
    "Frauen Mode & Beauty": {
        "icon": "👗",
        "reddit": "femalefashionadvice",
        "google_keywords": ["Damen Mode Trend", "Beauty Trend", "Frauen Fashion"],
        "amazon_search": "Damen Mode Trend",
        "amazon_node": "1981002031",   # Amazon DE: Damen Bekleidung
        "color": "#e91e8c",
    },
    "Männer Mode": {
        "icon": "👔",
        "reddit": "malefashionadvice",
        "google_keywords": ["Herren Mode Trend", "Männer Fashion", "Herren Style"],
        "amazon_search": "Herren Mode Trend",
        "amazon_node": "77028031",     # Amazon DE: Herren Bekleidung
        "color": "#1565c0",
    },
    "Tech & Gadgets": {
        "icon": "⚡",
        "reddit": "gadgets",
        "google_keywords": ["Tech Gadget Trend", "Neues Gadget", "Smart Home"],
        "amazon_search": "Gadgets 2025",
        "amazon_node": "573084",       # Amazon DE: Elektronik
        "color": "#6a1b9a",
    },
    "Home & Living": {
        "icon": "🏠",
        "reddit": "malelivingspace",
        "google_keywords": ["Home Deko Trend", "Wohnung einrichten", "Wohntrend"],
        "amazon_search": "Wohndeko Trend",
        "amazon_node": "3167641",      # Amazon DE: Küche & Haushalt
        "color": "#2e7d32",
    },
}

# ─── GOOGLE TRENDS ────────────────────────────────────────────────────────────

def fetch_google_trends(keywords: list[str], geo: str = "DE") -> list[dict]:
    """Holt die aktuellen Google Trends für die gegebenen Keywords."""
    try:
        pytrends = TrendReq(hl="de-DE", tz=60, timeout=(10, 25))
        pytrends.build_payload(keywords[:5], timeframe="now 7-d", geo=geo)
        related = pytrends.related_queries()

        trends = []
        for kw in keywords[:5]:
            if kw in related and related[kw]["top"] is not None:
                top = related[kw]["top"].head(5)
                for _, row in top.iterrows():
                    trends.append({
                        "term": row["query"],
                        "value": int(row["value"]),
                        "source": "Google Trends",
                        "url": f"https://trends.google.com/trends/explore?q={requests.utils.quote(row['query'])}&geo=DE",
                    })
        return sorted(trends, key=lambda x: x["value"], reverse=True)[:8]
    except Exception as e:
        print(f"  Google Trends Fehler: {e}")
        return []

# ─── REDDIT ───────────────────────────────────────────────────────────────────

def fetch_reddit_trends(subreddit: str, limit: int = 8) -> list[dict]:
    """Holt Hot-Posts von Reddit (keine API nötig, öffentliches JSON)."""
    url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
    headers = {"User-Agent": "TrendBot/1.0"}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        r.raise_for_status()
        posts = r.json()["data"]["children"]
        return [
            {
                "term": p["data"]["title"][:80],
                "value": p["data"]["score"],
                "source": f"r/{subreddit}",
                "url": f"https://reddit.com{p['data']['permalink']}",
                "thumbnail": p["data"].get("thumbnail") if p["data"].get("thumbnail", "").startswith("http") else None,
            }
            for p in posts
            if not p["data"].get("stickied")
        ]
    except Exception as e:
        print(f"  Reddit Fehler ({subreddit}): {e}")
        return []

# ─── AMAZON AFFILIATE LINKS ───────────────────────────────────────────────────

def build_amazon_link(search_term: str, node: str = "") -> str:
    """Baut einen Amazon-Suchlink mit Affiliate-Tag."""
    base = "https://www.amazon.de/s"
    params = f"?k={requests.utils.quote(search_term)}&tag={AMAZON_AFFILIATE_TAG}"
    if node:
        params += f"&rh=n:{node}"
    return base + params

def build_amazon_bestseller_link(node: str) -> str:
    """Link zur Amazon-Bestseller-Seite einer Kategorie."""
    return f"https://www.amazon.de/gp/bestsellers/fashion/{node}?tag={AMAZON_AFFILIATE_TAG}"

# ─── HAUPT-SCRAPER ────────────────────────────────────────────────────────────

def scrape_all() -> dict:
    """Scrapt alle Kategorien und gibt die gesammelten Daten zurück."""
    results = {}
    print(f"\n🚀 Starte Scraping — {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")

    for cat_name, cfg in CATEGORIES.items():
        print(f"📦 Kategorie: {cat_name}")
        cat_data = {"config": cfg, "google": [], "reddit": [], "amazon_links": {}}

        # Google Trends
        print("  → Google Trends...")
        cat_data["google"] = fetch_google_trends(cfg["google_keywords"])
        time.sleep(2)  # Rate limit respektieren

        # Reddit
        print(f"  → Reddit r/{cfg['reddit']}...")
        cat_data["reddit"] = fetch_reddit_trends(cfg["reddit"])
        time.sleep(1)

        # Amazon Links (keine API nötig — Suchlinks mit Affiliate-Tag)
        cat_data["amazon_links"] = {
            "search": build_amazon_link(cfg["amazon_search"], cfg["amazon_node"]),
            "bestseller": build_amazon_bestseller_link(cfg["amazon_node"]),
        }

        results[cat_name] = cat_data
        print(f"  ✓ {len(cat_data['google'])} Google-Trends, {len(cat_data['reddit'])} Reddit-Posts\n")

    return results

# ─── HTML GENERATOR ───────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Trend Report – {date}</title>
<style>
  :root {{
    --bg: #f8f9fa; --card: #fff; --text: #1a1a2e;
    --muted: #6c757d; --border: #e9ecef; --radius: 12px;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: var(--bg); color: var(--text); }}
  header {{
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    color: #fff; padding: 2.5rem 1.5rem; text-align: center;
  }}
  header h1 {{ font-size: 2rem; font-weight: 700; margin-bottom: .4rem; }}
  header p {{ opacity: .7; font-size: .95rem; }}
  .badge {{
    display: inline-block; padding: 3px 10px; border-radius: 20px;
    font-size: .75rem; font-weight: 600; color: #fff; margin-left: .5rem;
  }}
  main {{ max-width: 1200px; margin: 2rem auto; padding: 0 1rem; }}
  .category {{ margin-bottom: 3rem; }}
  .cat-header {{
    display: flex; align-items: center; gap: .75rem;
    border-left: 4px solid var(--accent); padding-left: 1rem; margin-bottom: 1.5rem;
  }}
  .cat-header h2 {{ font-size: 1.4rem; }}
  .cat-icon {{ font-size: 1.8rem; }}
  .amazon-bar {{
    background: #fff8e1; border: 1px solid #ffe082; border-radius: var(--radius);
    padding: 1rem 1.25rem; margin-bottom: 1.5rem;
    display: flex; gap: 1rem; flex-wrap: wrap; align-items: center;
  }}
  .amazon-bar span {{ font-weight: 600; color: #e65100; }}
  .amazon-bar a {{
    display: inline-block; padding: .45rem 1rem; border-radius: 8px;
    background: #ff9900; color: #fff; text-decoration: none; font-size: .85rem; font-weight: 600;
  }}
  .amazon-bar a:hover {{ background: #e68900; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; }}
  @media (max-width: 700px) {{ .grid {{ grid-template-columns: 1fr; }} }}
  .section-card {{ background: var(--card); border-radius: var(--radius); border: 1px solid var(--border); overflow: hidden; }}
  .section-card h3 {{ padding: .85rem 1rem; font-size: .85rem; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); border-bottom: 1px solid var(--border); }}
  .trend-list {{ list-style: none; }}
  .trend-list li {{ display: flex; align-items: flex-start; gap: .75rem; padding: .75rem 1rem; border-bottom: 1px solid var(--border); }}
  .trend-list li:last-child {{ border-bottom: none; }}
  .trend-rank {{ font-size: .75rem; font-weight: 700; color: #fff; background: var(--accent); border-radius: 4px; min-width: 22px; height: 22px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
  .trend-body {{ flex: 1; }}
  .trend-term {{ font-weight: 500; font-size: .92rem; }}
  .trend-term a {{ color: var(--text); text-decoration: none; }}
  .trend-term a:hover {{ color: var(--accent); }}
  .trend-meta {{ font-size: .78rem; color: var(--muted); margin-top: 2px; }}
  .bar {{ height: 4px; border-radius: 2px; margin-top: 5px; background: var(--accent); opacity: .3; }}
  footer {{ text-align: center; padding: 2rem 1rem; color: var(--muted); font-size: .8rem; border-top: 1px solid var(--border); margin-top: 2rem; }}
  footer a {{ color: var(--muted); }}
  .disclaimer {{ background: #f1f3f5; border-radius: 8px; padding: .75rem 1rem; margin: 2rem 0; font-size: .8rem; color: var(--muted); }}
</style>
</head>
<body>
<header>
  <h1>📈 Daily Trend Report</h1>
  <p>Automatisch aktualisiert am {date} · Trends aus Google, Reddit & Amazon</p>
</header>
<main>
<p class="disclaimer">
  * Diese Seite enthält Affiliate-Links. Wenn du über einen Link einkaufst, erhalte ich eine kleine Provision – für dich entstehen keine Mehrkosten.
</p>
{categories_html}
</main>
<footer>
  <p>Automatisch generiert · <a href="#">Datenschutz</a> · <a href="#">Impressum</a></p>
  <p style="margin-top:.5rem">* Amazon Affiliate | Stand: {date}</p>
</footer>
</body>
</html>"""

def render_html(data: dict) -> str:
    cats_html = ""
    for cat_name, cat in data.items():
        cfg = cat["config"]
        color = cfg["color"]
        icon = cfg["icon"]
        google_items = cat["google"]
        reddit_items = cat["reddit"]
        amz = cat["amazon_links"]

        # Google Trends Liste
        g_html = ""
        max_val = max((x["value"] for x in google_items), default=1)
        for i, t in enumerate(google_items[:6], 1):
            bar_width = int(t["value"] / max_val * 100)
            g_html += f"""
            <li>
              <span class="trend-rank" style="background:{color}">{i}</span>
              <div class="trend-body">
                <div class="trend-term"><a href="{t['url']}" target="_blank" rel="nofollow">{t['term']}</a></div>
                <div class="trend-meta">Interesse: {t['value']}% · {t['source']}</div>
                <div class="bar" style="width:{bar_width}%;opacity:.5;background:{color}"></div>
              </div>
            </li>"""

        # Reddit Liste
        r_html = ""
        for i, t in enumerate(reddit_items[:6], 1):
            r_html += f"""
            <li>
              <span class="trend-rank" style="background:{color}">{i}</span>
              <div class="trend-body">
                <div class="trend-term"><a href="{t['url']}" target="_blank" rel="nofollow">{t['term'][:70]}</a></div>
                <div class="trend-meta">👍 {t['value']:,} · {t['source']}</div>
              </div>
            </li>"""

        cats_html += f"""
<section class="category" style="--accent:{color}">
  <div class="cat-header">
    <span class="cat-icon">{icon}</span>
    <h2>{cat_name}</h2>
  </div>
  <div class="amazon-bar">
    <span>🛒 Amazon</span>
    <a href="{amz['search']}" target="_blank" rel="nofollow sponsored">Trendprodukte suchen →</a>
    <a href="{amz['bestseller']}" target="_blank" rel="nofollow sponsored">Bestseller ansehen →</a>
  </div>
  <div class="grid">
    <div class="section-card">
      <h3>🔍 Google Trends</h3>
      <ul class="trend-list">{g_html if g_html else '<li style="padding:1rem;color:#999">Keine Daten verfügbar</li>'}</ul>
    </div>
    <div class="section-card">
      <h3>💬 Reddit Hot Posts</h3>
      <ul class="trend-list">{r_html if r_html else '<li style="padding:1rem;color:#999">Keine Daten verfügbar</li>'}</ul>
    </div>
  </div>
</section>"""

    date_str = datetime.now().strftime("%d.%m.%Y")
    return HTML_TEMPLATE.format(date=date_str, categories_html=cats_html)

# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    data = scrape_all()

    # JSON speichern (für Debugging / Weiterverarbeitung)
    json_path = OUTPUT_DIR / f"trends_{datetime.now().strftime('%Y%m%d')}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        # Config-Objekte sind nicht JSON-serialisierbar — vereinfachen
        simplified = {
            k: {"google": v["google"], "reddit": v["reddit"], "amazon_links": v["amazon_links"]}
            for k, v in data.items()
        }
        json.dump(simplified, f, ensure_ascii=False, indent=2)
    print(f"📄 JSON gespeichert: {json_path}")

    # HTML generieren
    html = render_html(data)
    html_path = OUTPUT_DIR / "index.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"🌐 HTML generiert: {html_path}")
    print(f"\n✅ Fertig! Öffne {html_path} im Browser.\n")

if __name__ == "__main__":
    main()
