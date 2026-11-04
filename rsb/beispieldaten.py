"""Legt Beispieldaten zum Ausprobieren an: python -m rsb.beispieldaten

Nur für einen leeren Test-Datenordner gedacht (z. B. RSB_DATEN=Testdaten)!
"""
import sys

from . import create_app
from . import db as dbm
from .logik import naechste_kundennr, summen_speichern

# Nur erfundene Platzhalter – keine echten Personen oder Firmen
KUNDEN = [
    dict(typ="privat", anrede="Frau", vorname="Erika", nachname="Musterfrau", strasse="Musterweg 1", plz="12345",
         ort="Musterstadt", email="erika@example.com", telefon="0000 000000"),
    dict(typ="firma", firma="Musterkunde GmbH", anrede="Herr", vorname="Max", nachname="Mustermann",
         strasse="Beispielstraße 2", plz="12345", ort="Musterstadt", email="max@example.com",
         telefon="0000 000001", notizen="Beispielkunde zum Ausprobieren"),
    dict(typ="privat", anrede="Herr", vorname="John", nachname="Doe", strasse="Testallee 3", plz="12345",
         ort="Musterstadt", email="john.doe@example.org"),
]

ARTIKEL = [
    ("Beratung", "Beispielleistung je Stunde", "Beratung", "leistung", "Std.", 10000, 0, None),
    ("Workshop (halber Tag)", "Beispielleistung pauschal", "Schulung", "leistung", "pauschal", 50000, 0, None),
    ("Projektpauschale", "Beispielleistung", "Projekt", "leistung", "pauschal", 100000, 0, None),
    ("Beispielmaterial", "", "Sonstiges", "material", "Stk.", 1000, 500, 100),
]


def main():
    app = create_app()
    with app.app_context():
        con = dbm.get_db()
        if con.execute("SELECT 1 FROM kunden LIMIT 1").fetchone():
            print("Es sind bereits Kunden vorhanden – Beispieldaten werden nicht angelegt.")
            sys.exit(1)
        with dbm.Transaktion(con):
            dbm.einstellungen_speichern({
                "strasse": "Musterstraße 1", "plz": "12345", "telefon": "0151 00000000",
                "steuernummer": "00/000/00000 (Beispiel)", "bank_name": "Beispielbank",
                "iban": "DE02120300000000202051", "bic": "BYLADEM1001",
            }, con)
            einst = dbm.einstellungen(con)
            for k in KUNDEN:
                felder = {"land": "Deutschland", **k}
                con.execute(
                    f"INSERT INTO kunden (kundennr, {', '.join(felder)}, erstellt_am, geaendert_am) "
                    f"VALUES (?, {', '.join('?' * len(felder))}, ?, ?)",
                    [naechste_kundennr(con, einst), *felder.values(), dbm.jetzt(), dbm.jetzt()])
            for name, beschr, art, typ, einheit, preis, teile, aufschlag in ARTIKEL:
                con.execute(
                    "INSERT INTO artikel (name, beschreibung, leistungsart, typ, einheit, preis, teilekosten, "
                    "aufschlag_prozent, steuersatz, aktiv, erstellt_am, geaendert_am) VALUES (?,?,?,?,?,?,?,?,19,1,?,?)",
                    (name, beschr, art, typ, einheit, preis, teile, aufschlag, dbm.jetzt(), dbm.jetzt()))
            dbm.protokollieren("beispieldaten_angelegt", "system", con=con)
        print(f"Beispieldaten angelegt: {len(KUNDEN)} Kunden, {len(ARTIKEL)} Leistungen/Artikel.")


if __name__ == "__main__":
    main()
