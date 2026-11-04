"""Anmeldung mit dem Microsoft-Konto (Microsoft Entra ID) über die Authentifizierung von Azure App Service.

Einschalten mit `RSB_ANMELDUNG=entra` – NUR beim Betrieb auf Azure App Service mit eingeschalteter
„Authentifizierung“ (Easy Auth, Identitätsanbieter Microsoft). Azure prüft dann die Anmeldung und reicht das Ergebnis
in den Kopfzeilen `X-MS-CLIENT-PRINCIPAL*` an das Programm weiter; Kopfzeilen mit diesem Namen, die ein Browser
selbst schickt, entfernt Azure vorher. Ohne Azure davor dürfen diese Kopfzeilen NICHT vertraut werden – deshalb ist
der Modus standardmäßig aus.

Einbettung in SharePoint (iframe): Die Microsoft-Anmeldeseite lässt sich nicht in einem iframe anzeigen, und Browser
geben Cookies in eingebetteten Seiten oft nicht weiter. Darum:
  1. Im iframe zeigt die Anmeldeseite einen Knopf, der die Anmeldung in einem Popup-Fenster öffnet.
  2. Nach der Anmeldung erzeugt das Popup einen kurzlebigen, signierten Einmal-Code (`/anmeldung/fertig`).
  3. Das iframe holt den Code ab und tauscht ihn gegen eine eigene Sitzung (`/anmeldung/uebernehmen`); das
     Sitzungs-Cookie ist `SameSite=None; Secure; Partitioned` und funktioniert so auch im iframe.
  Klappt das im Browser nicht (z. B. sehr strenge Datenschutz-Einstellungen), bietet die Seite „In neuem Tab öffnen“.

Rollen: `RSB_ENTRA_INHABER` (E-Mail-Adressen, mit Komma getrennt) bzw. die App-Rolle „Inhaber“ in Entra ergeben die
Rolle Inhaber (alle Rechte), alle anderen angemeldeten Personen sind Mitarbeiter. Optional begrenzt
`RSB_ENTRA_ERLAUBT` den Zugang zusätzlich auf bestimmte Adressen oder Domains (z. B. `@omikronconsulting.de`).
"""
import base64
import json
import os
import threading
import time

from flask import current_app, request
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

CODE_GUELTIG_SEK = 120
_benutzte_codes = {}
_sperre = threading.Lock()


def aktiv():
    return (os.environ.get("RSB_ANMELDUNG") or "").strip().lower() == "entra"


def _liste(name):
    return [x.strip().lower() for x in (os.environ.get(name) or "").replace(";", ",").split(",") if x.strip()]


def login_url(ziel="/"):
    """Adresse der Microsoft-Anmeldung von Azure App Service (mit Rücksprung auf `ziel`)."""
    from urllib.parse import quote
    return f"/.auth/login/aad?post_login_redirect_uri={quote(ziel, safe='')}"


def logout_url():
    return "/.auth/logout?post_logout_redirect_uri=/"


def _claims():
    roh = request.headers.get("X-MS-CLIENT-PRINCIPAL")
    if not roh:
        return {}
    try:
        daten = json.loads(base64.b64decode(roh + "=" * (-len(roh) % 4)))
    except (ValueError, TypeError):
        return {}
    claims = {}
    for c in daten.get("claims") or []:
        typ, wert = c.get("typ"), c.get("val")
        if typ and wert is not None:
            claims.setdefault(typ, []).append(wert)
    return claims


def person():
    """Angemeldete Person aus den Azure-Kopfzeilen: {email, name, rolle} oder None."""
    if not aktiv():
        return None
    name = (request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME") or "").strip()
    idp = (request.headers.get("X-MS-CLIENT-PRINCIPAL-IDP") or "").strip().lower()
    if not name or idp not in ("aad", "azureactivedirectory"):
        return None
    claims = _claims()
    tenant = (os.environ.get("RSB_ENTRA_TENANT_ID") or "").strip().lower()
    if tenant:
        tid = [t.lower() for t in claims.get("http://schemas.microsoft.com/identity/claims/tenantid", [])
               + claims.get("tid", [])]
        if tenant not in tid:
            return None
    email = name.lower()
    anzeige = (claims.get("name") or [name])[0]
    rollen = {r.lower() for r in claims.get("roles", [])
              + claims.get("http://schemas.microsoft.com/ws/2008/06/identity/claims/role", [])}
    return {"email": email, "name": anzeige, "rolle": rolle_fuer(email, rollen)}


def rolle_fuer(email, rollen=()):
    if email in _liste("RSB_ENTRA_INHABER") or "inhaber" in rollen:
        return "inhaber"
    return "mitarbeiter"


def erlaubt(email):
    """Zusätzliche Freigabeliste (leer = alle, die Azure/Entra durchlässt)."""
    liste = _liste("RSB_ENTRA_ERLAUBT")
    if not liste:
        return True
    email = (email or "").lower()
    return any(email == e or (e.startswith("@") and email.endswith(e)) for e in liste)


# ---------------------------------------------------------------------- Einmal-Code für das iframe

def _serializer():
    return URLSafeTimedSerializer(current_app.config["SECRET_KEY"], salt="entra-iframe-uebergabe")


def code_erzeugen(p):
    return _serializer().dumps({"email": p["email"], "name": p["name"], "rolle": p["rolle"],
                                "n": base64.urlsafe_b64encode(os.urandom(9)).decode()})


def code_einloesen(code):
    """Prüft den Code (Signatur, Alter, nur einmal verwendbar). Gibt die Person zurück oder None."""
    try:
        p = _serializer().loads(code or "", max_age=CODE_GUELTIG_SEK)
    except (BadSignature, SignatureExpired):
        return None
    jetzt = time.monotonic()
    with _sperre:
        for k in [k for k, t in _benutzte_codes.items() if jetzt - t > CODE_GUELTIG_SEK * 2]:
            del _benutzte_codes[k]
        if code in _benutzte_codes:
            return None
        _benutzte_codes[code] = jetzt
    return p


# ---------------------------------------------------------------------- Einbetten (SharePoint)

def einbetten_erlaubt():
    """Herkünfte, die das Programm im iframe zeigen dürfen, z. B. https://omikron.sharepoint.com"""
    return [x.rstrip("/") for x in (os.environ.get("RSB_EINBETTEN_ERLAUBT") or "").replace(",", " ").split()
            if x.startswith(("https://", "http://localhost", "http://127.0.0.1"))]  # http nur für lokale Tests
