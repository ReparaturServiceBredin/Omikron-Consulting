"""Zentrale Kunden-Konfiguration: Programmname, Firmendaten, Farben und Standardwerte aus `firma.toml`.

Es gibt genau EINE Stelle für alles, was eine Installation von einer anderen unterscheidet: die Datei `firma.toml`
im Projektordner (bzw. in der EXE eingebaut). Sie wird so gelesen:
  1. Datei aus der Umgebungsvariable `RSB_FIRMA_DATEI` (falls gesetzt)
  2. `firma.toml` neben der EXE (zum Anpassen ohne neu zu bauen)
  3. die mitgelieferte `firma.toml` (Projektordner bzw. in der EXE eingebaut)

Die Werte aus `[firma]`, `[farben]`, `[standardwerte]` und `[einstellungen]` werden beim ERSTEN Start in die neue,
leere Datenbank übernommen. Danach ändert man sie in der App unter *Einstellungen* (dort gespeicherte Werte haben
Vorrang). Programmname, Kurzname (Name der EXE und des Datenordners) und Update-Quelle gelten immer.
"""
import os
import sys
import tomllib
from functools import lru_cache
from pathlib import Path

DATEINAME = "firma.toml"

# Fallback, falls keine firma.toml gefunden wird: neutrale Werte, keine Firmendaten
_STANDARD = {
    "programm": {"name": "Buchhaltung", "kurzname": "Buchhaltung", "update_repo": ""},
    "firma": {},
    "farben": {"primaer": "#1C3F6E", "sekundaer": "#5D6670", "schrift": "Montserrat"},
    "standardwerte": {},
    "einstellungen": {},
}

# [standardwerte] in firma.toml (verständliche Namen, Beträge in Euro) → interne Einstellung (Beträge in Cent)
_GELD = {
    "stundensatz_euro": "ak_stundensatz",
    "fahrzeit_stundensatz_euro": "ak_fahrzeit_satz",
    "km_satz_euro": "ak_km_satz",
    "anfahrt_pauschale_euro": "ak_anfahrt_pauschale",
    "verpflegung_8h_euro": "ak_verpflegung_8h",
    "verpflegung_24h_euro": "ak_verpflegung_24h",
    "mahngebuehr_1_euro": "mahngebuehr_cent",
    "mahngebuehr_2_euro": "mahngebuehr_2_cent",
}
_DIREKT = {
    "steuer_modus": "steuer_modus",
    "mwst_satz": "regel_steuersatz",
    "zahlungsziel_privat_tage": "zahlungsziel_privat",
    "zahlungsziel_firma_tage": "zahlungsziel_firma",
    "anfahrt_art": "ak_anfahrt",
    "kva_pauschalen": "kva_gebuehren",
    "garantie_monate": "garantie_monate",
    "leistungsarten": "leistungsarten",
    "zahlungsarten_text": "zahlungsarten_text",
}


def _basis():
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))


def kandidaten():
    liste = []
    if os.environ.get("RSB_FIRMA_DATEI"):
        liste.append(Path(os.environ["RSB_FIRMA_DATEI"]))
    if getattr(sys, "frozen", False):
        liste.append(Path(sys.executable).resolve().parent / DATEINAME)
    liste.append(_basis() / DATEINAME)
    return liste


@lru_cache(maxsize=1)
def laden():
    """Inhalt der ersten gefundenen firma.toml, ergänzt um die neutralen Standardwerte."""
    daten = {}
    for pfad in kandidaten():
        if pfad.is_file():
            with open(pfad, "rb") as f:
                daten = tomllib.load(f)
            break
    ergebnis = {}
    for abschnitt, standard in _STANDARD.items():
        ergebnis[abschnitt] = {**standard, **(daten.get(abschnitt) or {})}
    return ergebnis


def programm_name():
    """Anzeigename, z. B. „Omikron Consulting – Buchhaltung“ (Fenstertitel, Browser-Tab, PDF-Eigenschaften)."""
    return laden()["programm"]["name"]


def kurzname():
    """Name ohne Leerzeichen für EXE-Datei und Datenordner, z. B. „Omikron-Buchhaltung“."""
    return laden()["programm"]["kurzname"]


def exe_name():
    return f"{kurzname()}.exe"


def update_repo():
    """GitHub-Repository („Besitzer/Name“), aus dem die EXE Updates lädt. Leer = keine Updates."""
    return os.environ.get("RSB_UPDATE_REPO") or laden()["programm"].get("update_repo") or ""


def firmenname():
    return laden()["firma"].get("firma_name") or programm_name()


def einstellungen():
    """Startwerte für die Einstellungen einer neuen Datenbank (überschreiben db.STANDARD_EINSTELLUNGEN)."""
    cfg = laden()
    werte = {}
    for k, v in cfg["firma"].items():
        werte[k] = v
    if cfg["firma"].get("firma_name"):
        werte.setdefault("absender_name", cfg["firma"]["firma_name"])
    if cfg["firma"].get("email"):
        werte.setdefault("absender_email", cfg["firma"]["email"])
    if cfg["firma"].get("inhaber"):
        werte.setdefault("kontoinhaber", cfg["firma"]["inhaber"])
    farben = cfg["farben"]
    werte["farbe_primaer"] = farben["primaer"]
    werte["farbe_sekundaer"] = farben["sekundaer"]
    werte["schrift"] = farben["schrift"]
    for k, v in cfg["standardwerte"].items():
        if k in _GELD:
            werte[_GELD[k]] = int(round(float(v) * 100))
        elif k in _DIREKT:
            werte[_DIREKT[k]] = v
        else:
            raise ValueError(f"firma.toml: unbekannter Eintrag „{k}“ unter [standardwerte]")
    werte.update(cfg["einstellungen"])
    return werte
