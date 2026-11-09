#!/usr/bin/env python3
"""Fotografa le locandine degli eventi in arrivo e le salva accanto alle loro pagine.

Uso: python3 scripts/locandine.py <cartella-del-sito-compilato> [--tutti]

<cartella-del-sito-compilato> è l'output di `hugo -d <cartella>`, con il baseURL che termina in /devromagna-sito/
o in /. Per ogni evento in arrivo (o tutti, con --tutti) apre eventi/<slug>/locandina.html e scrive nella
stessa cartella locandina-quadrata.png (1080x1080), locandina-16x9.png (1920x1080) e locandina.pdf (A4).
"""

import functools
import http.server
import re
import socketserver
import struct
import sys
import threading
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

FORMATI = {"quadrata": (1080, 1080), "16x9": (1920, 1080)}
OGGI = datetime.now(ZoneInfo("Europe/Rome")).date()


def dimensioni_png(percorso: Path) -> tuple[int, int]:
    testa = percorso.read_bytes()[:24]
    if testa[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError(f"{percorso} non è un PNG")
    return struct.unpack(">II", testa[16:24])


def controlla(pagina, nome: str) -> None:
    """Si ferma se il titolo esce dal suo spazio o se qualcosa sborda dalla locandina."""
    esito = pagina.evaluate("""() => {
      const box = document.querySelector('.loc-titolo-box');
      const loc = document.querySelector('.locandina');
      return {
        titolo: box.scrollHeight <= box.clientHeight + 2 && box.scrollWidth <= box.clientWidth + 2,
        bordi: loc.scrollHeight <= loc.clientHeight + 2 && loc.scrollWidth <= loc.clientWidth + 2,
      };
    }""")
    if not (esito["titolo"] and esito["bordi"]):
        raise RuntimeError(f"locandina {nome}: il testo non sta nello spazio ({esito})")


def eventi_da_fotografare(sito: Path, tutti: bool) -> list[Path]:
    """Cartelle eventi/<slug>/ che hanno locandina.html, filtrate per data dal nome (AAAA-MM-GG-...)."""
    scelti = []
    for pagina in sorted(sito.glob("eventi/*/locandina.html")):
        m = re.match(r"(\d{4})-(\d{2})-(\d{2})-", pagina.parent.name)
        if not m:
            continue
        giorno = date(*map(int, m.groups()))
        if tutti or giorno >= OGGI:
            scelti.append(pagina.parent)
    return scelti


def prefisso(sito: Path) -> str:
    """Il sottopercorso del baseURL (es. /devromagna-sito/), letto da un link della home."""
    home = (sito / "index.html").read_text(encoding="utf-8")
    m = re.search(r'(?:href|src)=["\']?(/[^"\' >]*?)css/', home)
    return m.group(1) if m else "/"


def main(sito: Path, tutti: bool = False) -> list[Path]:
    from playwright.sync_api import sync_playwright

    sito = Path(sito).resolve()
    cartelle = eventi_da_fotografare(sito, tutti)
    if not cartelle:
        print("nessun evento in arrivo: niente locandine da generare")
        return []
    base = prefisso(sito)
    # il server serve il sito sotto il suo sottopercorso, come GitHub Pages
    radice = sito.parent / "_radice_locandine"
    radice.mkdir(exist_ok=True)
    link = radice / base.strip("/") if base.strip("/") else None
    if link and not link.exists():
        link.symlink_to(sito, target_is_directory=True)
    servi = radice if link else sito
    class Silenzioso(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    gestore = functools.partial(Silenzioso, directory=str(servi))
    scritti = []
    with socketserver.TCPServer(("127.0.0.1", 0), gestore) as server:
        porta = server.server_address[1]
        threading.Thread(target=server.serve_forever, daemon=True).start()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            for cartella in cartelle:
                url = f"http://127.0.0.1:{porta}{base}eventi/{cartella.name}/locandina.html"
                for nome, (w, h) in FORMATI.items():
                    pagina = browser.new_page(viewport={"width": w, "height": h})
                    pagina.goto(f"{url}?formato={nome}")
                    pagina.wait_for_selector("body[data-pronta]")
                    pagina.wait_for_load_state("networkidle")
                    controlla(pagina, f"{cartella.name} {nome}")
                    out = cartella / f"locandina-{nome}.png"
                    pagina.screenshot(path=str(out), clip={"x": 0, "y": 0, "width": w, "height": h})
                    if dimensioni_png(out) != (w, h):
                        raise RuntimeError(f"{out}: dimensioni {dimensioni_png(out)} invece di {(w, h)}")
                    scritti.append(out)
                    pagina.close()
                pagina = browser.new_page()
                pagina.goto(f"{url}?formato=a4")
                pagina.wait_for_selector("body[data-pronta]")
                pagina.wait_for_load_state("networkidle")
                out = cartella / "locandina.pdf"
                pagina.pdf(path=str(out), format="A4", print_background=True, prefer_css_page_size=True)
                scritti.append(out)
                pagina.close()
                print("locandine:", cartella.name)
            browser.close()
        server.shutdown()
    if link and link.is_symlink():
        link.unlink()
    radice.rmdir()
    return scritti


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    main(Path(sys.argv[1]), "--tutti" in sys.argv)
