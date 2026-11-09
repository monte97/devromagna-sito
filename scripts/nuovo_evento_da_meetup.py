#!/usr/bin/env python3
"""Crea la bozza dei prossimi eventi DevRomagna dal feed iCal di Meetup.

Uso: python3 scripts/nuovo_evento_da_meetup.py <url-o-file-ics> <cartella-eventi>

Crea un page bundle per ogni evento del feed che non ha ancora la sua cartella.
I bundle esistenti non vengono mai toccati: il file nel repo resta la fonte.
"""

import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parent))
from migra import slugify  # noqa: E402

ROMA = ZoneInfo("Europe/Rome")
SPEAKER_RE = re.compile(r"^\s*(?:Speakers?|Relatori?|Relatrice)\s*:\s*(.+)$", re.I)


def _unfold(text: str) -> list[str]:
    righe: list[str] = []
    for riga in text.replace("\r\n", "\n").split("\n"):
        if riga[:1] in (" ", "\t") and righe:
            righe[-1] += riga[1:]
        else:
            righe.append(riga)
    return righe


def _unescape(valore: str) -> str:
    return (
        valore.replace("\\n", "\n").replace("\\N", "\n")
        .replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
    )


def _data(nome: str, valore: str) -> datetime:
    tz = ROMA
    m = re.search(r"TZID=([^;:]+)", nome)
    if m:
        tz = ZoneInfo(m.group(1))
    if valore.endswith("Z"):
        return datetime.strptime(valore, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC")).astimezone(ROMA)
    return datetime.strptime(valore, "%Y%m%dT%H%M%S").replace(tzinfo=tz)


def _descrizione(testo: str) -> tuple[str | None, str]:
    speaker = None
    paragrafi = []
    for blocco in re.split(r"\n\s*\n", testo.strip()):
        righe = []
        for riga in blocco.split("\n"):
            m = SPEAKER_RE.match(riga)
            if m:
                speaker = speaker or m.group(1).strip()
            elif riga.strip() and riga.strip() != "DevRomagna":
                righe.append(riga.strip())
        if righe:
            paragrafi.append(" ".join(righe))
    return speaker, (paragrafi[0] if paragrafi else "")


def parse_ics(text: str) -> list[dict]:
    eventi = []
    corrente = None
    for riga in _unfold(text):
        if riga == "BEGIN:VEVENT":
            corrente = {}
        elif riga == "END:VEVENT" and corrente is not None:
            if "title" in corrente and "date" in corrente:
                eventi.append(corrente)
            corrente = None
        elif corrente is not None and ":" in riga:
            nome, valore = riga.split(":", 1)
            chiave = nome.split(";", 1)[0].upper()
            if chiave == "SUMMARY":
                corrente["title"] = _unescape(valore).strip()
            elif chiave == "DTSTART":
                corrente["date"] = _data(nome, valore.strip())
            elif chiave == "URL":
                corrente["meetup_url"] = valore.strip()
            elif chiave == "LOCATION" and valore.strip():
                corrente["location"] = _unescape(valore).strip()
            elif chiave == "DESCRIPTION":
                corrente["description"] = _unescape(valore)
                corrente["speaker"], corrente["abstract"] = _descrizione(corrente["description"])
    return eventi


def _yaml(valore: str) -> str:
    return '"' + valore.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _bundle(evento: dict) -> str:
    righe = ["---", f"title: {_yaml(evento['title'])}", f"date: {evento['date'].isoformat()}"]
    if evento.get("location"):
        righe.append(f"city: {_yaml(evento['location'])}")
    if evento.get("abstract"):
        righe.append(f"abstract: {_yaml(evento['abstract'])}")
    if evento.get("meetup_url"):
        righe.append(f"meetup_url: {_yaml(evento['meetup_url'])}")
    if evento.get("speaker"):
        righe += ["speakers:", f"  - {_yaml(evento['speaker'])}"]
    righe += ["---", "", (evento.get("description") or "").strip().replace("DevRomagna\n", "", 1), ""]
    return "\n".join(righe)


def main(url_or_path: str, out: Path) -> list[Path]:
    out = Path(out)
    if re.match(r"https?://", url_or_path):
        req = urllib.request.Request(url_or_path, headers={"User-Agent": "devromagna-sito"})
        testo = urllib.request.urlopen(req, timeout=30).read().decode("utf-8")
    else:
        testo = Path(url_or_path).read_text(encoding="utf-8")
    creati = []
    for evento in parse_ics(testo):
        cartella = out / f"{evento['date']:%Y-%m-%d}-{slugify(evento['title'])}"
        if cartella.exists():
            continue
        cartella.mkdir(parents=True)
        indice = cartella / "index.md"
        indice.write_text(_bundle(evento), encoding="utf-8")
        creati.append(indice)
    return creati


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    for percorso in main(sys.argv[1], Path(sys.argv[2])):
        print(percorso)
