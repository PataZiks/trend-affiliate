# 📈 Trend Affiliate Scraper

Sammelt täglich Trends aus Google, Reddit & Amazon und generiert eine HTML-Seite mit Affiliate-Links.

## 🚀 Schnellstart (lokal)

```bash
# 1. Abhängigkeiten installieren
pip install -r requirements.txt

# 2. Deinen Amazon Affiliate-Tag eintragen
# → scraper.py, Zeile: AMAZON_AFFILIATE_TAG = "DEIN-TAG-21"

# 3. Scraper starten
python scraper.py

# 4. Ergebnis öffnen
open output/index.html
```

## ☁️ Automatisierung (täglich, kostenlos)

### Variante A: GitHub Actions (empfohlen)

1. Repo auf GitHub erstellen
2. Code hochladen
3. In GitHub → Settings → Pages → Source: `gh-pages` Branch wählen
4. Das Script läuft automatisch täglich um 08:00 Uhr
5. Deine Seite ist kostenlos unter `https://USERNAME.github.io/REPO` erreichbar

### Variante B: Eigener Server / Raspberry Pi

```bash
# Cron-Job einrichten (täglich 08:00 Uhr)
crontab -e
# Zeile hinzufügen:
0 8 * * * cd /pfad/zu/trend-affiliate && python scraper.py >> logs/cron.log 2>&1
```

## 💰 Affiliate-Links einrichten

### Amazon (Haupteinnahme)

1. Anmelden: https://affiliate-program.amazon.de
2. Du brauchst eine Website/App (GitHub Pages reicht!)
3. Nach Genehmigung: deinen Tag in `scraper.py` eintragen
4. Provision: 1–10% je nach Kategorie (Mode: ~8%, Elektronik: ~3%)

### Weitere Netzwerke (optional)

| Netzwerk | Link | Provision |
|----------|------|-----------|
| Awin | https://www.awin.com/de | variabel |
| Adcell | https://www.adcell.de | variabel |
| TradeDoubler | https://www.tradedoubler.com/de | variabel |

## 📊 Datenquellen

| Quelle | Methode | Kosten |
|--------|---------|--------|
| Google Trends | pytrends (offiziell) | kostenlos |
| Reddit | Öffentliche JSON API | kostenlos |
| Amazon | Affiliate-Suchlinks | kostenlos |

## 🗂 Projektstruktur

```
trend-affiliate/
├── scraper.py          # Hauptscript
├── requirements.txt    # Abhängigkeiten
├── README.md
├── output/
│   ├── index.html      # Generierte Seite
│   └── trends_*.json   # Rohdaten (täglich)
└── .github/
    └── workflows/
        └── daily.yml   # GitHub Actions
```
