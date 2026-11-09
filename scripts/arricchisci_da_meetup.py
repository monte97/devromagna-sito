#!/usr/bin/env python3
"""Arricchisce gli eventi con i dati delle pagine Meetup salvate in locale.

Uso: python3 scripts/arricchisci_da_meetup.py <cartella-pagine-meetup> <content/eventi> [--scarica-locandine]

Per ogni bundle con `meetup_url`, legge la pagina Meetup salvata (<id>.html) e:
- se il corpo del bundle è vuoto, ci scrive la descrizione completa dell'evento;
- aggiunge `address` e `map_url` della sede, se mancano;
- con --scarica-locandine, salva l'immagine dell'evento come locandina.jpg nel bundle.
Non sovrascrive mai un corpo già scritto né campi già presenti.
"""

import json
import re
import sys
import urllib.request
from pathlib import Path

URL_FOTO = re.compile(r"^\s*https?://\S+\.(?:jpe?g|png|gif)\s*$", re.I)


def dati_meetup(html: str, event_id: str) -> dict:
    m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S)
    if not m:
        return {}
    stato = json.loads(m.group(1)).get("props", {}).get("pageProps", {}).get("__APOLLO_STATE__", {})
    ev = stato.get(f"Event:{event_id}", {})

    def deref(v):
        return stato.get(v["__ref"], {}) if isinstance(v, dict) and "__ref" in v else (v or {})

    sede = deref(ev.get("venue"))
    foto = deref(ev.get("featuredEventPhoto") or ev.get("displayPhoto"))
    return {
        "description": ev.get("description") or "",
        "address": sede.get("address"),
        "map_url": sede.get("googleMapsUrl"),
        "photo": foto.get("highResUrl"),
    }


def pulisci_descrizione(testo: str) -> str:
    righe = [r.rstrip() for r in testo.replace("\r\n", "\n").split("\n") if not URL_FOTO.match(r)]
    corpo = "\n".join(righe).strip()
    return re.sub(r"\n{3,}", "\n\n", corpo)


def dividi(testo: str) -> tuple[str, str]:
    m = re.match(r"^---\n(.*?)\n---\n?(.*)$", testo, re.S)
    if not m:
        raise ValueError("frontmatter mancante")
    return m.group(1), m.group(2)


def _yaml(valore: str) -> str:
    return json.dumps(valore, ensure_ascii=False)


def arricchisci(bundle: Path, pagine: Path, scarica: bool = False) -> list[str]:
    indice = bundle / "index.md"
    fm, corpo = dividi(indice.read_text(encoding="utf-8"))
    m = re.search(r'^meetup_url:\s*"?https?://[^"\n]*/events/(\d+)/?"?\s*$', fm, re.M)
    if not m:
        return []
    pagina = pagine / f"{m.group(1)}.html"
    if not pagina.is_file():
        return []
    dati = dati_meetup(pagina.read_text(encoding="utf-8"), m.group(1))
    fatto = []
    if dati.get("address") and not re.search(r"^address:", fm, re.M):
        fm += f"\naddress: {_yaml(dati['address'])}"
        fatto.append("address")
    if dati.get("map_url") and not re.search(r"^map_url:", fm, re.M):
        fm += f"\nmap_url: {_yaml(dati['map_url'])}"
        fatto.append("map_url")
    descrizione = pulisci_descrizione(dati.get("description", ""))
    if not corpo.strip() and descrizione:
        corpo = descrizione + "\n"
        fatto.append("corpo")
    if fatto:
        indice.write_text(f"---\n{fm}\n---\n\n{corpo.lstrip()}", encoding="utf-8")
    locandina = bundle / "locandina.jpg"
    if scarica and dati.get("photo") and not locandina.exists():
        req = urllib.request.Request(dati["photo"], headers={"User-Agent": "devromagna-sito"})
        locandina.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        fatto.append("locandina")
    return fatto


def main(pagine: Path, eventi: Path, scarica: bool = False) -> dict[str, list[str]]:
    esito = {}
    for bundle in sorted(p for p in Path(eventi).iterdir() if (p / "index.md").is_file()):
        fatto = arricchisci(bundle, Path(pagine), scarica)
        if fatto:
            esito[bundle.name] = fatto
    return esito


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    for nome, fatto in main(Path(sys.argv[1]), Path(sys.argv[2]), "--scarica-locandine" in sys.argv).items():
        print(nome, ",".join(fatto))
