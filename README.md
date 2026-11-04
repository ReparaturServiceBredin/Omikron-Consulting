# Omikron Consulting – Buchhaltung & Rechnungen

Rechnungs- und Buchhaltungsprogramm für **Omikron Consulting**: Kunden, Angebote, Aufträge, Rechnungen als PDF und
E-Rechnung, Zahlungen und Mahnwesen, Arbeitskalender mit Zeiterfassung, Verträge, Lager, Kasse, DATEV-Export.

Das Programm startet mit einem **leeren Datenbestand**. Firmenname, Logo, Farben und Standardwerte stehen zentral in
[`firma.toml`](firma.toml) und sind danach in der App unter *Einstellungen* änderbar.

| Dokument | Inhalt |
|---|---|
| **[EINRICHTUNG.md](EINRICHTUNG.md)** | **Einrichtung Schritt für Schritt:** Konten, Azure, Microsoft-Anmeldung, SharePoint, Logo & Standardwerte |
| [docs/SHAREPOINT_LISTEN.md](docs/SHAREPOINT_LISTEN.md) | Bewertung: Daten in SharePoint-Listen statt eigener Datenbank? |
| [docs/ANLEITUNG.md](docs/ANLEITUNG.md) | Bedienung: Rechnung schreiben, Layout & Textbausteine, Backup & Wiederherstellung |
| [docs/BETRIEB_SERVER.md](docs/BETRIEB_SERVER.md) | Alternative: Betrieb auf einem eigenen Linux-Server mit Docker |
| [docs/RECHT_UND_GOBD.md](docs/RECHT_UND_GOBD.md) | Pflichtangaben, E-Rechnung, Aufbewahrung, GoBD |
| [docs/AENDERUNGEN.md](docs/AENDERUNGEN.md) | Versionsprotokoll |

## Zwei Betriebsarten

1. **Im Browser, von überall (empfohlen für SharePoint):** Betrieb auf **Azure App Service** im Microsoft-365-Konto
   des Kunden, Anmeldung mit dem Microsoft-Konto, eingebettet in eine SharePoint-Seite.
   Anleitung: [EINRICHTUNG.md](EINRICHTUNG.md).
2. **Lokal unter Windows:** `Omikron-Buchhaltung.exe` aus *Releases* herunterladen, in einen eigenen Ordner legen
   (z. B. `C:\Omikron-Buchhaltung`, nicht in OneDrive) und starten. Die Daten liegen dann unter
   `%LOCALAPPDATA%\Omikron-Buchhaltung\Daten`.

## Technik (kurz)

Python 3.12 · Flask · Waitress · SQLite (eine Datenbankdatei) · ReportLab (PDF) · cryptography · PyInstaller (EXE).
Die Datenbank legt das Programm beim ersten Start selbst leer an (Schema: [`rsb/schema.sql`](rsb/schema.sql),
spätere Änderungen ergänzt `rsb/db.py` automatisch). Alle Zugangsdaten und umgebungsabhängigen Werte kommen aus
Umgebungsvariablen, Vorlage mit Erklärungen: [`.env.example`](.env.example).

Neue Version veröffentlichen: `VERSION_NUMMER` in `rsb/__init__.py` erhöhen, Abschnitt in `docs/AENDERUNGEN.md`
ergänzen und auf `main` übernehmen – GitHub Actions testet, baut die EXE und veröffentlicht sie unter *Releases*.

## Für Entwickler

```bash
python -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m pytest                                   # automatische Tests
RSB_DATEN=Testdaten .venv/bin/python -m rsb.beispieldaten     # Platzhalter-Beispieldaten in separatem Ordner
RSB_DATEN=Testdaten .venv/bin/python -m rsb                   # starten
.venv/bin/python bauen/symbole_erzeugen.py [logo.png]          # Logo/Programmsymbole neu erzeugen
```

Regeln für Änderungen: [docs/ENTWICKLUNG.md](docs/ENTWICKLUNG.md). Interne Namen (`rsb`-Paket, Variablen `RSB_…`)
sind technische Bezeichner und haben keine Bedeutung für die Oberfläche.
