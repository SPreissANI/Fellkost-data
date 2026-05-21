"""
Fellkost.de Produktcrawler
--------------------------
Liest Produktdaten von fellkost.de und speichert sie als JSON-Dateien.
Diese Dateien werden dann automatisch in GitHub gespeichert.
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# ── Konfiguration ──────────────────────────────────────────────────────────────
BASE_URL = "https://www.fellkost.de"

KATEGORIEN = {
    "hund_nassfutter":   "/content/partners/produkte/?category=hund&sub=nassfutter",
    "hund_barf":         "/content/partners/produkte/?category=hund&sub=barf",
    "hund_flocken":      "/content/partners/produkte/?category=hund&sub=flocken",
    "hund_snacks":       "/content/partners/produkte/?category=hund&sub=snacks",
    "hund_ernaehrung":   "/content/partners/produkte/?category=hund&sub=nahrungsergaenzung",
    "katze_nassfutter":  "/content/partners/produkte/?category=katze&sub=nassfutter",
    "katze_barf":        "/content/partners/produkte/?category=katze&sub=barf",
    "katze_snacks":      "/content/partners/produkte/?category=katze&sub=snacks",
    "katze_ernaehrung":  "/content/partners/produkte/?category=katze&sub=nahrungsergaenzung",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; FellkostBot/1.0; +https://fellkost.de)"
}

OUTPUT_DIR = "daten"  # Ordner wo die JSON-Dateien gespeichert werden

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def seite_laden(url):
    """Lädt eine Webseite und gibt das BeautifulSoup-Objekt zurück."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"  ⚠️  Fehler beim Laden von {url}: {e}")
        return None


def produkte_aus_seite_lesen(soup, kategorie):
    """Liest Produktdaten aus einer geparsten Seite."""
    produkte = []

    # Anifit-Shops nutzen typischerweise .product-item oder ähnliche Klassen
    # Wir versuchen mehrere gängige Selektoren
    selektoren = [
        "div.product-item",
        "div.product",
        "li.product",
        "article.product",
        ".product-list-item",
        ".item-product",
    ]

    items = []
    for sel in selektoren:
        items = soup.select(sel)
        if items:
            break

    # Fallback: alle Links mit Produktnamen suchen
    if not items:
        # Versuche Produktnamen direkt aus Überschriften zu lesen
        for tag in soup.select("h2, h3, .product-name, .item-name"):
            name = tag.get_text(strip=True)
            if name and len(name) > 3:
                produkte.append({
                    "name": name,
                    "kategorie": kategorie,
                    "preis": None,
                    "beschreibung": None,
                    "url": None,
                    "gescannt_am": datetime.now().isoformat()
                })
        return produkte

    for item in items:
        # Name
        name_tag = item.select_one("h2, h3, .product-name, .item-title, .name")
        name = name_tag.get_text(strip=True) if name_tag else "Unbekannt"

        # Preis
        preis_tag = item.select_one(".price, .product-price, .item-price, [class*='price']")
        preis = preis_tag.get_text(strip=True) if preis_tag else None

        # Beschreibung
        beschr_tag = item.select_one(".description, .product-description, p")
        beschreibung = beschr_tag.get_text(strip=True) if beschr_tag else None

        # Link
        link_tag = item.select_one("a[href]")
        url = BASE_URL + link_tag["href"] if link_tag and link_tag["href"].startswith("/") else (
            link_tag["href"] if link_tag else None
        )

        if name and name != "Unbekannt":
            produkte.append({
                "name": name,
                "kategorie": kategorie,
                "preis": preis,
                "beschreibung": beschreibung,
                "url": url,
                "gescannt_am": datetime.now().isoformat()
            })

    return produkte


# ── Hauptprogramm ──────────────────────────────────────────────────────────────

def crawlen():
    print("🐾 Fellkost Crawler startet...")
    print(f"   Zeitstempel: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")

    alle_produkte = []
    ergebnisse = {}

    # Zuerst die Hauptproduktseite laden (beste Datenquelle)
    haupt_url = f"{BASE_URL}/content/partners/produkte/"
    print(f"📥 Lade Hauptproduktseite: {haupt_url}")
    soup = seite_laden(haupt_url)

    if soup:
        # Alle Produktlinks sammeln
        alle_links = soup.select("a[href*='/produkte/']")
        print(f"   → {len(alle_links)} Produktlinks gefunden")

        # Produktnamen direkt von der Übersichtsseite
        produkte_haupt = produkte_aus_seite_lesen(soup, "alle")
        print(f"   → {len(produkte_haupt)} Produkte auf Hauptseite erkannt")
        alle_produkte.extend(produkte_haupt)

    # Einzelne Kategorieseiten
    for kat_name, kat_pfad in KATEGORIEN.items():
        url = BASE_URL + kat_pfad
        print(f"\n📥 Lade Kategorie '{kat_name}': {url}")
        soup = seite_laden(url)

        if soup:
            produkte = produkte_aus_seite_lesen(soup, kat_name)
            print(f"   → {len(produkte)} Produkte gefunden")
            ergebnisse[kat_name] = produkte
            alle_produkte.extend(produkte)
        else:
            ergebnisse[kat_name] = []

    # Duplikate entfernen (nach Name)
    gesehen = set()
    unique_produkte = []
    for p in alle_produkte:
        if p["name"] not in gesehen:
            gesehen.add(p["name"])
            unique_produkte.append(p)

    print(f"\n✅ Gesamt: {len(unique_produkte)} unique Produkte gefunden")

    # ── JSON-Dateien speichern ─────────────────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. Alle Produkte zusammen
    gesamt_datei = os.path.join(OUTPUT_DIR, "alle_produkte.json")
    with open(gesamt_datei, "w", encoding="utf-8") as f:
        json.dump({
            "quelle": BASE_URL,
            "letzte_aktualisierung": datetime.now().isoformat(),
            "anzahl_produkte": len(unique_produkte),
            "produkte": unique_produkte
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Gespeichert: {gesamt_datei}")

    # 2. Hund-Produkte
    hund_produkte = [p for p in unique_produkte if "hund" in p.get("kategorie", "").lower() or p.get("kategorie") == "alle"]
    hund_datei = os.path.join(OUTPUT_DIR, "produkte_hund.json")
    with open(hund_datei, "w", encoding="utf-8") as f:
        json.dump({
            "letzte_aktualisierung": datetime.now().isoformat(),
            "anzahl": len(hund_produkte),
            "produkte": hund_produkte
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Gespeichert: {hund_datei}")

    # 3. Katzen-Produkte
    katze_produkte = [p for p in unique_produkte if "katze" in p.get("kategorie", "").lower()]
    katze_datei = os.path.join(OUTPUT_DIR, "produkte_katze.json")
    with open(katze_datei, "w", encoding="utf-8") as f:
        json.dump({
            "letzte_aktualisierung": datetime.now().isoformat(),
            "anzahl": len(katze_produkte),
            "produkte": katze_produkte
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Gespeichert: {katze_datei}")

    # 4. Zusammenfassung
    summary_datei = os.path.join(OUTPUT_DIR, "zusammenfassung.json")
    with open(summary_datei, "w", encoding="utf-8") as f:
        json.dump({
            "letzte_aktualisierung": datetime.now().isoformat(),
            "gesamt_produkte": len(unique_produkte),
            "hund_produkte": len(hund_produkte),
            "katze_produkte": len(katze_produkte),
            "kategorien": {k: len(v) for k, v in ergebnisse.items()},
            "status": "erfolgreich"
        }, f, ensure_ascii=False, indent=2)
    print(f"💾 Gespeichert: {summary_datei}")

    print("\n🎉 Crawler fertig!")
    return unique_produkte


if __name__ == "__main__":
    crawlen()
