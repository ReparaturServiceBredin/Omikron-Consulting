# Einrichtung – Schritt für Schritt

Diese Anleitung richtet die Buchhaltung so ein, dass Sie sie **über SharePoint von überall** nutzen können:

```
 Browser / SharePoint-Seite ──(eingebettet)──►  Azure App Service  ──►  Datenbank + Belege (/home/daten)
                                                 │
                                                 └── Anmeldung mit dem Microsoft-Konto (Microsoft Entra ID)
```

Sie brauchen dafür keine Programmierkenntnisse. Rechnen Sie mit etwa **1–2 Stunden** für die erste Einrichtung.
Die Menüs im Azure-Portal ändern sich gelegentlich etwas; die Begriffe unten helfen beim Suchen (Suchfeld oben im
Portal).

---

## 1. Welche Konten und Dienste werden gebraucht?

| Was | Wofür | Kosten (Richtwert) |
|---|---|---|
| **Microsoft 365** (z. B. Business Basic/Standard) mit SharePoint | Anmeldung der Mitarbeitenden, SharePoint-Seite | vorhanden |
| **Azure-Abonnement** im selben Microsoft-365-Konto (portal.azure.com, Zahlungsmethode hinterlegen) | Betrieb des Programms | App Service Plan **Basic B1 (Linux)** ca. 12–15 € / Monat |
| Eine Person mit Rolle **Globaler Administrator** oder **Anwendungsadministrator** | einmalig: Anmeldung einrichten | – |
| **GitHub-Zugang** zu diesem Repository | Azure holt das Programm von dort und aktualisiert es automatisch | kostenlos |
| **E-Mail-Postfach mit SMTP-Zugang** (Benutzername/Passwort) | Rechnungen per E-Mail versenden | je nach Anbieter |

> **Hinweis E-Mail:** Microsoft 365 (Exchange Online) erlaubt die Anmeldung per Passwort für IMAP nicht mehr und
> schaltet sie für SMTP ab. Das Programm kann deshalb (noch) nicht über ein Microsoft-365-Postfach senden oder
> abrufen. Verwenden Sie für den Versand ein Postfach eines Anbieters mit SMTP-Passwort (z. B. Ihres
> Webhosters) oder lassen Sie den E-Mail-Versand vorerst aus (PDF herunterladen und selbst versenden).

### Warum Azure App Service und nicht Azure Static Web Apps?

Azure Static Web Apps kann nur fertige, unveränderliche Webseiten ausliefern. Dieses Programm braucht aber einen
**laufenden Server** (Python), der PDFs erzeugt, E-Mails versendet und Daten speichert. Die passende Azure-Lösung
dafür ist **Azure App Service (Linux)**: Es bringt die Anmeldung mit dem Microsoft-Konto gleich mit, speichert die
Daten dauerhaft und lässt sich genauso in SharePoint einbetten.

---

## 2. Programm in Azure anlegen (App Service)

1. Auf **portal.azure.com** mit dem Administrator-Konto des Kunden anmelden.
2. Oben im Suchfeld **„App Services“** eingeben → **Erstellen** → **Web-App**.
3. Ausfüllen:
   - **Ressourcengruppe:** *Neu erstellen* → `omikron-buchhaltung`
   - **Name:** z. B. `omikron-buchhaltung` (daraus entsteht die Adresse, z. B.
     `https://omikron-buchhaltung-xxxx.germanywestcentral-01.azurewebsites.net`)
   - **Veröffentlichen:** *Code*
   - **Runtimestapel:** *Python 3.12*
   - **Betriebssystem:** *Linux*
   - **Region:** *Germany West Central* (Daten bleiben in Deutschland)
   - **Tarif:** *Basic B1* (über „Tarif ändern“ / „Explore pricing plans“)
4. **Überprüfen + erstellen** → **Erstellen**. Nach 1–2 Minuten: **Zu Ressource wechseln**.
5. Die **Standarddomäne** auf der Übersichtsseite notieren – das ist die Adresse des Programms
   (im Folgenden `IHRE-APP.azurewebsites.net`).

### 2a. Grundeinstellungen

Im App Service links **Einstellungen → Konfiguration** (bzw. **Allgemeine Einstellungen**):

- **Startbefehl:** `python -m rsb`
- **Immer aktiv (Always On):** *Ein* – sonst laufen Hintergrundaufgaben (Sicherung, Mahnungen, E-Mail-Abruf) nicht
- **Nur HTTPS:** *Ein*
- Speichern.

Unter **Skalieren (horizontal)** muss die Anzahl der Instanzen **1** bleiben (die Datenbank ist eine einzelne Datei).

### 2b. Umgebungsvariablen setzen

Links **Einstellungen → Umgebungsvariablen** → Reiter **App-Einstellungen** → für jede Zeile **+ Hinzufügen**
(Name und Wert genau so übernehmen), danach **Übernehmen** und bestätigen:

| Name | Wert | Bedeutung |
|---|---|---|
| `RSB_MODUS` | `server` | Betrieb als Server |
| `RSB_DATEN` | `/home/daten` | Datenordner (bleibt bei Neustarts und Updates erhalten) |
| `RSB_HOST` | `0.0.0.0` | erreichbar für Azure |
| `RSB_PORT` | `8000` | Port des Programms |
| `WEBSITES_PORT` | `8000` | sagt Azure, wo das Programm lauscht |
| `RSB_HINTER_PROXY` | `1` | Azure leitet die Aufrufe weiter |
| `RSB_SICHERE_COOKIES` | `1` | nur HTTPS |
| `RSB_SQLITE_JOURNAL` | `DELETE` | sichere Datenbank-Einstellung für den Azure-Speicher |
| `RSB_ANMELDUNG` | `entra` | Anmeldung mit dem Microsoft-Konto (Schritt 4) |
| `RSB_ENTRA_INHABER` | z. B. `chefin@omikronconsulting.de` | Personen mit allen Rechten (mehrere mit Komma) |
| `RSB_EINBETTEN_ERLAUBT` | `https://KUNDE.sharepoint.com` | SharePoint-Adresse, in die eingebettet werden darf |
| `SCM_DO_BUILD_DURING_DEPLOYMENT` | `true` | Azure installiert die Programmbausteine selbst |

Optional:

| Name | Wert | Bedeutung |
|---|---|---|
| `RSB_ENTRA_ERLAUBT` | z. B. `@omikronconsulting.de` | nur Konten dieser Domain/Adressen zulassen |
| `RSB_ENTRA_TENANT_ID` | Verzeichnis-ID (Entra → Übersicht → *Mandanten-ID*) | zusätzliche Prüfung des Microsoft-365-Kontos |

`KUNDE` ist der vordere Teil Ihrer SharePoint-Adresse: Steht im Browser `https://omikron.sharepoint.com/sites/…`, dann
ist der Wert `https://omikron.sharepoint.com`. Eine vollständige Liste aller Variablen mit Erklärung steht in
[`.env.example`](.env.example).

> Passwörter (z. B. für das E-Mail-Postfach) gehören **nicht** hierher: Sie werden später in der App unter
> *Einstellungen → E-Mail* eingegeben und verschlüsselt gespeichert.

---

## 3. Programm veröffentlichen (aus GitHub)

1. Im App Service links **Bereitstellung → Bereitstellungscenter**.
2. **Quelle:** *GitHub* → **Autorisieren** und mit dem GitHub-Konto anmelden, das Zugriff auf dieses Repository hat.
3. **Organisation** (Besitzer dieses Repositorys), **Repository:** `Omikron-Consulting`, **Branch:** `main`.
4. **Speichern.** Azure legt dabei selbst einen Ablauf in GitHub an und veröffentlicht das Programm (dauert ca. 5–10
   Minuten; Fortschritt im Reiter **Protokolle**).
5. Ab jetzt wird jede Änderung auf `main` automatisch veröffentlicht. Ihre Daten bleiben dabei erhalten.

Kontrolle: `https://IHRE-APP.azurewebsites.net/version` zeigt die Versionsnummer an.

---

## 4. Anmeldung mit dem Microsoft-Konto einrichten (Microsoft Entra ID)

1. Im App Service links **Einstellungen → Authentifizierung** → **Identitätsanbieter hinzufügen**.
2. **Identitätsanbieter:** *Microsoft*.
3. **App-Registrierung:** *Neue App-Registrierung erstellen*, Name z. B. `Omikron Buchhaltung`.
4. **Unterstützte Kontotypen:** *Aktueller Mandant – Einzelner Mandant* (nur Konten Ihres Microsoft 365).
5. **Zugriff einschränken:** ***Nicht authentifizierten Zugriff zulassen*** auswählen.
   Das ist Absicht: Das Programm prüft die Anmeldung selbst und zeigt im SharePoint-iframe einen eigenen
   Anmeldeknopf (die Microsoft-Anmeldeseite lässt sich nicht im iframe anzeigen). Ohne Anmeldung ist im Programm
   nichts zugänglich.
6. **Token-Speicher:** aktiviert lassen. **Hinzufügen.**

### 4a. Nur berechtigte Personen zulassen (wichtig)

1. **entra.microsoft.com** → **Anwendungen → Unternehmensanwendungen** → `Omikron Buchhaltung` öffnen.
2. **Eigenschaften → Zuweisung erforderlich?** auf **Ja** → Speichern.
3. **Benutzer und Gruppen → Benutzer/Gruppe hinzufügen** → alle Personen (oder eine Gruppe) auswählen, die das
   Programm nutzen dürfen → **Zuweisen**.

Nur zugewiesene Personen können sich jetzt anmelden. Gäste und andere Microsoft-Konten werden abgewiesen.

### 4b. Rechte im Programm

- Wer in `RSB_ENTRA_INHABER` steht, ist **Inhaber** (alle Rechte inkl. Einstellungen, Protokoll, Sicherungen).
- Alle anderen angemeldeten Personen sind **Mitarbeiter** (alles außer Einstellungen, Protokoll, Updates,
  Benutzerverwaltung).
- Für Fortgeschrittene: In der App-Registrierung eine **App-Rolle** mit dem Wert `Inhaber` anlegen und Personen in
  der Unternehmensanwendung zuweisen – wirkt wie ein Eintrag in `RSB_ENTRA_INHABER`.
- Die Benutzerverwaltung mit eigenen Passwörtern im Programm wird bei der Microsoft-Anmeldung nicht gebraucht.

### 4c. Testen

`https://IHRE-APP.azurewebsites.net` im Browser öffnen → **Mit Microsoft anmelden** → mit einem zugewiesenen Konto
anmelden. Danach als Inhaber unter **Einstellungen → Firmendaten** Anschrift, Steuernummer und Bankverbindung
eintragen.

---

## 5. In SharePoint einbetten

### 5a. Domain unter „HTML-Feldsicherheit“ freigeben (einmalig je Website)

Ohne diese Freigabe zeigt SharePoint das Programm im Webpart „Einbetten“ nicht an.

1. Die SharePoint-Website öffnen, auf der das Programm erscheinen soll.
2. Oben rechts **Zahnrad (Einstellungen) → Websiteinformationen → Alle Websiteeinstellungen anzeigen**.
   (Falls nicht sichtbar: an die Adresse der Website `/_layouts/15/settings.aspx` anhängen.)
3. Unter **Websitesammlungsverwaltung** auf **HTML-Feldsicherheit** klicken.
4. Bei **„Mitwirkenden das Einfügen von iframes aus den folgenden Domänen erlauben“** die Adresse **ohne https://**
   eintragen, z. B. `omikron-buchhaltung-xxxx.germanywestcentral-01.azurewebsites.net` → **Hinzufügen** → **OK**.

Dafür braucht man Rechte als **Websitesammlungsadministrator**. Die Änderung kann einige Minuten dauern.

### 5b. Seite mit dem Programm anlegen

1. Auf der Website **Neu → Seite** (oder eine vorhandene Seite **Bearbeiten**).
2. Am besten einen **Abschnitt mit voller Breite** hinzufügen (mehr Platz für das Programm).
3. **+ → Einbetten** wählen und diesen Code einfügen (Adresse anpassen):

   ```html
   <iframe src="https://IHRE-APP.azurewebsites.net/" width="100%" height="900" style="border:0"></iframe>
   ```

4. **Veröffentlichen.**

Tipp: Zusätzlich auf derselben Seite einen Webpart **Schaltfläche** mit dem Text „Buchhaltung im eigenen Fenster
öffnen“ und derselben Adresse anlegen. Für längeres Arbeiten ist das eigene Browserfenster angenehmer.

### 5c. Anmeldung im eingebetteten Programm

- Beim ersten Aufruf erscheint im Programm der Knopf **„Mit Microsoft anmelden“**. Er öffnet die Anmeldung in einem
  **kleinen Fenster (Popup)**. Popups für die SharePoint-Seite ggf. erlauben.
- Nach der Anmeldung schließt sich das Fenster; in Safari/Firefox erscheint manchmal noch ein Knopf **„Weiter“**
  (der Browser fragt dann, ob die eingebettete Seite Cookies verwenden darf – bitte zulassen).
- Klappt es trotzdem nicht (z. B. bei sehr strengen Datenschutz-Einstellungen des Browsers): Link
  **„Programm in neuem Tab öffnen“** benutzen.
- Eingebettet werden darf das Programm **nur** von der eigenen Adresse und der SharePoint-Adresse aus
  `RSB_EINBETTEN_ERLAUBT`; andere Websites können es nicht einbetten.

---

## 6. Firmenname, Logo und Standardwerte ändern

### Im laufenden Betrieb (empfohlen): in der App

Als Inhaber unter **Einstellungen**:

| Was | Wo |
|---|---|
| Firmenname, Anschrift, Steuernummer, Bankverbindung | *Unternehmen → Firmendaten* |
| Logo (Bilddatei hochladen), Farben, Schrift | *Unternehmen → Layout & Dokumente* |
| Umsatzsteuer (MwSt.-Satz bzw. Kleinunternehmer), Zahlungsziele | *Verkauf & Werkstatt → Rechnung & Steuer* |
| Mahngebühren | *Verkauf & Werkstatt → Mahnwesen* |
| Pauschalen für Kostenvoranschläge, Garantie | *Verkauf & Werkstatt → Annahme & Abholung* |
| Stundensatz, Kilometersatz, Anfahrtspauschale | im Menü **Arbeitskalender → Einstellungen** |

Das Suchfeld oben in den Einstellungen findet jede Einstellung (z. B. „Stundensatz“).

### Für neue Installationen und die EXE: `firma.toml`

Die Datei [`firma.toml`](firma.toml) im Repository ist die **eine zentrale Stelle** für Programmname, Firmendaten,
Farben und Standardwerte. Die Werte werden beim **ersten Start** in die neue, leere Datenbank übernommen; danach gilt,
was in der App gespeichert ist.

Ändern ohne Programmierkenntnisse: auf GitHub die Datei `firma.toml` öffnen → Stift-Symbol (**Edit**) → Werte ändern
→ **Commit changes**. Beträge mit Punkt schreiben (z. B. `95.00`).

### Logo und Programmsymbol austauschen

Eingebaut ist das Logo von Omikron Consulting (Waben + Schriftzug). Quelle ist `bauen/logo_quelle.png`, freigestellt
aus einer kleinen Vorlage (225×69 Pixel, hochskaliert und nachgeschärft). Auf Rechnungen ist es daher etwas weich. Liegt eine **größere Logodatei** vor
(PNG mit transparentem Hintergrund, ab ca. 1500 px Breite, oder SVG als PNG exportiert), sollte sie das Logo
ersetzen. Die drei Waben im Programmsymbol (EXE, Browser-Tab) werden in den Farben aus `firma.toml` → `[farben] marke`
gezeichnet und bleiben in jeder Größe scharf.

So tauschen Sie das Logo aus:

- **Nur auf Rechnungen und im Programm:** in der App *Einstellungen → Layout & Dokumente → Logo* hochladen. Fertig.
- **Auch Anmeldeseite, Browser-Tab und EXE-Symbol:** die Dateien im Ordner `rsb/static/bilder/` ersetzen
  (gleiche Dateinamen):
  - `logo_standard.png` – Logo (breit, transparenter Hintergrund, ca. 1500 px breit)
  - `symbol.png` (128×128), `favicon.png` (32×32), `programm.ico` (Windows-Symbol der EXE)

  Wer Python installiert hat, legt die neue Datei als `bauen/logo_quelle.png` ab und erzeugt alle Dateien auf einmal:
  `python bauen/symbole_erzeugen.py bauen/logo_quelle.png`

---

## 7. Datensicherung

- Das Programm erstellt täglich selbst eine Sicherung (ZIP) im Datenordner. Unter **Einstellungen → Backup** lässt
  sich jederzeit eine Sicherung **herunterladen** – bitte regelmäßig (z. B. monatlich) herunterladen und separat
  aufbewahren (z. B. in einer SharePoint-Dokumentbibliothek).
- Zusätzlich kann Azure den App Service sichern (**Sicherungen** im App Service; Umfang je nach Tarif).
- Wiederherstellen: *Einstellungen → Backup → Sicherung wiederherstellen* (ZIP hochladen).

## 8. Windows-Programm über SharePoint verteilen (ohne Azure)

Wer ohne Azure arbeiten möchte, installiert das Programm auf jedem PC. Verteilt wird es über SharePoint, Updates
holt sich das Programm danach selbst aus diesem GitHub-Repository.

**Ordner für SharePoint:** Jede Veröffentlichung enthält unter *Releases* die Datei
`Omikron-Buchhaltung-SharePoint.zip`. Entpacken und den Ordner **„Omikron Buchhaltung“** in eine
SharePoint-Dokumentbibliothek des Kunden hochladen (z. B. *Dokumente → Software*). Inhalt:

| Datei | Zweck |
|---|---|
| `Installieren.cmd` | Doppelklick: lädt die neueste Version von GitHub (Prüfsumme wird kontrolliert), installiert nach `%LOCALAPPDATA%\Programs\Omikron-Buchhaltung`, legt Verknüpfungen auf Desktop und im Startmenü an, startet das Programm. Ohne Internet wird die EXE aus dem Ordner genommen. Keine Administratorrechte nötig. |
| `Omikron-Buchhaltung.exe` | Programm (Reserve für die Installation ohne Internet) |
| `Deinstallieren.cmd` | entfernt Programm und Verknüpfungen, Daten bleiben erhalten |
| `installieren.ps1`, `deinstallieren.ps1` | die eigentlichen Skripte (werden von den .cmd-Dateien aufgerufen) |
| `Anleitung.pdf` | Anleitung für den Kunden (Installation, Updates, Datensicherung) |

Die Quelldateien liegen im Repository unter `verteilung/sharepoint/` (Anleitung: `anleitung.html`, daraus wird
`Anleitung.pdf` gedruckt).

**Wichtig:**
- Das Programm wird **nicht** direkt aus SharePoint/OneDrive gestartet, sondern lokal installiert. Sonst könnte es
  sich nicht selbst aktualisieren, und die Synchronisierung könnte die Datenbank beschädigen.
- Jeder PC hat einen **eigenen Datenbestand** (`%LOCALAPPDATA%\Omikron-Buchhaltung\Daten`). Für gemeinsame Daten
  im Team ist die Azure-Variante (Abschnitte 2–5) nötig.
- Empfehlung für die Datensicherung: *Einstellungen → Backup → Zusätzlicher Backup-Ordner* auf einen mit
  SharePoint synchronisierten Ordner setzen.

### Neue Version für den Kunden veröffentlichen

1. Änderungen am Programm vornehmen (lassen).
2. In `rsb/__init__.py` die `VERSION_NUMMER` erhöhen (z. B. `1.1.2` → `1.2.0`) und in `docs/AENDERUNGEN.md` einen
   Abschnitt `## 1.2.0 – Datum` mit den Neuerungen ergänzen (erscheint beim Kunden als Update-Hinweis).
3. Auf GitHub hochladen (Push auf den Standard-Branch). GitHub testet automatisch, baut die EXE, prüft die
   Installation und veröffentlicht unter *Releases*: EXE, Prüfsumme und das SharePoint-Paket. Ohne neue
   Versionsnummer wird nur getestet, nichts veröffentlicht. Manuell starten: *Actions → „Windows-EXE bauen und
   veröffentlichen“ → Run workflow*.
4. Beim Kunden: Das Programm findet die neue Version innerhalb von 6 Stunden bzw. beim nächsten Start und
   installiert sie beim nächsten Start selbst (mit Sicherung vorher). Der SharePoint-Ordner muss **nicht** ersetzt
   werden – `Installieren.cmd` lädt ohnehin immer die neueste Version.

Voraussetzung: Dieses Repository bleibt **öffentlich**. Die EXE fragt die Versionen ohne Anmeldung bei GitHub ab;
bei einem privaten Repository findet sie keine Updates mehr. Im Repository stehen keine Zugangsdaten und keine
Kundendaten.

## 9. Wenn etwas nicht klappt

| Problem | Lösung |
|---|---|
| Seite zeigt „Application Error“ | App Service → **Protokollstream** ansehen; Startbefehl `python -m rsb` und `WEBSITES_PORT=8000` prüfen |
| SharePoint zeigt „Einbetten ist nicht zulässig“ | Domain unter HTML-Feldsicherheit freigeben (5a), Schreibweise ohne `https://` |
| Leere graue Fläche im iframe | `RSB_EINBETTEN_ERLAUBT` prüfen (genau `https://KUNDE.sharepoint.com`, ohne `/` am Ende), App neu starten |
| „Ihr Microsoft-Konto ist nicht freigegeben“ | Person in der Unternehmensanwendung zuweisen (4a) bzw. `RSB_ENTRA_ERLAUBT` prüfen |
| Einstellungen nicht erreichbar | Adresse in `RSB_ENTRA_INHABER` eintragen (genau wie bei der Microsoft-Anmeldung) |
| Nach Änderung an Umgebungsvariablen keine Wirkung | App Service → **Neu starten** |
