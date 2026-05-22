"""
Fellkost Crawler v3
--------------------
Liest Produktdaten direkt aus den JSON-Dateien im GitHub-Repository.
Kein Website-Crawling mehr - stabiler und zuverlässiger.
"""

import requests
import json
import os
from datetime import datetime

# ── Konfiguration ──────────────────────────────────────────────────────────────
GITHUB_USER = "SPreissANI"
GITHUB_REPO = "Fellkost-data"
BRANCH = "main"
BASE_RAW = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/{BRANCH}/daten"

QUELLEN = {
    "alle_produkte":  f"{BASE_RAW}/alle_produkte.json",
    "produkte_hund":  f"{BASE_RAW}/produkte_hund.json",
    "produkte_katze": f"{BASE_RAW}/produkte_katze.json",
}

OUTPUT_DIR = "daten"

# ── Hauptprogramm ──────────────────────────────────────────────────────────────

def laden():
    print("🐾 Fellkost Daten-Loader v3 startet...")
    print(f"   Zeitstempel: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    alle_produkte = []

    for name, url in QUELLEN.items():
        print(f"📥 Lade: {name}")
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            daten = response.json()

            # Produkte sammeln
            if "produkte" in daten:
                produkte = daten["produkte"]
                print(f"   → {len(produkte)} Produkte geladen")
                if name == "alle_produkte":
                    alle_produkte = produkte
            
            # Datei lokal speichern
            with open(f"{OUTPUT_DIR}/{name}.json", "w", encoding="utf-8") as f:
                json.dump(daten, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"   ⚠️ Fehler: {e}")

    # Zusammenfassung aktualisieren
    hund = [p for p in alle_produkte if p.get("kategorie") == "hund"]
    katze = [p for p in alle_produkte if p.get("kategorie") == "katze"]

    summary = {
        "letzte_aktualisierung": datetime.now().isoformat(),
        "gesamt_produkte": len(alle_produkte),
        "hund_produkte": len(hund),
        "katze_produkte": len(katze),
        "status": "erfolgreich"
    }

    with open(f"{OUTPUT_DIR}/zusammenfassung.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Fertig!")
    print(f"   Gesamt: {len(alle_produkte)} Produkte")
    print(f"   Hund:   {len(hund)}")
    print(f"   Katze:  {len(katze)}")


if __name__ == "__main__":
    laden()
