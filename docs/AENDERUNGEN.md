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
| 1.0.0 | 04.11.2026 | Erste eigene Version für Omikron Consulting |

---

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
- Logo und Programmsymbol (Platzhalter) für Omikron Consulting, EXE heißt `Omikron-Buchhaltung.exe`.

### Technik
- `RSB_SQLITE_JOURNAL=DELETE` für den Betrieb der Datenbank auf Netzlaufwerken (Azure App Service `/home`).
- Neue Tests für Neuinstallation, Microsoft-Anmeldung und Einbetten.
