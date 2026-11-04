"""Erzeugt Logo und Programmsymbole aus den Angaben in firma.toml.

Aufruf (im Projektordner):   python bauen/symbole_erzeugen.py
  - ohne eigenes Logo: zeichnet ein schlichtes Platzhalter-Logo (Buchstabe Omikron „ο“ + Firmenname)
  - mit eigenem Logo:  python bauen/symbole_erzeugen.py pfad/zum/logo.png [pfad/zur/bildmarke.png]
    (die Bildmarke ist das quadratische Zeichen für EXE-Symbol und Browser-Tab; ohne Angabe wird das Logo verwendet)

Ergebnis (wird vom Programm, der EXE und den PDFs benutzt):
  rsb/static/bilder/logo_standard.png   Logo auf Rechnungen und Anmeldeseite
  rsb/static/bilder/symbol.png          Symbol neben der Uhr (128 px)
  rsb/static/bilder/favicon.png         Symbol im Browser-Tab (32 px)
  rsb/static/bilder/programm.ico        Symbol der EXE-Datei (16–256 px)
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WURZEL = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WURZEL))
from rsb import marke  # noqa: E402

BILDER = WURZEL / "rsb" / "static" / "bilder"
FONTS = WURZEL / "rsb" / "static" / "fonts"


def _farbe(hexwert):
    h = hexwert.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def bildmarke(groesse, farbe):
    """Quadratisches Zeichen: kräftiger Kreis – der griechische Buchstabe Omikron „ο“."""
    f = 4  # überabtasten für glatte Kanten
    s = groesse * f
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    rand = int(s * 0.08)
    staerke = int(s * 0.17)
    d.ellipse([rand, rand, s - rand, s - rand], outline=farbe, width=staerke)
    return img.resize((groesse, groesse), Image.LANCZOS)


def platzhalter_logo(name, zusatz, farbe, farbe2):
    breite, hoehe = 1800, 520
    img = Image.new("RGBA", (breite, hoehe), (255, 255, 255, 0))
    zeichen = bildmarke(400, farbe)
    img.alpha_composite(zeichen, (40, 60))
    d = ImageDraw.Draw(img)
    schrift = ImageFont.truetype(str(FONTS / "Montserrat-Bold.ttf"), 150)
    klein = ImageFont.truetype(str(FONTS / "Montserrat-Regular.ttf"), 70)
    teile = name.upper().split(" ", 1)
    d.text((500, 95), teile[0], font=schrift, fill=farbe)
    if len(teile) > 1:
        d.text((500, 255), teile[1], font=klein, fill=farbe2)
    if zusatz:
        d.text((500, 360), zusatz, font=ImageFont.truetype(str(FONTS / "Montserrat-Regular.ttf"), 44), fill=farbe2)
    box = img.getbbox()
    return img.crop((0, max(box[1] - 30, 0), box[2] + 40, min(box[3] + 30, hoehe)))


def quadratisch(img):
    s = max(img.size)
    q = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    q.alpha_composite(img.convert("RGBA"), ((s - img.width) // 2, (s - img.height) // 2))
    return q


def main():
    cfg = marke.laden()
    farbe = _farbe(cfg["farben"]["primaer"])
    farbe2 = _farbe(cfg["farben"]["sekundaer"])
    if len(sys.argv) > 1:
        logo = Image.open(sys.argv[1]).convert("RGBA")
        zeichen = quadratisch(Image.open(sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]).convert("RGBA"))
    else:
        firma = cfg["firma"]
        logo = platzhalter_logo(firma.get("firma_name") or cfg["programm"]["name"], firma.get("firma_zusatz", ""),
                                farbe, farbe2)
        zeichen = bildmarke(256, farbe)
    logo.save(BILDER / "logo_standard.png")
    zeichen.resize((128, 128), Image.LANCZOS).save(BILDER / "symbol.png")
    zeichen.resize((32, 32), Image.LANCZOS).save(BILDER / "favicon.png")
    zeichen.resize((256, 256), Image.LANCZOS).save(
        BILDER / "programm.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Logo und Symbole erzeugt in", BILDER)


if __name__ == "__main__":
    main()
