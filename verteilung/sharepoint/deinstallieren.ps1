# Entfernt das Programm und die Verknüpfungen. Die DATEN bleiben erhalten
# (%LOCALAPPDATA%\Omikron-Buchhaltung\Daten) – sie werden nur gelöscht, wenn Sie das ausdrücklich bestätigen.

$Name    = 'Omikron-Buchhaltung'
$Anzeige = 'Omikron Buchhaltung'
$Ziel    = Join-Path $env:LOCALAPPDATA "Programs\$Name"
$Daten   = Join-Path $env:LOCALAPPDATA "$Name\Daten"

Write-Host ''
Write-Host "=== $Anzeige entfernen ===" -ForegroundColor Cyan
Get-Process -Name $Name -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 2

foreach ($lnk in @((Join-Path ([Environment]::GetFolderPath('Desktop')) "$Anzeige.lnk"),
                   (Join-Path ([Environment]::GetFolderPath('Programs')) "$Anzeige.lnk"))) {
    if (Test-Path $lnk) { Remove-Item -Force $lnk }
}
if (Test-Path $Ziel) { Remove-Item -Recurse -Force $Ziel }
Write-Host 'Programm und Verknüpfungen entfernt.' -ForegroundColor Green
Write-Host ''
Write-Host "Ihre Daten liegen weiterhin in: $Daten"
Write-Host 'Bei einer erneuten Installation sind sie automatisch wieder da.'
Write-Host ''
$antwort = Read-Host 'Sollen die DATEN ebenfalls endgültig gelöscht werden? Dann bitte LOESCHEN eintippen (sonst Enter)'
if ($antwort -eq 'LOESCHEN') {
    Remove-Item -Recurse -Force (Split-Path $Daten -Parent)
    Write-Host 'Daten gelöscht.' -ForegroundColor Yellow
} else {
    Write-Host 'Daten bleiben erhalten.'
}
