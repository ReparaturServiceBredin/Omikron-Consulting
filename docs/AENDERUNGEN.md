# Versionsprotokoll

Alle Versionen mit Neuerungen, Änderungen und Fehlerbehebungen. Die neueste Version steht oben.

**So funktionieren Versionen**
- Die Versionsnummer steht unten links im Programm und unter *Einstellungen → Programm & Updates*.
- Aufbau: `Haupt.Funktion.Korrektur`. Die mittlere Zahl steigt bei neuen Funktionen, die letzte Zahl bei
  reinen Fehlerbehebungen.
- Jede Version gibt es als Windows-EXE unter *GitHub → Releases* dieses Repositorys. Die EXE installiert neue
  Versionen selbst und erstellt vorher ein Backup.
- Ihre Daten bleiben bei jedem Update erhalten. Neue Datenbankfelder ergänzt das Programm beim Start selbst.
- Der Abschnitt einer Version erscheint im Programm als Hinweistext, wenn diese Version zum Update bereitsteht.

| Version | Datum | Schwerpunkt |
|---|---|---|
| 1.1.2 | 04.11.2026 | Installationspaket für SharePoint |
| 1.1.1 | 04.11.2026 | Finanzen: Einnahmen nach Leistungsart, nur berechnete Leistungen |
| 1.1.0 | 04.11.2026 | Oberfläche anpassen: Bausteine, Spalten, eigene Einträge in Auswahllisten |
| 1.0.0 | 04.11.2026 | Erste eigene Version für Omikron Consulting |

---

## 1.1.2 – 04.11.2026
### Neu
- **Installationspaket für SharePoint** (`Omikron-Buchhaltung-SharePoint.zip` bei jeder Veröffentlichung):
  `Installieren.cmd` lädt die neueste Version, installiert ohne Administratorrechte, legt Verknüpfungen auf dem
  Desktop und im Startmenü an. `Deinstallieren.cmd` entfernt das Programm, die Daten bleiben erhalten.
  Dazu eine Anleitung als PDF.

## 1.1.1 – 04.11.2026
### Geändert
- **Finanzen → Einnahmen:** Statt fester Zeilen (Reparaturen, Artikelverkauf, Leihgebühren, KVA-Gebühren) zeigt
  die Aufstellung jetzt die **Leistungsarten, die im Zeitraum tatsächlich berechnet wurden** – z. B. Beratung,
  Schulung, Projekt –, größte zuerst. Maßgeblich ist die Leistungsart der Rechnungsposition, sonst die des Artikels.
  Artikel ohne Leistungsart zählen als Artikelverkauf, Positionen ohne Leistungsart als „Sonstige Leistungen“.
  Ohne Umsatz erscheint der Hinweis „Im Zeitraum wurde nichts berechnet.“

## 1.1.0 – 04.11.2026
### Neu
- **Übersicht und Finanzen anpassen:** Knopf **„Anpassen“** oben rechts. Jeder Baustein lässt sich **ausblenden
  bzw. einblenden**, **verschieben** (ziehen oder Pfeile ↑ ↓) und in der **Breite** ändern (¼, ⅓, ½, ⅔, ganz).
  „Fertig“ beendet das Anpassen, „Standard“ stellt die ursprüngliche Anordnung wieder her. Die Einstellung gilt je
  Benutzer und auf allen Geräten.
- **Zusätzliche Kacheln auf der Übersicht** zum Einblenden: neue Anfragen, überfällige Rechnungen,
  Benachrichtigungen, überfällige Leihgeräte, Lager unter Mindestbestand, Schnellzugriff.
- **Tabellenspalten ein-/ausblenden:** Bei allen Listen mit mehreren Spalten oben rechts **„⚙ Spalten“**.
- **Eigene Einträge in Auswahllisten:** Wo eine Liste nur Vorschläge enthält (Leistungsart, Kostenart,
  Fixkosten-Kategorie, Gerätetyp, Anrede, Versanddienst, Vertragskategorie, Nebenkosten im Arbeitskalender), gibt es
  **„✎ Eigener Eintrag …“**. Neue Leistungsarten, Kostenarten und Fixkosten-Kategorien werden automatisch in die
  Vorgabenliste übernommen und stehen beim nächsten Mal zur Auswahl.
- Auswahllisten, die feste Programmlogik steuern (z. B. Status, Zahlart, Besteuerung, Abrechnungsart), bleiben
  bewusst fest, damit Berechnungen und Buchungen stimmen.

## 1.0.0 – 04.11.2026
### Neu
- **Eigenständige Installation** mit leerem Datenbestand: keine Kunden, Belege oder Vorlagen aus anderen
  Installationen. Alte Datenordner auf dem Rechner werden nicht mehr automatisch übernommen.
- **Zentrale Konfiguration** in `firma.toml`: Programmname, Firmendaten, Farben und Standardwerte (MwSt.,
  Stundensatz, Kilometersatz, Pauschalen, Zahlungsziele) an einer Stelle.
- **Anmeldung mit dem Microsoft-Konto** (Microsoft Entra ID) beim Betrieb auf Azure App Service
  (`RSB_ANMELDUNG=entra`), Rollen Inhaber/Mitarbeiter über E-Mail-Liste oder App-Rolle.
- **Einbetten in SharePoint**: Freigabe nur für die eigene SharePoint-Adresse (`RSB_EINBETTEN_ERLAUBT`),
  Anmeldung im eingebetteten Fenster per Popup, Ausweg „In neuem Tab öffnen“.
- Logo von Omikron Consulting, Programmsymbol mit den drei Waben, EXE heißt `Omikron-Buchhaltung.exe`.

### Technik
- `RSB_SQLITE_JOURNAL=DELETE` für den Betrieb der Datenbank auf Netzlaufwerken (Azure App Service `/home`).
- Neue Tests für Neuinstallation, Microsoft-Anmeldung und Einbetten.
