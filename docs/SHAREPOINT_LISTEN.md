# Daten in SharePoint-Listen statt eigener Datenbank?

**Stand:** Bewertung, nicht umgesetzt. Das Programm speichert weiterhin in einer eigenen SQLite-Datenbank
(`/home/daten/buchhaltung.db` auf Azure) plus Dateiordnern für Belege, PDFs und Fotos.

## Wie es heute aussieht

- Rund **60 Tabellen** (Kunden, Dokumente mit Positionen, Zahlungen, Mahnungen, Aufträge, Lager, Kasse, Verträge,
  Protokoll …) mit Fremdschlüsseln, Triggern und Transaktionen.
- **GoBD-Funktionen** hängen an der Datenbank: unveränderliche, lückenlose Rechnungsnummern, Festschreiben,
  Änderungsprotokoll mit Prüfsummenkette, Trigger, die festgeschriebene Belege gegen Änderungen sperren.
- Viele Auswertungen sind SQL-Abfragen über mehrere Tabellen (offene Posten, Finanzübersicht, DATEV-Export).

## Vorteile von SharePoint-Listen (über Microsoft Graph)

- Daten liegen **im Microsoft-365-Konto des Kunden**, werden von Microsoft gesichert und unterliegen dessen
  Aufbewahrungs-/Compliance-Richtlinien.
- Kunden, Aufträge usw. sind **direkt in SharePoint/Teams sichtbar**, filterbar, exportierbar nach Excel, nutzbar in
  Power Automate.
- Kein eigener Datenbank-Speicher; Belege könnten in einer Dokumentbibliothek liegen.
- Berechtigungen über SharePoint-Gruppen.

## Nachteile

- **Keine Transaktionen:** Eine Rechnung besteht aus Kopf, Positionen, Nummernvergabe und Protokolleintrag. Bricht
  die Verbindung mittendrin ab, bleiben halbe Belege übrig. Für eine Buchhaltung ist das ein ernstes Risiko.
- **Lückenlose Rechnungsnummern** (gesetzlich gefordert) lassen sich mit Listen nur mit Zusatzaufwand sicher vergeben
  (gleichzeitige Zugriffe, Sperren über ETags/Wiederholungen).
- **GoBD-Unveränderbarkeit:** Listen-Einträge kann jede Person mit Bearbeitungsrecht direkt in SharePoint ändern –
  am Programm vorbei. Die heutigen Datenbank-Sperren und die Protokoll-Prüfsummen greifen dort nicht.
- **Abfragen:** Keine Joins, Summen oder Gruppierungen über Listen hinweg; Auswertungen müssten alle Einträge laden und
  im Programm rechnen. Ab 5.000 Einträgen (Listenansichtsschwelle) braucht jede Abfrage indizierte Spalten.
- **Geschwindigkeit und Grenzen:** Jede Seite bräuchte mehrere Graph-Aufrufe (100–300 ms je Aufruf), dazu
  Drosselung durch Microsoft bei vielen Zugriffen.
- **Programm muss weiterhin auf Azure laufen** (PDF-Erzeugung, E-Mail, Hintergrundaufgaben) – SharePoint ersetzt also
  nur den Speicher, nicht den Server.
- Zusätzliche Berechtigungen in Entra (Graph `Sites.Selected` bzw. `Sites.ReadWrite.All`) und deren Pflege.

## Aufwand

| Schritt | Aufwand (Richtwert) |
|---|---|
| Datenzugriffsschicht neu schreiben (rund 60 Tabellen, rund 900 Datenbankaufrufe im Code) | 25–40 Personentage |
| Nummernvergabe, Festschreiben und Protokoll ohne Datenbank-Transaktionen sicher nachbauen | 5–10 Personentage |
| Auswertungen (Finanzen, offene Posten, DATEV, Lager) ohne SQL neu rechnen | 5–10 Personentage |
| Belege/PDFs/Fotos in Dokumentbibliothek, Sicherung/Wiederherstellung neu | 3–5 Personentage |
| Listen anlegen (Provisioning), Berechtigungen, Tests, Datenübernahme | 5–8 Personentage |
| **Summe** | **ca. 45–75 Personentage**, danach höherer Pflegeaufwand bei jeder neuen Funktion |

## Empfehlung

**Eigene Datenbank beibehalten** (SQLite auf Azure App Service, eine Instanz). Sie ist für eine Buchhaltung mit
GoBD-Anforderungen deutlich sicherer und schneller, und der Umbau wäre sehr aufwendig.

Sinnvolle, kleine Ergänzungen statt Komplett-Umbau, falls gewünscht:

1. **Sicherungen automatisch in eine SharePoint-Dokumentbibliothek** kopieren (Graph, nur Datei-Upload):
   ca. 2–3 Personentage. Damit liegen die Daten zusätzlich im Microsoft-365-Konto des Kunden.
2. **Festgeschriebene Rechnungs-PDFs** zusätzlich in eine Dokumentbibliothek ablegen (Ablage/Suche in SharePoint):
   ca. 2–3 Personentage.
3. Später bei Bedarf **Azure Database for PostgreSQL** statt SQLite, wenn mehrere Server-Instanzen oder sehr viele
   gleichzeitige Nutzer nötig werden: ca. 10–15 Personentage.
