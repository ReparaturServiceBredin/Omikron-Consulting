#!/usr/bin/env bash
# =====================================================================================================
#  Omikron Buchhaltung – Einrichtung in Microsoft Azure (Browser-Version, Anmeldung mit Microsoft-Konto)
# =====================================================================================================
#  Ausführen im Azure-Portal in der Cloud Shell (Symbol >_ oben, Modus „Bash“):
#
#    curl -fsSL https://raw.githubusercontent.com/ReparaturServiceBredin/Omikron-Consulting/claude/nice-noether-j6v2s5/verteilung/azure/azure-einrichten.sh -o azure-einrichten.sh
#    bash azure-einrichten.sh
#
#  Das Skript fragt alle nötigen Angaben ab und richtet ein:
#    1. Ressourcengruppe, App-Service-Plan (Linux, B1) und Web-App (Python 3.12) in Deutschland
#    2. Einstellungen und Umgebungsvariablen (Datenordner, Port, Anmeldung, SharePoint-Einbettung)
#    3. erste Veröffentlichung des Programms aus GitHub
#    4. Anmeldung mit dem Microsoft-Konto (App-Registrierung, „Zuweisung erforderlich“, Personen freigeben)
#    5. automatische Updates aus GitHub (eigene Identität nur für die Bereitstellung, ohne Passwort)
#  Es kann gefahrlos erneut ausgeführt werden (vorhandene Teile werden übernommen bzw. aktualisiert).
#
#  Rechte: „Besitzer“ auf dem Azure-Abonnement (für Schritt 5 nötig) und „Anwendungsadministrator“ in Entra ID.
#  Von Hand bleibt danach nur: SharePoint (HTML-Feldsicherheit + Seite) und drei Werte in GitHub eintragen –
#  das Skript zeigt am Ende genau an, was wo einzutragen ist.
# =====================================================================================================
# shellcheck disable=SC1111  # deutsche Anführungszeichen in Texten sind gewollt
set -euo pipefail

REPO="ReparaturServiceBredin/Omikron-Consulting"
BRANCH="${BRANCH:-claude/nice-noether-j6v2s5}"
REGION="${REGION:-germanywestcentral}"
SKU="${SKU:-B1}"
LAUFZEIT="PYTHON:3.12"
GRAPH="00000003-0000-0000-c000-000000000000"         # Microsoft Graph
USER_READ="e1fe6dd8-ba31-4d61-89e7-88639da4683d"      # Berechtigung User.Read (Anmelden, Profil lesen)

gruen() { printf '\033[32m%s\033[0m\n' "$*"; }
gelb()  { printf '\033[33m%s\033[0m\n' "$*"; }
rot()   { printf '\033[31m%s\033[0m\n' "$*"; }
titel() { printf '\n\033[1;36m== %s ==\033[0m\n' "$*"; }
frage() { local text="$1" standard="${2:-}" antwort; read -r -p "$text${standard:+ [$standard]}: " antwort; echo "${antwort:-$standard}"; }
WARNUNGEN=()
warnung() { gelb "WARNUNG: $*"; WARNUNGEN+=("$*"); }

# ------------------------------------------------------------------------------------------ Angaben
titel "Angaben"
az account show >/dev/null 2>&1 || az login --use-device-code
ABO_NAME=$(az account show --query name -o tsv); ABO_ID=$(az account show --query id -o tsv)
TENANT=$(az account show --query tenantId -o tsv)
echo "Azure-Abonnement: $ABO_NAME ($ABO_ID)"
if [ "$(frage 'Dieses Abonnement verwenden? (j/n)' j)" != "j" ]; then
  az account list --query "[].{Name:name, Id:id}" -o table
  az account set --subscription "$(frage 'Id des gewünschten Abonnements')"
  ABO_ID=$(az account show --query id -o tsv); TENANT=$(az account show --query tenantId -o tsv)
fi

APP=$(frage "Name der App (nur Kleinbuchstaben, Ziffern, Bindestrich)" "${APP:-omikron-buchhaltung}")
[[ "$APP" =~ ^[a-z0-9][a-z0-9-]{1,40}[a-z0-9]$ ]] || { rot "Ungültiger Name: $APP"; exit 1; }
RG="${RG:-$APP}"
SHAREPOINT=$(frage "SharePoint-Adresse des Kunden – nur der Teil vor .sharepoint.com (z. B. omikronconsulting)" "${SHAREPOINT:-}")
SHAREPOINT="${SHAREPOINT#https://}"; SHAREPOINT="${SHAREPOINT%%.sharepoint.com*}"
[ -n "$SHAREPOINT" ] || { rot "Die SharePoint-Adresse wird gebraucht."; exit 1; }
INHABER=$(frage "E-Mail-Adresse(n) mit ALLEN Rechten (Inhaber), mit Komma getrennt" "${INHABER:-}")
[ -n "$INHABER" ] || { rot "Mindestens eine Inhaber-Adresse wird gebraucht."; exit 1; }
MITARBEITER=$(frage "Weitere Personen mit Zugang (Mitarbeiter), mit Komma getrennt – leer lassen = später" "${MITARBEITER:-}")
ANZEIGE="Omikron Buchhaltung ($APP)"

echo
echo "  App:         $APP  (Ressourcengruppe $RG, Region $REGION, Tarif $SKU)"
echo "  SharePoint:  https://$SHAREPOINT.sharepoint.com"
echo "  Inhaber:     $INHABER"
echo "  Mitarbeiter: ${MITARBEITER:-–}"
[ "$(frage 'Einrichten? (j/n)' j)" = "j" ] || exit 0

# ------------------------------------------------------------------------------------------ 1. Web-App
titel "1/5 Web-App anlegen"
az provider register --namespace Microsoft.Web --wait >/dev/null
az group create -n "$RG" -l "$REGION" -o none
if ! az webapp show -g "$RG" -n "$APP" -o none 2>/dev/null; then
  FREI=$(az rest --method post \
    --uri "https://management.azure.com/subscriptions/$ABO_ID/providers/Microsoft.Web/checknameavailability?api-version=2022-03-01" \
    --body "{\"name\":\"$APP\",\"type\":\"Microsoft.Web/sites\"}" --query nameAvailable -o tsv)
  [ "$FREI" = "true" ] || { rot "Der Name „$APP“ ist bei Azure schon vergeben. Bitte einen anderen wählen (z. B. $APP-$RANDOM)."; exit 1; }
  az appservice plan create -g "$RG" -n "$APP-plan" --is-linux --sku "$SKU" -l "$REGION" -o none
  az webapp create -g "$RG" -n "$APP" -p "$APP-plan" --runtime "$LAUFZEIT" -o none
fi
HOST=$(az webapp show -g "$RG" -n "$APP" --query defaultHostName -o tsv)
WEBAPP_ID=$(az webapp show -g "$RG" -n "$APP" --query id -o tsv)
gruen "Web-App: https://$HOST"

# ------------------------------------------------------------------------------------------ 2. Einstellungen
titel "2/5 Einstellungen"
az webapp config set -g "$RG" -n "$APP" --startup-file "python -m rsb" --always-on true --ftps-state Disabled \
  --http20-enabled true -o none
az webapp update -g "$RG" -n "$APP" --https-only true -o none
az webapp config appsettings set -g "$RG" -n "$APP" -o none --settings \
  RSB_MODUS=server RSB_DATEN=/home/daten RSB_HOST=0.0.0.0 RSB_PORT=8000 WEBSITES_PORT=8000 \
  RSB_HINTER_PROXY=1 RSB_SICHERE_COOKIES=1 RSB_SQLITE_JOURNAL=DELETE RSB_KEIN_UPDATE=1 \
  RSB_ANMELDUNG=entra "RSB_ENTRA_INHABER=$INHABER" "RSB_ENTRA_TENANT_ID=$TENANT" \
  "RSB_EINBETTEN_ERLAUBT=https://$SHAREPOINT.sharepoint.com" \
  SCM_DO_BUILD_DURING_DEPLOYMENT=true WEBSITES_ENABLE_APP_SERVICE_STORAGE=true TZ=Europe/Berlin
gruen "Einstellungen gesetzt (eine Instanz, immer aktiv, nur HTTPS, Daten in /home/daten)."

# ------------------------------------------------------------------------------------------ 3. Programm
titel "3/5 Programm veröffentlichen (dauert 5–10 Minuten)"
ARBEIT=$(mktemp -d)
git clone -q --depth 1 -b "$BRANCH" "https://github.com/$REPO.git" "$ARBEIT/quelle"
( cd "$ARBEIT/quelle" && zip -qr "$ARBEIT/app.zip" rsb firma.toml requirements.txt docs/AENDERUNGEN.md -x '*/__pycache__/*' )
VERSION=$(sed -n 's/^VERSION_NUMMER = "\(.*\)"/\1/p' "$ARBEIT/quelle/rsb/__init__.py")
az webapp deploy -g "$RG" -n "$APP" --src-path "$ARBEIT/app.zip" --type zip --timeout 900000 -o none \
  || warnung "Die Veröffentlichung meldete einen Fehler – Details: Web-App → Bereitstellungscenter → Protokolle."
printf 'Warte auf den Start '
OK=""
for _ in $(seq 1 60); do
  if curl -fsS --max-time 8 "https://$HOST/version" 2>/dev/null | grep -q "\"$VERSION\""; then OK=1; break; fi
  printf '.'; sleep 10
done
echo
if [ -n "$OK" ]; then gruen "Programm läuft: Version $VERSION"; else
  warnung "Programm antwortet noch nicht. Bitte in einigen Minuten https://$HOST/version öffnen; Fehler stehen unter Web-App → Protokollstream."
fi

# ------------------------------------------------------------------------------------------ 4. Anmeldung
titel "4/5 Anmeldung mit dem Microsoft-Konto"
CALLBACK="https://$HOST/.auth/login/aad/callback"
APP_ID=$(az ad app list --display-name "$ANZEIGE" --query "[0].appId" -o tsv)
if [ -z "$APP_ID" ]; then
  APP_ID=$(az ad app create --display-name "$ANZEIGE" --sign-in-audience AzureADMyOrg \
    --web-redirect-uris "$CALLBACK" --enable-id-token-issuance true --query appId -o tsv)
else
  az ad app update --id "$APP_ID" --web-redirect-uris "$CALLBACK" --enable-id-token-issuance true
fi
az ad app permission add --id "$APP_ID" --api "$GRAPH" --api-permissions "$USER_READ=Scope" -o none 2>/dev/null || true
az ad app permission admin-consent --id "$APP_ID" 2>/dev/null \
  || warnung "Administrator-Zustimmung nicht möglich – beim ersten Anmelden fragt Microsoft ggf. nach Zustimmung (Entra → App-Registrierungen → $ANZEIGE → API-Berechtigungen → Zustimmung erteilen)."
GEHEIM=$(az ad app credential reset --id "$APP_ID" --display-name "Azure App Service Anmeldung" --years 2 --append \
  --query password -o tsv)
az webapp config appsettings set -g "$RG" -n "$APP" -o none --settings "MICROSOFT_PROVIDER_AUTHENTICATION_SECRET=$GEHEIM"
unset GEHEIM
# Wichtig: nicht angemeldete Aufrufe ZULASSEN – das Programm prüft selbst und zeigt im SharePoint-iframe
# eine Anmeldung per Popup (die Microsoft-Seite darf nicht in einem iframe laufen).
az webapp auth update -g "$RG" -n "$APP" --enabled true --unauthenticated-client-action AllowAnonymous \
  --enable-token-store true -o none
az webapp auth microsoft update -g "$RG" -n "$APP" --client-id "$APP_ID" \
  --client-secret-setting-name MICROSOFT_PROVIDER_AUTHENTICATION_SECRET \
  --issuer "https://login.microsoftonline.com/$TENANT/v2.0" --yes -o none
SP_ID=$(az ad sp show --id "$APP_ID" --query id -o tsv 2>/dev/null || az ad sp create --id "$APP_ID" --query id -o tsv)
az ad sp update --id "$SP_ID" --set appRoleAssignmentRequired=true
for MAIL in $(echo "$INHABER,$MITARBEITER" | tr ',;' '  '); do
  UID_=$(az ad user show --id "$MAIL" --query id -o tsv 2>/dev/null || true)
  if [ -z "$UID_" ]; then
    UID_=$(az ad user list --filter "mail eq '$MAIL'" --query "[0].id" -o tsv 2>/dev/null || true)
  fi
  if [ -z "$UID_" ]; then warnung "Person $MAIL nicht im Verzeichnis gefunden – bitte von Hand zuweisen (Entra → Unternehmensanwendungen → $ANZEIGE → Benutzer und Gruppen)."; continue; fi
  az rest --method post --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignedTo" \
    --body "{\"principalId\":\"$UID_\",\"resourceId\":\"$SP_ID\",\"appRoleId\":\"00000000-0000-0000-0000-000000000000\"}" \
    -o none 2>/dev/null && echo "  Zugang freigegeben: $MAIL" || echo "  Zugang bestand bereits: $MAIL"
done
gruen "Anmeldung eingerichtet: nur zugewiesene Personen aus Ihrem Microsoft 365 kommen hinein."

# ------------------------------------------------------------------------------------------ 5. Updates
titel "5/5 Automatische Updates aus GitHub"
DEP_NAME="$APP GitHub-Bereitstellung"
DEP_ID=$(az ad app list --display-name "$DEP_NAME" --query "[0].appId" -o tsv)
[ -n "$DEP_ID" ] || DEP_ID=$(az ad app create --display-name "$DEP_NAME" --sign-in-audience AzureADMyOrg --query appId -o tsv)
DEP_SP=$(az ad sp show --id "$DEP_ID" --query id -o tsv 2>/dev/null || az ad sp create --id "$DEP_ID" --query id -o tsv)
if ! az ad app federated-credential list --id "$DEP_ID" --query "[?name=='github-branch']" -o tsv | grep -q .; then
  az ad app federated-credential create --id "$DEP_ID" -o none --parameters "{\"name\":\"github-branch\",
    \"issuer\":\"https://token.actions.githubusercontent.com\",
    \"subject\":\"repo:$REPO:ref:refs/heads/$BRANCH\",\"audiences\":[\"api://AzureADTokenExchange\"]}"
fi
# darf nur diese eine Web-App aktualisieren
az role assignment create --assignee-object-id "$DEP_SP" --assignee-principal-type ServicePrincipal \
  --role "Website Contributor" --scope "$WEBAPP_ID" -o none 2>/dev/null \
  || warnung "Rolle konnte nicht vergeben werden (Rechte „Besitzer“ nötig): Web-App → Zugriffssteuerung (IAM) → Rollenzuweisung „Website-Mitwirkender“ für „$DEP_NAME“."
rm -rf "$ARBEIT"

# ------------------------------------------------------------------------------------------ Ergebnis
titel "Fertig"
cat <<EOF

Programm:   https://$HOST
Anmelden:   Adresse öffnen → „Mit Microsoft anmelden“ → als Inhaber unter Einstellungen die Firmendaten eintragen.

NOCH VON HAND (ca. 10 Minuten):

A) GitHub – automatische Updates einschalten
   github.com/$REPO → Settings → Secrets and variables → Actions → Reiter „Variables“ → „New repository variable“:
     AZURE_CLIENT_ID        = $DEP_ID
     AZURE_TENANT_ID        = $TENANT
     AZURE_SUBSCRIPTION_ID  = $ABO_ID
     AZURE_WEBAPP_NAME      = $APP
     AZURE_WEBAPP_HOST      = $HOST
   (Keine Geheimnisse – GitHub meldet sich ohne Passwort bei Azure an.) Danach geht jede neue Programmversion
   automatisch auch auf diese Web-App.

B) SharePoint – Einbetten erlauben (Websitesammlungs-Administrator)
   Website öffnen → Zahnrad → Websiteinformationen → Alle Websiteeinstellungen anzeigen
   → Websitesammlungsverwaltung → HTML-Feldsicherheit → Domäne hinzufügen:
     $HOST

C) SharePoint – Seite anlegen
   Neu → Seite → Abschnitt mit voller Breite → + → „Einbetten“ → einfügen:
     <iframe src="https://$HOST/" width="100%" height="900" style="border:0"></iframe>
   → Veröffentlichen. Tipp: zusätzlich eine Schaltfläche „Im eigenen Fenster öffnen“ mit https://$HOST

D) Weitere Personen freigeben
   entra.microsoft.com → Unternehmensanwendungen → „$ANZEIGE“ → Benutzer und Gruppen → Benutzer hinzufügen.

Hinweis: Das Anmelde-Geheimnis der App gilt 2 Jahre. Zum Verlängern dieses Skript erneut ausführen.
EOF
if [ ${#WARNUNGEN[@]} -gt 0 ]; then
  echo; gelb "Bitte prüfen:"; for w in "${WARNUNGEN[@]}"; do gelb "  - $w"; done
fi
