"""Erzeugt Logo und Programmsymbole aus den Angaben in firma.toml.

Aufruf (im Projektordner):   python bauen/symbole_erzeugen.py
  - mit Logo (Normalfall):  python bauen/symbole_erzeugen.py bauen/logo_quelle.png [pfad/zur/bildmarke.png]
    Die Bildmarke ist das quadratische Zeichen für EXE-Symbol und Browser-Tab. Ohne Angabe werden drei
    Waben-Sechsecke in den Farben aus firma.toml → [farben] marke gezeichnet (scharf in jeder Größe).
  - ohne Logo: zeichnet ein schlichtes Platzhalter-Logo mit dem Firmennamen

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


def bildmarke(groesse, farben):
    """Quadratisches Zeichen für EXE-Symbol und Browser-Tab: drei Waben-Sechsecke in den Markenfarben.

    `farben` = Liste mit 1–3 Farben (oben links, rechts, unten links), aus firma.toml → [farben] marke."""
    import math
    farben = [_farbe(f) if isinstance(f, str) else f for f in farben] or [(0, 0, 0, 255)]
    farben = (farben * 3)[:3]
    f = 4  # überabtasten für glatte Kanten
    s = groesse * f
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # Sechsecke mit Spitzen links/rechts; Nachbarn im Wabenraster: (1,5 R | ±0,866 R)
    r = s / 3.6
    luecke = r * 0.10
    breite, hoehe = 3.5 * r, 2 * 0.866 * r + 2 * 0.866 * r
    x0, y0 = (s - breite) / 2 + r, (s - hoehe) / 2 + 0.866 * r
    mitten = [(x0, y0), (x0 + 1.5 * r, y0 + 0.866 * r), (x0, y0 + 1.732 * r)]
    for (cx, cy), farbe in zip(mitten, farben):
        rr = r - luecke
        d.polygon([(cx + rr * math.cos(math.radians(w)), cy + rr * math.sin(math.radians(w))) for w in range(0, 360, 60)],
                  fill=farbe)
    return img.resize((groesse, groesse), Image.LANCZOS)


def platzhalter_logo(name, zusatz, farbe, farbe2):
    breite, hoehe = 1800, 520
    img = Image.new("RGBA", (breite, hoehe), (255, 255, 255, 0))
    zeichen = bildmarke(400, [farbe])
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
    marken_farben = cfg["farben"].get("marke") or [cfg["farben"]["primaer"]]
    if len(sys.argv) > 1:
        logo = Image.open(sys.argv[1]).convert("RGBA")
        zeichen = (quadratisch(Image.open(sys.argv[2]).convert("RGBA")) if len(sys.argv) > 2
                   else bildmarke(256, marken_farben))
    else:
        firma = cfg["firma"]
        logo = platzhalter_logo(firma.get("firma_name") or cfg["programm"]["name"], firma.get("firma_zusatz", ""),
                                farbe, farbe2)
        zeichen = bildmarke(256, marken_farben)
    logo.save(BILDER / "logo_standard.png")
    zeichen.resize((128, 128), Image.LANCZOS).save(BILDER / "symbol.png")
    zeichen.resize((32, 32), Image.LANCZOS).save(BILDER / "favicon.png")
    zeichen.resize((256, 256), Image.LANCZOS).save(
        BILDER / "programm.ico", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    print("Logo und Symbole erzeugt in", BILDER)


if __name__ == "__main__":
    main()
