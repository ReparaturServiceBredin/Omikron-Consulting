# PyInstaller-Bauplan für die Mac-App (Apple-Chip, arm64). Name und Symbol kommen aus firma.toml.
# Bauen (auf einem Mac):  pyinstaller buchhaltung-mac.spec   -> dist/<kurzname>.app
import re
import tomllib

from PyInstaller.utils.hooks import collect_all

with open("firma.toml", "rb") as _f:
    _cfg = tomllib.load(_f)
KURZNAME = _cfg["programm"]["kurzname"]
ANZEIGE = _cfg["programm"]["name"]
with open("rsb/__init__.py", encoding="utf-8") as _f:
    VERSION = re.search(r'VERSION_NUMMER = "([^"]+)"', _f.read()).group(1)

datas = [
    ("rsb/templates", "rsb/templates"),
    ("rsb/static", "rsb/static"),
    ("rsb/schema.sql", "rsb"),
    ("docs/AENDERUNGEN.md", "docs"),
    ("firma.toml", "."),
]
binaries = []
hiddenimports = ["waitress", "pystray._darwin"]
for paket in ("reportlab", "tzdata", "facturx", "drafthorse", "pypdf", "lxml", "stdnum", "iso4217"):
    d, b, h = collect_all(paket)
    datas += d
    binaries += b
    hiddenimports += h

a = Analysis(
    ["start_exe.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    excludes=["tkinter", "pytest", "playwright", "aiosmtpd"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=KURZNAME,
    console=False,
    upx=False,
    target_arch="arm64",
)
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name=KURZNAME)
app = BUNDLE(
    coll,
    name=f"{KURZNAME}.app",
    icon="rsb/static/bilder/programm.icns",
    bundle_identifier="de.omikronconsulting.buchhaltung",
    version=VERSION,
    info_plist={
        "CFBundleDisplayName": ANZEIGE,
        "CFBundleName": KURZNAME,
        "CFBundleShortVersionString": VERSION,
        "CFBundleVersion": VERSION,
        "LSMinimumSystemVersion": "12.0",
        "LSUIElement": True,          # kein Dock-Symbol: bedient wird über das Symbol in der Menüleiste
        "NSHighResolutionCapable": True,
    },
)
