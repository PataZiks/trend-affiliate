"""
Pinterest Auto-Poster
=====================
Liest die täglichen Trends aus output/trends_*.json
und postet automatisch Pins auf Pinterest.

Setup:
  pip install requests pillow

Konfiguration:
  PINTEREST_TOKEN  → dein Access Token von developers.pinterest.com
  BOARD_ID         → wird automatisch aus deinem Username geholt
"""

import os
import json
import requests
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import textwrap
import glob

# ─── KONFIGURATION ────────────────────────────────────────────────────────────

# NICHT JEMANDEN GEBEN 
PINTEREST_TOKEN = os.environ.get("PINTEREST_TOKEN", "")
PINTEREST_USERNAME = "patrik00131152"
BOARD_NAME = "trends-2026"
AMAZON_AFFILIATE_TAG = "DEIN-TAG-21"  # ← deinen Amazon Tag eintragen

OUTPUT_DIR = Path("output")
PINS_DIR = Path("output/pins")
PINS_DIR.mkdir(parents=True, exist_ok=True)

# Farben pro Kategorie
CATEGORY_COLORS = {
    "Frauen Mode & Beauty": {"bg": "#FF6B9D", "text": "#FFFFFF", "accent": "#FF1493"},
    "Männer Mode":          {"bg": "#1565C0", "text": "#FFFFFF", "accent": "#0D47A1"},
    "Tech & Gadgets":       {"bg": "#6A1B9A", "text": "#FFFFFF", "accent": "#4A148C"},
    "Home & Living":        {"bg": "#2E7D32", "text": "#FFFFFF", "accent": "#1B5E20"},
}

CATEGORY_ICONS = {
    "Frauen Mode & Beauty": "FASHION",
    "Männer Mode":          "STYLE",
    "Tech & Gadgets":       "TECH",
    "Home & Living":        "HOME",
}

# ─── PIN-BILD ERSTELLEN ───────────────────────────────────────────────────────

def create_pin_image(category: str, trends: list[str], save_path: Path) -> Path:
    """Erstellt ein 1000x1500px Pinterest-Pin Bild."""
    colors = CATEGORY_COLORS.get(category, {"bg": "#333333", "text": "#FFFFFF", "accent": "#111111"})
    label = CATEGORY_ICONS.get(category, "TREND")

    W, H = 1000, 1500
    img = Image.new("RGB", (W, H), color=colors["bg"])
    draw = ImageDraw.Draw(img)

    # Hintergrund-Dekoration (einfache geometrische Formen)
    draw.ellipse([600, -100, 1100, 400], fill=colors["accent"])
    draw.ellipse([-100, 1200, 400, 1700], fill=colors["accent"])

    # Label oben
    draw.rectangle([60, 80, 260, 130], fill="#FFFFFF")
    try:
        font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
        font_trend = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 38)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 28)
    except:
        font_label = font_title = font_trend = font_small = ImageFont.load_default()

    draw.text((80, 88), label, font=font_label, fill=colors["bg"])

    # Titel
    draw.text((60, 180), "TOP TRENDS", font=font_title, fill="#FFFFFF")
    date_str = datetime.now().strftime("%d.%m.%Y")
    draw.text((60, 260), date_str, font=font_small, fill="#FFFFFF")

    # Trennlinie
    draw.rectangle([60, 310, 940, 316], fill="#FFFFFF")

    # Trend-Liste
    y = 360
    for i, trend in enumerate(trends[:6], 1):
        # Nummer-Badge
        draw.ellipse([60, y, 110, y+50], fill="#FFFFFF")
        draw.text((75, y+8), str(i), font=font_trend, fill=colors["bg"])

        # Trend-Text (wrappen falls zu lang)
        wrapped = textwrap.fill(trend[:50], width=28)
        draw.text((130, y+5), wrapped, font=font_trend, fill="#FFFFFF")
        y += 130

    # Footer
    draw.rectangle([0, 1380, W, H], fill=colors["accent"])
    draw.text((60, 1410), "Jetzt bei Amazon shoppen →", font=font_small, fill="#FFFFFF")
    draw.text((60, 1450), f"Affiliate-Link | {category}", font=font_small, fill="#FFFFFF")

    img.save(save_path, "PNG", quality=95)
    return save_path

# ─── PINTEREST API ────────────────────────────────────────────────────────────

def get_board_id(username: str, board_name: str) -> str | None:
    """Holt die Board-ID anhand von Username und Board-Name."""
    url = f"https://api.pinterest.com/v5/boards/{username}/{board_name}"
    headers = {"Authorization": f"Bearer {PINTEREST_TOKEN}"}
    r = requests.get(url, headers=headers, timeout=10)
    if r.status_code == 200:
        return r.json().get("id")
    print(f"  Board nicht gefunden: {r.status_code} {r.text}")
    return None

def upload_image_to_pinterest(image_path: Path) -> str | None:
    """Lädt ein Bild zu Pinterest hoch und gibt die Media-ID zurück."""
    url = "https://api.pinterest.com/v5/media"
    headers = {"Authorization": f"Bearer {PINTEREST_TOKEN}"}

    # Schritt 1: Upload-URL anfordern
    r = requests.post(url, headers=headers, json={"media_type": "image"}, timeout=10)
    if r.status_code != 201:
        print(f"  Media-Upload fehlgeschlagen: {r.text}")
        return None

    data = r.json()
    media_id = data["media_id"]
    upload_url = data["upload_url"]
    upload_params = data.get("upload_parameters", {})

    # Schritt 2: Bild hochladen
    with open(image_path, "rb") as f:
        files = {"file": f}
        r2 = requests.post(upload_url, data=upload_params, files=files, timeout=30)
        if r2.status_code not in [200, 204]:
            print(f"  Bild-Upload fehlgeschlagen: {r2.status_code}")
            return None

    return media_id

def create_pin(board_id: str, title: str, description: str, link: str, media_id: str) -> bool:
    """Erstellt einen Pin auf Pinterest."""
    url = "https://api.pinterest.com/v5/pins"
    headers = {
        "Authorization": f"Bearer {PINTEREST_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "board_id": board_id,
        "title": title[:100],
        "description": description[:500],
        "link": link,
        "media_source": {
            "source_type": "media_id",
            "media_id": media_id
        }
    }
    r = requests.post(url, headers=headers, json=payload, timeout=10)
    if r.status_code == 201:
        pin_id = r.json().get("id")
        print(f"  ✓ Pin erstellt: https://pinterest.com/pin/{pin_id}")
        return True
    else:
        print(f"  Pin-Erstellung fehlgeschlagen: {r.status_code} {r.text}")
        return False

# ─── HAUPT-FUNKTION ───────────────────────────────────────────────────────────

def main():
    print(f"\n📌 Pinterest Auto-Poster — {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")

    # Neueste JSON-Datei laden
    json_files = sorted(glob.glob(str(OUTPUT_DIR / "trends_*.json")))
    if not json_files:
        print("❌ Keine Trend-Daten gefunden. Zuerst scraper.py ausführen!")
        return

    latest = json_files[-1]
    print(f"📄 Lade Trends aus: {latest}")
    with open(latest, encoding="utf-8") as f:
        trends_data = json.load(f)

    # Board-ID holen
    print(f"🔍 Suche Board '{BOARD_NAME}'...")
    board_id = get_board_id(PINTEREST_USERNAME, BOARD_NAME)
    if not board_id:
        print("❌ Board nicht gefunden!")
        return
    print(f"✓ Board-ID: {board_id}")

    # Pro Kategorie einen Pin erstellen
    for cat_name, cat_data in trends_data.items():
        print(f"\n📦 Kategorie: {cat_name}")

        # Trends sammeln (Google + Reddit kombiniert)
        all_trends = []
        for t in cat_data.get("google", [])[:4]:
            all_trends.append(t["term"])
        for t in cat_data.get("reddit", [])[:3]:
            all_trends.append(t["term"][:40])

        if not all_trends:
            print("  Keine Trends verfügbar, überspringe...")
            continue

        # Pin-Bild erstellen
        safe_name = cat_name.replace(" ", "_").replace("&", "und")
        img_path = PINS_DIR / f"pin_{safe_name}_{datetime.now().strftime('%Y%m%d')}.png"
        print(f"  🎨 Erstelle Pin-Bild...")
        create_pin_image(cat_name, all_trends, img_path)

        # Amazon Affiliate Link
        amazon_link = cat_data.get("amazon_links", {}).get("search", "https://amazon.de")

        # Bild hochladen
        print(f"  📤 Lade Bild hoch...")
        media_id = upload_image_to_pinterest(img_path)
        if not media_id:
            continue

        # Pin erstellen
        top_trend = all_trends[0] if all_trends else cat_name
        title = f"Top Trends {cat_name} – {datetime.now().strftime('%B %Y')}"
        description = (
            f"🔥 Aktuelle Top-Trends in {cat_name}!\n\n"
            + "\n".join([f"#{i} {t}" for i, t in enumerate(all_trends[:5], 1)])
            + f"\n\n👉 Jetzt bei Amazon shoppen (Affiliate-Link)\n"
            + f"#trends #{cat_name.replace(' ', '').replace('&', '')} #shopping #mode"
        )

        print(f"  📌 Poste Pin: '{title}'")
        create_pin(board_id, title, description, amazon_link, media_id)

    print(f"\n✅ Fertig! Prüfe dein Board: https://pinterest.com/{PINTEREST_USERNAME}/{BOARD_NAME}/\n")

if __name__ == "__main__":
    main()
