"""Migrazione degli incontri passati di DevRomagna.

Legge la lista storica del sito, gli eventi Meetup e le cartelle dei materiali,
e scrive un bundle Hugo per ogni incontro.
"""

import json
import re
import shutil
import unicodedata
from datetime import date, datetime
from html import unescape
from pathlib import Path
from urllib.parse import quote


START_YEAR = 2017
MAX_SLUG = 60
APOSTROFI = "'\u2019\u2018"
MAX_ABSTRACT = 400

KNOWN_FOLDER_IDS = {
    "20180221-ElasticSearch4Dummies": "257990206",
}

CODE_EXTENSIONS = {
    ".c", ".cs", ".css", ".ex", ".exs", ".go", ".h", ".html", ".java",
    ".js", ".json", ".jsx", ".nq", ".php", ".py", ".rb", ".rs", ".sh",
    ".ts", ".tsx", ".yaml", ".yml", ".cypher",
}

LINK_EVENTO = re.compile(
    r'<a\s+href="([^"]*meetup\.com[^"]*/events/(\d+)/?[^"]*)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
SPEAKER = re.compile(r"^\s*(?:speakers?|relatore|relatori)\s*:\s*(.*)$", re.IGNORECASE)
NOME = re.compile(
    r"^((?:[A-ZÀ-ÖØ-Þ][a-zA-ZÀ-ÖØ-öø-ÿ'\u2019-]+\s*){1,4})"
)
FOTO = re.compile(r"^https?://\S+\.(?:jpe?g|png|gif|webp)$", re.IGNORECASE)


def slugify(title):
    """Trasforma un titolo in uno slug ``[a-z0-9-]`` di al massimo 60 caratteri."""
    testo = unicodedata.normalize("NFKD", title)
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    testo = testo.lower()
    for apostrofo in APOSTROFI:
        testo = testo.replace(apostrofo, "")
    testo = re.sub(r"[^a-z0-9]+", "-", testo)
    testo = re.sub(r"-{2,}", "-", testo).strip("-")
    if len(testo) > MAX_SLUG:
        tagliato = testo[:MAX_SLUG]
        if "-" in tagliato:
            tagliato = tagliato[: tagliato.rfind("-")]
        testo = tagliato.strip("-")
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


def normalizza(testo):
    testo = unicodedata.normalize("NFKD", testo or "")
    testo = "".join(c for c in testo if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "", testo.lower())


def leggi_live_index(percorso):
    """Estrae gli incontri passati dalla pagina storica."""
    html = Path(percorso).read_text(encoding="utf-8", errors="replace")
    evento = {}
    ordine = []
    for href, event_id, grezzo in LINK_EVENTO.findall(html):
        titolo = unescape(re.sub(r"<[^>]+>", "", grezzo))
        titolo = " ".join(titolo.split())
        if event_id not in evento:
            evento[event_id] = {
                "id": event_id,
                "url": href,
                "titolo_live": titolo,
            }
            ordine.append(event_id)
    return [evento[event_id] for event_id in ordine]


def leggi_meetup(percorso):
    """Legge il JSON degli eventi Meetup gia' scaricato."""
    dati = json.loads(Path(percorso).read_text(encoding="utf-8"))
    eventi = []
    for voce in dati:
        momento = datetime.fromisoformat(voce["dateTime"])
        eventi.append(
            {
                "id": str(voce.get("id") or ""),
                "title": (voce.get("title") or "").strip(),
                "date": momento.date(),
                "datetime": momento.isoformat(),
                "description": voce.get("description") or "",
                "city": (voce.get("city") or "").strip(),
                "host": (voce.get("venue") or "").strip(),
                "url": (voce.get("url") or "").strip(),
            }
        )
    return eventi


def prima_paragrafo(descrizione):
    for paragrafo in re.split(r"\n\s*\n", descrizione or ""):
        testo = " ".join(paragrafo.split())
        if not testo:
            continue
        if FOTO.match(testo):
            continue
        if testo.startswith("http") and len(testo.split()) == 1:
            continue
        testo = re.sub(r"(\*\*|__|`)", "", testo)
        return testo
    return ""


def estrai_abstract(descrizione):
    testo = prima_paragrafo(descrizione)
    if len(testo) <= MAX_ABSTRACT:
        return testo
    tagliato = testo[:MAX_ABSTRACT]
    tagliato = tagliato[: tagliato.rfind(" ")].rstrip()
    return tagliato + "..."


def _nomi(riga):
    testo = re.sub(r"\([^)]*\)", "", riga)
    testo = re.sub(r"\.\s.*$", "", testo)
    testo = testo.split(",")[0]
    nomi = []
    for parte in re.split(r"\s+e\s+", testo, flags=re.IGNORECASE):
        parte = parte.strip(" .;:")
        if not parte:
            continue
        trovato = NOME.match(parte)
        if trovato:
            nomi.append(" ".join(trovato.group(1).split()))
    return nomi


def estrai_speaker(descrizione):
    righe = (descrizione or "").splitlines()
    nomi = []
    for indice, riga in enumerate(righe):
        trovato = SPEAKER.match(riga)
        if not trovato:
            continue
        raccolte = []
        resto = trovato.group(1).strip()
        if resto:
            raccolte.append(resto)
        successivo = indice + 1
        while successivo < len(righe):
            linea = righe[successivo].strip()
            if not linea:
                if raccolte:
                    seguente = successivo + 1
                    while seguente < len(righe) and not righe[seguente].strip():
                        seguente += 1
                    if seguente < len(righe) and righe[seguente].strip().startswith(
                        ("-", "*", "•")
                    ):
                        successivo = seguente
                        continue
                    break
                successivo += 1
                continue
            if linea.startswith("#") or SPEAKER.match(linea):
                break
            if re.match(r"^(?:PS|P\.S\.|ATTENZIONE|Nota|NB)\b", linea, re.IGNORECASE):
                break
            if linea.startswith(("-", "*", "•")):
                raccolte.append(linea.lstrip("-*• ").strip())
                successivo += 1
                continue
            if not raccolte:
                raccolte.append(linea)
                successivo += 1
                continue
            break
        for voce in raccolte:
            nomi.extend(_nomi(voce))
        break

    visti = []
    for nome in nomi:
        if nome not in visti:
            visti.append(nome)
    return visti


def _readme(cartella):
    for nome in ("README.md", "readme.md", "Readme.md"):
        percorso = cartella / nome
        if percorso.is_file():
            return percorso.read_text(encoding="utf-8", errors="replace")
    return ""


def _titolo_readme(testo):
    righe = testo.splitlines()
    indice = 0
    while indice < len(righe) and not righe[indice].strip():
        indice += 1
    if indice >= len(righe):
        return None
    prima = righe[indice].strip()
    if prima.startswith("#"):
        return prima.lstrip("#").strip() or None
    successivo = indice + 1
    while successivo < len(righe) and not righe[successivo].strip():
        successivo += 1
    if successivo < len(righe) and re.fullmatch(r"[=-]{3,}", righe[successivo].strip()):
        return prima
    return None


def _senza_titolo_iniziale(testo):
    righe = testo.splitlines()
    indice = 0
    while indice < len(righe) and not righe[indice].strip():
        indice += 1
    if indice >= len(righe):
        return ""
    if righe[indice].lstrip().startswith("#"):
        return "\n".join(righe[indice + 1 :]).lstrip("\n")
    successivo = indice + 1
    while successivo < len(righe) and not righe[successivo].strip():
        successivo += 1
    if successivo < len(righe) and re.fullmatch(r"[=-]{3,}", righe[successivo].strip()):
        return "\n".join(righe[successivo + 1 :]).lstrip("\n")
    return testo


def _pdf(cartella):
    return sorted(
        percorso
        for percorso in cartella.iterdir()
        if percorso.is_file() and percorso.suffix.lower() == ".pdf"
    )


def _pptx(cartella):
    return sorted(
        percorso
        for percorso in cartella.iterdir()
        if percorso.is_file() and percorso.suffix.lower() == ".pptx"
    )


def _ha_codice(cartella):
    for percorso in cartella.rglob("*"):
        if percorso.is_file() and percorso.suffix.lower() in CODE_EXTENSIONS:
            return True
    return False


def _url_github(*parti):
    encoded = "/".join(quote(parte, safe="") for parte in parti)
    return "https://github.com/DevRomagna/eventi/tree/master/" + encoded


def _titolo_cartella(cartella):
    ricavato = _titolo_readme(_readme(cartella))
    if ricavato:
        return ricavato
    nome = cartella.name
    trovato = re.match(r"^\d{8}-(.+)$", nome)
    if trovato:
        return trovato.group(1).replace("-", " ").strip()
    return nome.replace("-", " ").strip()


def _accorpa_cartelle(eventi, cartelle, problemi):
    per_id = {evento["id"]: evento for evento in eventi}
    per_data = {}
    for evento in eventi:
        per_data.setdefault(evento["date"], []).append(evento)

    for cartella in cartelle:
        data_cartella = parse_folder_date(cartella.name)
        scelto = None
        if cartella.name in KNOWN_FOLDER_IDS:
            scelto = per_id.get(KNOWN_FOLDER_IDS[cartella.name])
        if scelto is None and data_cartella is not None:
            candidati = per_data.get(data_cartella, [])
            if len(candidati) == 1:
                scelto = candidati[0]
            elif len(candidati) > 1:
                atteso = normalizza(_titolo_cartella(cartella))
                for candidato in candidati:
                    if normalizza(candidato["title"]) == atteso:
                        scelto = candidato
                        break
        if scelto is None:
            atteso = normalizza(_titolo_cartella(cartella))
            for evento in eventi:
                if normalizza(evento["title"]) == atteso:
                    scelto = evento
                    break

        if scelto is None:
            titolo = _titolo_cartella(cartella)
            evento = {
                "id": None,
                "title": titolo,
                "date": data_cartella,
                "datetime": None,
                "description": "",
                "city": "",
                "host": "",
                "url": "",
                "folder": cartella,
            }
            eventi.append(evento)
            per_id[None] = evento
            if data_cartella is not None:
                per_data.setdefault(data_cartella, []).append(evento)
            problemi.append(
                "Materiali nella cartella %s senza evento Meetup corrispondente: "
                "evento creato con la data presa dal nome della cartella."
                % cartella.name
            )
            continue

        scelto["folder"] = cartella
        if data_cartella is not None and data_cartella != scelto["date"]:
            problemi.append(
                "Cartella %s: il nome indica il %s, Meetup il %s. "
                "Usata la data di Meetup."
                % (
                    cartella.name,
                    data_cartella.isoformat(),
                    scelto["date"].isoformat(),
                )
            )


def _front_matter(evento, slides, repo):
    righe = ["---"]
    righe.append("title: " + json.dumps(evento["title"], ensure_ascii=False))
    if evento.get("datetime"):
        righe.append("date: " + evento["datetime"])
    elif evento.get("date"):
        righe.append("date: " + evento["date"].isoformat())
    if evento.get("city"):
        righe.append("city: " + json.dumps(evento["city"], ensure_ascii=False))
    if evento.get("host"):
        righe.append("host: " + json.dumps(evento["host"], ensure_ascii=False))
    abstract = estrai_abstract(evento.get("description", ""))
    if abstract:
        righe.append("abstract: " + json.dumps(abstract, ensure_ascii=False))
    if evento.get("url"):
        righe.append("meetup_url: " + json.dumps(evento["url"], ensure_ascii=False))
    speaker = estrai_speaker(evento.get("description", ""))
    if speaker:
        righe.append("speakers:")
        for nome in speaker:
            righe.append("  - " + json.dumps(nome, ensure_ascii=False))
    if slides:
        righe.append("slides: " + json.dumps(slides, ensure_ascii=False))
    if repo:
        righe.append("repo: " + json.dumps(repo, ensure_ascii=False))
    righe.append("---")
    return "\n".join(righe)


def _scrivi_evento(evento, radice, problemi):
    if not evento.get("date"):
        problemi.append(
            "Evento %s senza data certa: non e' stato possibile creare la pagina."
            % evento["title"]
        )
        return

    slug = slugify(evento["title"]) or "evento"
    nome = "%s-%s" % (evento["date"].isoformat(), slug)
    cartella = radice / nome
    indice = cartella / "index.md"
    if indice.exists():
        return

    cartella.mkdir(parents=True, exist_ok=True)
    folder = evento.get("folder")
    slides = ""
    repo = ""
    corpo = ""

    if folder is not None:
        mapping = {}
        for numero, pdf in enumerate(_pdf(folder)):
            nuovo = "slide.pdf" if numero == 0 else "slide-%d.pdf" % (numero + 1)
            destinazione = cartella / nuovo
            if not destinazione.exists():
                shutil.copyfile(pdf, destinazione)
            mapping[pdf.name] = nuovo
            if numero == 0:
                slides = nuovo
        if not slides:
            presentazioni = _pptx(folder)
            if presentazioni:
                slides = (
                    "https://github.com/DevRomagna/eventi/blob/master/%s/%s"
                    % (quote(folder.name, safe=""), quote(presentazioni[0].name, safe=""))
                )
        if _ha_codice(folder):
            repo = _url_github(folder.name)
        corpo = _senza_titolo_iniziale(_readme(folder))
        for originale, nuovo in mapping.items():
            corpo = corpo.replace(originale, nuovo)
            corpo = corpo.replace(
                quote(originale, safe=""), quote(nuovo, safe="")
            )

    testo = _front_matter(evento, slides, repo) + "\n"
    if corpo.strip():
        testo += "\n" + corpo.rstrip() + "\n"
    indice.write_text(testo, encoding="utf-8")


def _scrivi_report(problemi, out):
    righe = [
        "# Migrazione da verificare",
        "",
        "Voci emerse durante la migrazione dal sito storico che richiedono una "
        "conferma prima del passaggio a devromagna.org.",
        "",
        "## Da verificare",
        "",
        "- Link di contatto per \"Ospitaci o sostienici\": per ora punta alla pagina "
        "Meetup della community, da sostituire con un indirizzo dedicato se disponibile.",
        "- Nessun evento trovato fra ottobre 2024 e settembre 2025: verificare se ci "
        "sono serate mancanti.",
    ]
    for problema in problemi:
        righe.append("- " + problema)
    righe.append("")
    (out / "MIGRAZIONE-DA-VERIFICARE.md").write_text(
        "\n".join(righe), encoding="utf-8"
    )


def main(live_index, eventi_repo, meetup_json, out):
    """Unisce le tre fonti e scrive i bundle degli incontri passati."""
    live_index = Path(live_index)
    eventi_repo = Path(eventi_repo)
    meetup_json = Path(meetup_json)
    out = Path(out)

    problemi = []
    oggi = date.today()
    live = leggi_live_index(live_index)
    eventi = [evento for evento in leggi_meetup(meetup_json) if evento["date"] <= oggi]
    per_id = {evento["id"]: evento for evento in eventi}

    in_live = {voce["id"] for voce in live}
    for voce in live:
        if voce["id"] in per_id:
            per_id[voce["id"]]["url"] = per_id[voce["id"]]["url"] or voce["url"]
        else:
            eventi.append(
                {
                    "id": voce["id"],
                    "title": voce["titolo_live"],
                    "date": None,
                    "datetime": None,
                    "description": "",
                    "city": "",
                    "host": "",
                    "url": voce["url"],
                    "folder": None,
                }
            )

    cartelle = sorted(
        percorso
        for percorso in eventi_repo.iterdir()
        if percorso.is_dir() and not percorso.name.startswith(".")
    )
    _accorpa_cartelle(eventi, cartelle, problemi)

    with_folder = {evento["folder"].name for evento in eventi if evento.get("folder")}
    for evento in eventi:
        if evento["id"] and evento["id"] not in in_live and evento.get("folder") is None:
            problemi.append(
                "Evento \"%s\" (%s) presente solo fra gli eventi Meetup, "
                "senza materiali ne' voce nella pagina storica."
                % (evento["title"], evento["date"].isoformat())
            )

    radice = out / "content" / "eventi"
    radice.mkdir(parents=True, exist_ok=True)
    for evento in sorted(eventi, key=lambda voce: (voce["date"] or date.min, voce["title"])):
        _scrivi_evento(evento, radice, problemi)

    _scrivi_report(problemi, out)


if __name__ == "__main__":
    import sys

    if len(sys.argv) != 5:
        raise SystemExit(
            "uso: migra.py <index-live.html> <cartella-eventi> <meetup.json> <uscita>"
        )
    main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
