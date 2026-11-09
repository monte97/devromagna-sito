"""Migrazione degli incontri passati di DevRomagna.

Unit 6a: funzioni di supporto ``slugify`` e ``parse_folder_date``.
La funzione ``main`` completa arriva nella unit 6b.
"""

import re
import unicodedata
from datetime import date
from pathlib import Path


START_YEAR = 2017
MAX_SLUG = 60
APOSTROFI = "'\u2019\u2018"


def slugify(title):
    """Trasforma un titolo in uno slug ``[a-z0-9-]`` di al massimo 60 caratteri."""
    testo = unicodedata.normalize("NFKD", title)
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    testo = testo.lower()
    for apostrofo in APOSTROFI:
        testo = testo.replace(apostrofo, "")
    testo = re.sub(r"[^a-z0-9]+", "-", testo)
    testo = re.sub(r"-{2,}", "-", testo).strip("-")
    testo = testo[:MAX_SLUG].strip("-")
    return testo


def parse_folder_date(name):
    """Riconosce ``YYYYMMDD-...`` o ``DDMMYYYY-...`` fra il 2017 e oggi."""
    match = re.match(r"^(\d{8})(?:-|$)", name)
    if not match:
        return None
    cifre = match.group(1)

    candidate = []
    try:
        candidate.append(date(int(cifre[:4]), int(cifre[4:6]), int(cifre[6:8])))
    except ValueError:
        pass
    try:
        candidate.append(date(int(cifre[4:8]), int(cifre[2:4]), int(cifre[0:2])))
    except ValueError:
        pass

    oggi = date.today()
    for valore in candidate:
        if START_YEAR <= valore.year and valore <= oggi:
            return valore
    return None


def main(live_index, eventi_repo, meetup_past, out):
    raise NotImplementedError("la migrazione completa arriva nella unit 6b")
