"""Neuinstallation: zentrale Konfiguration, leerer Start, Microsoft-Anmeldung (Entra) und Einbetten in SharePoint."""
import base64
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from rsb import create_app, datenort, marke
from rsb import db as dbm

WURZEL = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------- firma.toml

def test_mitgelieferte_firma_toml_ist_gueltig_und_ohne_firmendaten(monkeypatch):
    """Die echte firma.toml lässt sich lesen; Bank-/Steuerdaten sind leer (trägt der Kunde selbst ein)."""
    monkeypatch.setenv("RSB_FIRMA_DATEI", str(WURZEL / "firma.toml"))
    marke.laden.cache_clear()
    try:
        cfg = marke.laden()
        werte = marke.einstellungen()
        assert cfg["programm"]["kurzname"] and " " not in cfg["programm"]["kurzname"]
        assert werte["firma_name"]
        for feld in ("iban", "bic", "steuernummer", "ust_idnr", "strasse", "telefon"):
            assert werte[feld] == "", feld
        assert werte["absender_name"] == werte["firma_name"]
        assert isinstance(werte["ak_stundensatz"], int)
    finally:
        marke.laden.cache_clear()


def test_standardwerte_werden_umgerechnet(tmp_path, monkeypatch):
    datei = tmp_path / "firma.toml"
    datei.write_text('[programm]\nname = "X"\nkurzname = "X"\n[firma]\nfirma_name = "Beispiel AG"\n'
                     '[standardwerte]\nstundensatz_euro = 95.5\nkm_satz_euro = 0.3\nmwst_satz = 7\n'
                     '[einstellungen]\npraefix_rechnung = "R"\n', encoding="utf-8")
    monkeypatch.setenv("RSB_FIRMA_DATEI", str(datei))
    marke.laden.cache_clear()
    try:
        w = marke.einstellungen()
        assert (w["ak_stundensatz"], w["ak_km_satz"], w["regel_steuersatz"]) == (9550, 30, 7)
        assert w["praefix_rechnung"] == "R" and w["firma_name"] == "Beispiel AG"
        datei.write_text('[standardwerte]\ntippfehler = 1\n', encoding="utf-8")
        marke.laden.cache_clear()
        with pytest.raises(ValueError, match="tippfehler"):
            marke.einstellungen()
    finally:
        marke.laden.cache_clear()


# ---------------------------------------------------------------------- leerer Start

def test_neue_datenbank_ist_leer(tmp_path):
    app = create_app(tmp_path / "Daten", testing=True)
    con = dbm.verbinden(app.config["DB_PFAD"])
    try:
        for tabelle in ("kunden", "dokumente", "auftraege", "vertragsarten",
                        "anfragen", "lieferanten", "benutzer", "kassenbuch"):
            assert con.execute(f"SELECT COUNT(*) FROM {tabelle}").fetchone()[0] == 0, tabelle
    finally:
        con.close()


def test_keine_alten_datenordner_ohne_ausdruecklichen_wunsch(tmp_path, monkeypatch):
    """Eine Neuinstallation übernimmt nie selbständig Daten, die schon auf dem Rechner liegen."""
    monkeypatch.delenv("RSB_DATEN", raising=False)
    monkeypatch.delenv("RSB_ALTE_DATEN_SUCHEN", raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "AppData"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "AppData"))
    monkeypatch.setattr(datenort, "kandidaten", lambda *a, **k: pytest.fail("darf nicht suchen"))
    assert datenort.ermitteln() == datenort.fester_ort()


def test_keine_daten_des_vorbetreibers_im_projekt():
    """Schutz vor Rückfällen: keine Namen, Orte oder Adressen der Vorlage im Projekt."""
    verboten = re.compile(r"bredin|möckmühl|moeckmuehl|kochend(ö|oe)rfer|9879253", re.I)
    dateien = subprocess.run(["git", "ls-files"], cwd=WURZEL, capture_output=True, text=True).stdout.split()
    if not dateien:  # außerhalb von git (z. B. entpacktes Archiv)
        dateien = [str(p.relative_to(WURZEL)) for p in WURZEL.rglob("*") if p.is_file() and ".git" not in p.parts]
    treffer = []
    for name in dateien:
        pfad = WURZEL / name
        if pfad.suffix in (".png", ".ico", ".ttf", ".pdf") or not pfad.is_file() or name.endswith(Path(__file__).name):
            continue
        # Ausnahme: Adresse dieses Repositorys (Quelle für Updates und Downloads)
        text = pfad.read_text(encoding="utf-8", errors="ignore").replace("ReparaturServiceBredin/Omikron-Consulting", "")
        if verboten.search(text):
            treffer.append(name)
    assert treffer == []


# ---------------------------------------------------------------------- Microsoft-Anmeldung (Entra)

def _kopf(email="anna@example.com", rollen=(), tid="t-1"):
    claims = [{"typ": "name", "val": "Anna Beispiel"}, {"typ": "tid", "val": tid}]
    claims += [{"typ": "roles", "val": r} for r in rollen]
    roh = base64.b64encode(json.dumps({"auth_typ": "aad", "claims": claims}).encode()).decode()
    return {"X-MS-CLIENT-PRINCIPAL-NAME": email, "X-MS-CLIENT-PRINCIPAL-IDP": "aad", "X-MS-CLIENT-PRINCIPAL": roh}


@pytest.fixture
def entra_app(tmp_path, monkeypatch):
    monkeypatch.setenv("RSB_ANMELDUNG", "entra")
    monkeypatch.setenv("RSB_MODUS", "server")
    monkeypatch.setenv("RSB_ENTRA_INHABER", "chef@example.com")
    monkeypatch.setenv("RSB_EINBETTEN_ERLAUBT", "https://kunde.sharepoint.com")
    return create_app(tmp_path / "Daten", testing=True)


def test_entra_ohne_anmeldung_zur_anmeldeseite(entra_app):
    c = entra_app.test_client()
    r = c.get("/kunden")
    assert r.status_code == 302 and "/login" in r.headers["Location"]
    seite = c.get(r.headers["Location"]).get_data(as_text=True)
    assert "Mit Microsoft anmelden" in seite and "/.auth/login/aad?post_login_redirect_uri=%2Fkunden" in seite
    assert "neuem Tab" in seite  # Ausweg, falls die Anmeldung im iframe nicht klappt
    assert c.post("/kunden/neu", data={}).status_code == 401
    assert c.get("/einrichten").status_code == 302  # kein Passwort-Einrichten im Entra-Modus


def test_entra_mitarbeiter_und_inhaber(entra_app):
    c = entra_app.test_client()
    assert c.get("/kunden", headers=_kopf()).status_code == 200
    assert c.get("/einstellungen/firma", headers=_kopf()).status_code == 403  # Mitarbeiter
    assert c.get("/einstellungen/firma", headers=_kopf("chef@example.com")).status_code == 200
    assert c.get("/einstellungen/firma", headers=_kopf("x@example.com", rollen=["Inhaber"])).status_code == 200


def test_entra_freigabeliste_und_tenant(entra_app, monkeypatch):
    c = entra_app.test_client()
    monkeypatch.setenv("RSB_ENTRA_ERLAUBT", "@firma.example")
    assert c.get("/kunden", headers=_kopf("fremd@example.com")).status_code == 403
    assert c.get("/kunden", headers=_kopf("ok@firma.example")).status_code == 200
    monkeypatch.setenv("RSB_ENTRA_TENANT_ID", "T-1")
    assert c.get("/kunden", headers=_kopf("ok@firma.example", tid="anderer")).status_code == 403
    assert c.get("/kunden", headers=_kopf("ok@firma.example", tid="t-1")).status_code == 200


def test_entra_kopfzeilen_ohne_entra_modus_wirkungslos(tmp_path, monkeypatch):
    monkeypatch.setenv("RSB_MODUS", "server")
    app = create_app(tmp_path / "Daten", testing=True)
    r = app.test_client().get("/kunden", headers=_kopf("chef@example.com"))
    assert r.status_code in (302, 403)  # Passwort-Anmeldung nötig, die Kopfzeilen zählen nicht


def test_iframe_uebergabe_per_einmalcode(entra_app):
    popup = entra_app.test_client()
    seite = popup.get("/anmeldung/fertig", headers=_kopf("chef@example.com")).get_data(as_text=True)
    code = re.search(r'id="anmeldecode" value="([^"]+)"', seite).group(1)
    iframe = entra_app.test_client()  # eigene Cookies wie ein iframe ohne Azure-Cookie
    assert iframe.get("/kunden").status_code == 302
    r = iframe.post("/anmeldung/uebernehmen", data={"code": code})
    assert r.status_code == 200 and r.get_json() == {"ok": True}
    assert "SameSite=None" in r.headers["Set-Cookie"] and "Secure" in r.headers["Set-Cookie"]
    assert "Partitioned" in r.headers["Set-Cookie"]
    assert iframe.get("/kunden").status_code == 200
    assert iframe.get("/einstellungen/firma").status_code == 200  # Rolle Inhaber übernommen
    # Code nur einmal verwendbar, gefälschte Codes werden abgelehnt
    assert entra_app.test_client().post("/anmeldung/uebernehmen", data={"code": code}).status_code == 403
    assert entra_app.test_client().post("/anmeldung/uebernehmen", data={"code": "abc"}).status_code == 403


def test_abmelden_im_entra_modus(entra_app):
    c = entra_app.test_client()
    c.get("/kunden", headers=_kopf())
    with c.session_transaction() as s:
        token = s["csrf"]
    r = c.post("/abmelden", data={"csrf": token}, headers=_kopf())
    assert r.status_code == 302 and r.headers["Location"].startswith("/.auth/logout")


# ---------------------------------------------------------------------- Einbetten

def test_einbetten_nur_von_sharepoint(entra_app, tmp_path, monkeypatch):
    r = entra_app.test_client().get("/version")
    assert r.headers["Content-Security-Policy"] == "frame-ancestors 'self' https://kunde.sharepoint.com"
    assert "X-Frame-Options" not in r.headers
    monkeypatch.delenv("RSB_EINBETTEN_ERLAUBT")
    r = create_app(tmp_path / "Daten2", testing=True).test_client().get("/version")
    assert r.headers["X-Frame-Options"] == "SAMEORIGIN"
    assert r.headers["Content-Security-Policy"] == "frame-ancestors 'self'"


def test_sqlite_journal_einstellbar(tmp_path, monkeypatch):
    monkeypatch.setenv("RSB_SQLITE_JOURNAL", "DELETE")
    con = dbm.verbinden(str(tmp_path / "x.db"))
    try:
        assert con.execute("PRAGMA journal_mode").fetchone()[0] == "delete"
    finally:
        con.close()


# ---------------------------------------------------------------------- Mac-App

def test_mac_app_kein_selbstaustausch_und_eigener_datenordner(tmp_path, monkeypatch):
    import sys
    from rsb import update
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    assert update.ist_mac_app() and not update.ist_exe()  # Mac: nur Hinweis, kein Austausch der Windows-EXE
    assert update.download_seite().endswith("/releases/latest")
    monkeypatch.setattr(datenort.os, "name", "posix")
    monkeypatch.setattr(datenort.Path, "home", classmethod(lambda cls: tmp_path))
    assert datenort.fester_ort() == tmp_path / "Library" / "Application Support" / marke.kurzname() / "Daten"
    monkeypatch.setattr(sys, "platform", "win32")
    assert update.ist_exe() and not update.ist_mac_app()


def test_mac_hinweis_in_den_einstellungen(tmp_path, monkeypatch):
    import sys
    app = create_app(tmp_path / "Daten", testing=True)
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "platform", "darwin")
    seite = app.test_client().get("/einstellungen/programm").get_data(as_text=True)
    assert "Mac-Version:" in seite and "/releases/latest" in seite and "Jetzt aktualisieren" not in seite
