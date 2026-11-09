# Sito DevRomagna

Prototipo del nuovo sito di [DevRomagna](https://www.meetup.com/devromagna/), la developer community della Romagna. Sito statico in [Hugo](https://gohugo.io/), pubblicato su GitHub Pages a ogni push su `main` e ricompilato ogni notte.

Online: https://monte97.github.io/devromagna-sito/

## Aggiungere un evento

Ogni evento è una cartella in `content/eventi/`, chiamata `AAAA-MM-GG-titolo-breve` (solo minuscole, numeri e trattini).

Due modi:

- **Dal feed di Meetup.** Nella tab Actions lancia il workflow "Bozza evento da Meetup": crea le cartelle degli eventi in arrivo che mancano e apre una PR. Controlla città, sede, speaker e abstract prima del merge.
- **A mano.** `hugo new eventi/2026-12-16-titolo-breve/index.md`, poi compila il frontmatter.

Frontmatter (obbligatori solo `title` e `date`):

```yaml
title: "Titolo del talk"
date: 2026-12-16T19:00:00+01:00
speakers:
  - "Nome Cognome"
city: "Faenza"
host: "Azienda o spazio che ci ospita"
meetup_url: "https://www.meetup.com/devromagna/events/..."
abstract: "Due o tre righe sul talk."
slides: "slide.pdf"   # file nella cartella o URL
repo: ""
video: ""
attendees:            # numero di presenti, dopo la serata
```

Fino al giorno della serata la pagina è un annuncio con il bottone di Meetup. Dal giorno dopo diventa il post: mostra le foto della cartella, il testo sotto il frontmatter e i link a slide, repo e video. Lo stato si calcola dalla data, non va scritto.

## Dopo la serata

Nella cartella dell'evento:

- aggiungi le foto (`foto-01.jpg`, `foto-02.jpg`, ...), già ridimensionate a una dimensione ragionevole, meglio sotto 1 MB l'una: Hugo crea le miniature;
- aggiungi le slide come `slide.pdf`, oppure metti il link in `slides`;
- scrivi due righe su com'è andata sotto il frontmatter;
- se vuoi, compila `attendees`.

## Speaker e chi ci ha ospitato

Ogni nome in `speakers` diventa una pagina `/speaker/nome-cognome/` con i suoi talk; l'elenco `/speaker/` è ordinato per ultimo talk. Scrivi il nome sempre allo stesso modo, o finisce su due pagine diverse.

Link e una riga di bio, facoltativi, in `data/speaker.yaml`, con il nome scritto come negli eventi:

```yaml
"Nome Cognome":
  linkedin: "https://www.linkedin.com/in/..."
  sessionize: "https://sessionize.com/..."
  sito: "https://..."
  bio: "Una riga su chi è."
```

Lo stesso vale per chi ci ospita: ogni valore di `host` diventa una pagina `/ospiti/nome/`, e l'elenco `/ospiti/` è ordinato per ultima serata. Sito, LinkedIn e una riga di descrizione, facoltativi, in `data/ospiti.yaml`:

```yaml
"Nome Azienda":
  sito: "https://..."
  linkedin: "https://www.linkedin.com/company/..."
  descrizione: "Una riga su chi sono."
```

## Sponsor, media partner, affiliazioni

In `data/partner.yaml`, una voce per partner, con il logo in `static/img/partner/`:

```yaml
- name: "Nome"
  type: sponsor        # sponsor | media-partner | affiliazione
  url: "https://..."
  logo: "img/partner/nome.svg"
```

Un gruppo compare in home solo quando ha almeno una voce.

## In locale

```bash
hugo server            # http://localhost:1313/devromagna-sito/
bash tests/site.sh     # build di prova e controlli sull'HTML
python3 -m unittest    # test degli script Python
```

Serve Hugo extended alla versione scritta in `.hugo-version`.

## Passare a devromagna.org

1. In `hugo.toml` metti `baseURL = "https://devromagna.org/"`.
2. Crea `static/CNAME` con dentro `devromagna.org`.
3. Configura il dominio nelle impostazioni Pages del repo.

## Da verificare

`MIGRAZIONE-DA-VERIFICARE.md` elenca i dati della migrazione dal vecchio sito che vanno controllati da un organizzatore.
