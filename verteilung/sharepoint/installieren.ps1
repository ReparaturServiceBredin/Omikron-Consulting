# Installiert bzw. aktualisiert die Omikron-Buchhaltung für den angemeldeten Windows-Benutzer.
# Aufruf über "Installieren.cmd" (Doppelklick). Keine Administratorrechte nötig.
#
# - holt die neueste Version direkt von GitHub (mit Prüfsummen-Kontrolle);
#   ohne Internet wird die EXE aus diesem Ordner verwendet
# - Programmordner: %LOCALAPPDATA%\Programs\Omikron-Buchhaltung (nicht in OneDrive/SharePoint, damit sich das
#   Programm später selbst aktualisieren kann)
# - legt Verknüpfungen auf dem Desktop und im Startmenü an und startet das Programm
# - Ihre Daten liegen getrennt davon in %LOCALAPPDATA%\Omikron-Buchhaltung\Daten und bleiben immer erhalten

$ErrorActionPreference = 'Stop'
$Name     = 'Omikron-Buchhaltung'
$Anzeige  = 'Omikron Buchhaltung'
$Repo     = 'ReparaturServiceBredin/Omikron-Consulting'
$Exe      = "$Name.exe"
$Ziel     = Join-Path $env:LOCALAPPDATA "Programs\$Name"
$ZielExe  = Join-Path $Ziel $Exe
$Hier     = Split-Path -Parent $MyInvocation.MyCommand.Path

function Meldung($text, $farbe = 'Gray') { Write-Host $text -ForegroundColor $farbe }

Meldung ''
Meldung "=== $Anzeige installieren ===" 'Cyan'
Meldung ''

# Läuft das Programm? Dann zuerst beenden (sonst kann die Datei nicht ersetzt werden)
$laeuft = Get-Process -Name $Name -ErrorAction SilentlyContinue
if ($laeuft) {
    Meldung 'Das Programm läuft gerade. Es wird für die Installation kurz beendet ...' 'Yellow'
    $laeuft | Stop-Process -Force
    Start-Sleep -Seconds 2
}

New-Item -ItemType Directory -Force -Path $Ziel | Out-Null
$temp = Join-Path $env:TEMP "$Name-neu.exe"
$quelle = $null

# 1) Neueste Version von GitHub
try {
    Meldung 'Lade die neueste Version von GitHub ...'
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    $basis = "https://github.com/$Repo/releases/latest/download"
    $ProgressPreference = 'SilentlyContinue'
    Invoke-WebRequest -Uri "$basis/$Exe" -OutFile $temp -UseBasicParsing
    $sollText = (Invoke-WebRequest -Uri "$basis/$Exe.sha256" -UseBasicParsing).Content
    if ($sollText -is [byte[]]) { $sollText = [Text.Encoding]::ASCII.GetString($sollText) }
    $soll = ($sollText.Trim() -split '\s+')[0].ToLower()
    $ist = (Get-FileHash $temp -Algorithm SHA256).Hash.ToLower()
    if ($soll -ne $ist) { throw 'Prüfsumme stimmt nicht – Download beschädigt.' }
    $quelle = $temp
    Meldung 'Download geprüft (Prüfsumme in Ordnung).' 'Green'
} catch {
    Meldung "GitHub nicht erreichbar oder Download fehlerhaft: $($_.Exception.Message)" 'Yellow'
}

# 2) Sonst die EXE aus diesem Ordner (SharePoint)
if (-not $quelle) {
    $lokal = Join-Path $Hier $Exe
    if (Test-Path $lokal) {
        Meldung 'Verwende die Programmdatei aus diesem Ordner.'
        $quelle = $lokal
    } else {
        Meldung "Keine Programmdatei gefunden. Bitte Internetverbindung prüfen oder $Exe in diesen Ordner legen." 'Red'
        exit 1
    }
}

Copy-Item -Force $quelle $ZielExe
if ($quelle -eq $temp) { Remove-Item -Force $temp -ErrorAction SilentlyContinue }
Unblock-File -Path $ZielExe -ErrorAction SilentlyContinue   # Herkunft „Internet“ entfernen (weniger Windows-Warnungen)

# Verknüpfungen
$shell = New-Object -ComObject WScript.Shell
$orte = @([Environment]::GetFolderPath('Desktop'), [Environment]::GetFolderPath('Programs'))
foreach ($ort in $orte) {
    $lnk = $shell.CreateShortcut((Join-Path $ort "$Anzeige.lnk"))
    $lnk.TargetPath = $ZielExe
    $lnk.WorkingDirectory = $Ziel
    $lnk.IconLocation = "$ZielExe,0"
    $lnk.Description = 'Buchhaltung & Rechnungen'
    $lnk.Save()
}

$version = (Get-Item $ZielExe).VersionInfo.ProductVersion
Meldung ''
Meldung "Fertig! $Anzeige $version ist installiert." 'Green'
Meldung "Programm:  $ZielExe"
Meldung "Daten:     $(Join-Path $env:LOCALAPPDATA "$Name\Daten")"
Meldung 'Verknüpfungen: Desktop und Startmenü. Updates lädt das Programm künftig selbst.'
Meldung ''
Start-Process -FilePath $ZielExe -WorkingDirectory $Ziel
