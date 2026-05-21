"""
Fellkost.de Produktcrawler - Version 2
---------------------------------------
Nutzt die echte Anifit Partner-URL-Struktur mit Partner-ID 466587
"""

import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

# ── Konfiguration ──────────────────────────────────────────────────────────────
PARTNER_ID = "466587"
BASE_URL = f"https://www.fellkost.de/content/partners/{PARTNER_ID}"

# Echte Anifit Kategorie-IDs (Standard für alle Partnershops)
KATEGORIEN = {
    "hund_alle":        f"{BASE_URL}/shop/shop/?lang=ger&category=62182",
    "hund_nassfutter":  f"{BASE_URL}/shop/shop/?lang=ger&category=62183",
    "hund_barf":        f"{BASE_URL}/shop/shop/?lang=ger&category=62184",
    "hund_flocken":     f"{BASE_URL}/shop/shop/?lang=ger&category=62185",
    "hund_snacks":      f"{BASE_URL}/shop/shop/?lang=ger&category=62186",
    "hund_ernaehrung":  f"{BASE_URL}/shop/shop/?lang=ger&category=62187",
    "katze_alle":       f"{BASE_URL}/shop/shop/?lang=ger&category=62196",
    "katze_nassfutter": f"{BASE_URL}/shop/shop/?lang=ger&category=62197",
    "katze_barf":       f"{BASE_URL}/shop/shop/?lang=ger&category=62198",
    "katze_snacks":     f"{BASE_URL}/shop/shop/?lang=ger&category=62199",
    "katze_ernaehrung": f"{BASE_URL}/shop/shop/?lang=ger&category=62200",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-DE,de;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}

OUTPUT_DIR = "daten"

# ── Hilfsfunktionen ────────────────────────────────────────────────────────────

def seite_laden(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as e:
        print(f"  ⚠️  Fehler beim Laden von {url}: {e}")
        return None


def produkte_lesen(soup, kategorie):
    produkte = []
    if not soup:
        return produkte

    # Anifit nutzt typischerweise diese Selektoren
    selektoren = [
        ".article-item",
        ".product-item",
        ".shop-item",
        "div[class*='article']",
        "div[class*='product']",
        "li[class*='article']",
        "li[class*='product']",
        ".item",
    ]

    items = []
    for sel in selektoren:
        items = soup.select(sel)
        if len(items) > 2:
            print(f"   → Selektor '{sel}' gefunden: {len(items)} Einträge")
            break

    # Fallback: alle Artikellinks direkt suchen
    if not items:
        links = soup.select(f"a[href*='/shop/article/']")
        print(f"   → Fallback: {len(links)} Artikellinks gefunden")
        for link in links:
            name = link.get_text(strip=True)
            href = link.get("href", "")
            url = f"https://www.fellkost.de{href}" if href.startswith("/") else href
            if name and len(name) > 2:
                produkte.append({
                    "name": name,
                    "kategorie": kategorie,
                    "preis": None,
                    "beschreibung": None,
                    "url": url,
                    "gescannt_am": datetime.now().isoformat()
                })
        return produkte

    for item in items:
        name_tag = item.select_one("h2, h3, h4, .name, .title, .article-name, .product-name")
        name = name_tag.get_text(strip=True) if name_tag else ""

        preis_tag = item.select_one(".price, .artikel-preis, [class*='price']")
        preis = preis_tag.get_text(strip=True) if preis_tag else None

        beschr_tag = item.select_one(".description, .short-desc, p")
        beschreibung = beschr_tag.get_text(strip=True)[:200] if beschr_tag else None

        link_tag = item.select_one("a[href]")
        href = link_tag["href"] if link_tag else ""
        url = f"https://www.fellkost.de{href}" if href.startswith("/") else href

        if name:
            produkte.append({
                "name": name,
                "kategorie": kategorie,
                "preis": preis,
                "beschreibung": beschreibung,
                "url": url or None,
                "gescannt_am": datetime.now().isoformat()
            })

    return produkte


# ── Hauptprogramm ──────────────────────────────────────────────────────────────

def crawlen():
    print("🐾 Fellkost Crawler v2 startet...")
    print(f"   Partner-ID: {PARTNER_ID}")
    print(f"   Zeitstempel: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")

    alle_produkte = []
    ergebnisse = {}

    for kat_name, url in KATEGORIEN.items():
        print(f"\n📥 Lade: {kat_name}")
        print(f"   URL: {url}")
        soup = seite_laden(url)

        if soup:
            # Debug: HTML-Schnipsel ausgeben
            body = soup.find("body")
            if body:
                text = body.get_text(separator=" ", strip=True)[:300]
                print(f"   Seiteninhalt (Anfang): {text}")

            produkte = produkte_lesen(soup, kat_name)
            print(f"   → {len(produkte)} Produkte gefunden")
            ergebnisse[kat_name] = produkte
            alle_produkte.extend(produkte)
        else:
            ergebnisse[kat_name] = []

    # Duplikate entfernen
    gesehen = set()
    unique = []
    for p in alle_produkte:
        key = p["name"] + str(p.get("url", ""))
        if key not in gesehen:
            gesehen.add(key)
            unique.append(p)

    print(f"\n✅ Gesamt: {len(unique)} unique Produkte")

    # Speichern
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    with open(f"{OUTPUT_DIR}/alle_produkte.json", "w", encoding="utf-8") as f:
        json.dump({
            "quelle": BASE_URL,
            "letzte_aktualisierung": datetime.now().isoformat(),
            "anzahl_produkte": len(unique),
            "produkte": unique
        }, f, ensure_ascii=False, indent=2)

    hund = [p for p in unique if "hund" in p["kategorie"]]
    with open(f"{OUTPUT_DIR}/produkte_hund.json", "w", encoding="utf-8") as f:
        json.dump({"letzte_aktualisierung": datetime.now().isoformat(), "anzahl": len(hund), "produkte": hund}, f, ensure_ascii=False, indent=2)

    katze = [p for p in unique if "katze" in p["kategorie"]]
    with open(f"{OUTPUT_DIR}/produkte_katze.json", "w", encoding="utf-8") as f:
        json.dump({"letzte_aktualisierung": datetime.now().isoformat(), "anzahl": len(katze), "produkte": katze}, f, ensure_ascii=False, indent=2)

    with open(f"{OUTPUT_DIR}/zusammenfassung.json", "w", encoding="utf-8") as f:
        json.dump({
            "letzte_aktualisierung": datetime.now().isoformat(),
            "gesamt_produkte": len(unique),
            "hund_produkte": len(hund),
            "katze_produkte": len(katze),
            "kategorien": {k: len(v) for k, v in ergebnisse.items()},
            "status": "erfolgreich"
        }, f, ensure_ascii=False, indent=2)

    print("🎉 Crawler fertig!")


if __name__ == "__main__":
    crawlen()
