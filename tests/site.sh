#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT=""

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

build_site() {
  OUT="$(mktemp -d)"
  trap 'rm -rf "$OUT" "$ROOT/tests/fixtures/tmp"' EXIT
  ( cd "$ROOT" && hugo --gc --minify --environment test -d "$OUT" ) \
    || fail "build del sito fallita"
}

assert_file() {
  [ -f "$1" ] || fail "file mancante: $1"
}

assert_contains() {
  grep -q -- "$2" "$1" || fail "atteso \"$2\" in $1"
}

assert_not_contains() {
  grep -q -- "$2" "$1" && fail "non atteso \"$2\" in $1"
  return 0
}

site_base_path() {
  hugo config --environment test 2>/dev/null \
    | grep -i '^baseurl' \
    | head -n1 \
    | sed -E "s/^baseurl[[:space:]]*=[[:space:]]*['\"]?//; s/['\"]?[[:space:]]*$//" \
    | sed -E 's#^[a-zA-Z][a-zA-Z0-9+.-]*://[^/]+##'
}

check_global() {
  local index="$OUT/index.html"
  assert_file "$index"
  assert_contains "$index" "DevRomagna"

  local prefix file total prefixed
  prefix="$(site_base_path)"
  [ -n "$prefix" ] || prefix="/"

  while IFS= read -r file; do
    total="$(grep -Eo '(href|src)=["'"'"']?/' "$file" | wc -l | tr -d ' ')"
    prefixed="$(grep -Eo "(href|src)=[\"']?${prefix}" "$file" | wc -l | tr -d ' ')"
    [ "$total" -eq "$prefixed" ] \
      || fail "link o asset root-relative fuori da $prefix in $file (usare relURL/absURL/.RelPermalink)"
  done < <(find "$OUT" -type f -name '*.html')
}

check_task2() {
  local index="$OUT/index.html"
  assert_file "$index"

  local prefix css_href css_rel cssfile
  prefix="$(site_base_path)"
  [ -n "$prefix" ] || prefix="/"

  css_href="$(grep -Eo 'href=[^ >]+\.css' "$index" | head -n1 | sed -E 's/^href=//')"
  css_href="${css_href%\"}"
  css_href="${css_href#\"}"
  css_href="${css_href%\'}"
  css_href="${css_href#\'}"
  [ -n "$css_href" ] || fail "nessun CSS referenziato in index.html"

  case "$css_href" in
    *://*) css_href="${css_href#*://}"; css_href="${css_href#*/}" ;;
  esac

  css_rel="${css_href#/}"
  css_rel="${css_rel#"${prefix#/}"}"
  cssfile="$OUT/$css_rel"
  assert_file "$cssfile"
  assert_contains "$cssfile" "bricolage-grotesque"
  assert_contains "$cssfile" "work-sans"
  assert_contains "$cssfile" "font-display"

  assert_not_contains "$index" "fonts.googleapis"
  assert_not_contains "$index" "fonts.gstatic"
  assert_file "$OUT/img/logo.png"
  assert_file "$OUT/fonts/bricolage-grotesque-latin-800-normal.woff2"
  assert_file "$OUT/fonts/work-sans-latin-400-normal.woff2"
  assert_file "$OUT/fonts/work-sans-latin-600-normal.woff2"
  assert_file "$OUT/fonts/OFL-BricolageGrotesque.txt"
  assert_file "$OUT/fonts/OFL-WorkSans.txt"

  assert_contains "$index" "eventi/"
  assert_contains "$index" "#chi-siamo"
  assert_contains "$index" "#proponi"
  assert_contains "$index" "#ospitaci"
  assert_contains "$index" "meetup.com/devromagna"
  assert_contains "$index" "Entra su Meetup"
}

check_task3() {
  local page imgs oggi

  page="$OUT/eventi/2099-01-15-futuro/index.html"
  assert_file "$page"
  assert_contains "$page" "In arrivo"
  assert_contains "$page" "15 gen 2099"
  assert_contains "$page" "Iscriviti su Meetup"
  assert_not_contains "$page" "Tenuto"

  page="$OUT/eventi/2020-03-26-passato-completo/index.html"
  assert_file "$page"
  assert_contains "$page" "Tenuto"
  assert_contains "$page" "26 mar 2020"
  imgs="$(grep -o '<img' "$page" | wc -l | tr -d ' ')"
  [ "$imgs" -ge 2 ] || fail "attese almeno due immagini della galleria in $page"
  assert_contains "$page" "slide.pdf"
  assert_contains "$page" "database a grafo"
  assert_not_contains "$page" "Iscriviti su Meetup"

  page="$OUT/eventi/2018-05-25-passato-nudo/index.html"
  assert_file "$page"
  assert_contains "$page" "Introduzione a Docker"
  assert_contains "$page" "Tenuto"
  # solo nel contenuto (il menu contiene la voce "Speaker")
  tr -d '\n' < "$page" | sed 's#.*<main##; s#</main>.*##' | grep -q "Speaker" && fail "etichetta Speaker in un evento senza speaker"
  assert_not_contains "$page" "gallery"
  assert_not_contains "$page" "Slide"
  assert_not_contains "$page" "undefined"
  assert_not_contains "$page" "<p></p>"

  oggi="$(TZ=Europe/Rome date +%Y-%m-%d)"
  page="$OUT/eventi/$oggi-oggi/index.html"
  assert_file "$page"
  assert_contains "$page" "In arrivo"
}

check_task4() {
  local index="$OUT/index.html"
  assert_file "$index"

  assert_contains "$index" "Gli sviluppatori romagnoli fanno rete"
  assert_contains "$index" "Ci incontriamo per discutere di piattaforme"
  assert_contains "$index" "Proponi un talk"
  assert_contains "$index" "Ospitaci o sostienici"
  assert_contains "$index" "Incontri passati"
  assert_contains "$index" "sessionize.com/devromagna"
  assert_contains "$index" "clicks.meetup.com"
  assert_contains "$index" ".NET Foundation"
  assert_contains "$index" "Invoicetronic"
  assert_not_contains "$index" "incotriamo"
  # Il riquadro "Prossimo evento" mostra la serata di oggi (fixture-oggi), non quella dopo
  local box
  box="$(tr -d '\n' < "$index" | grep -o 'home-prossimo.*' | sed 's#</section>.*##')"
  printf '%s' "$box" | grep -q -- '-oggi/' || fail "il prossimo evento in home non e' la serata di oggi"
  printf '%s' "$box" | grep -q -- '2099-01-15-futuro' && fail "il prossimo evento in home salta la serata di oggi"
  return 0
}

check_task4_vuoto() {
  local out index
  out="$(mktemp -d)"
  ( cd "$ROOT" && hugo --gc --minify --environment test-vuoto -d "$out" ) \
    || fail "build del sito (test-vuoto) fallita"
  index="$out/index.html"
  assert_file "$index"
  assert_contains "$index" "Prossima serata in preparazione"
  assert_contains "$index" "meetup.com/devromagna"
  rm -rf "$out"
}

check_task5() {
  local page prefix off_arrivo off2020 off2018 off_oggi off2099

  page="$OUT/eventi/index.html"
  assert_file "$page"
  assert_contains "$page" "In arrivo"
  assert_contains "$page" "Il futuro del web"
  assert_contains "$page" "Incontro di oggi"
  assert_contains "$page" "Neo4j e i database a grafo"
  assert_contains "$page" "Introduzione a Docker"
  assert_contains "$page" "26 mar 2020"
  assert_contains "$page" "25 mag 2018"

  off_arrivo="$(grep -bo -- 'In arrivo' "$page" | head -n1 | cut -d: -f1)"
  off2020="$(grep -bo -- '>2020<' "$page" | head -n1 | cut -d: -f1)"
  off2018="$(grep -bo -- '>2018<' "$page" | head -n1 | cut -d: -f1)"
  off_oggi="$(grep -bo -- 'Incontro di oggi' "$page" | head -n1 | cut -d: -f1)"
  off2099="$(grep -bo -- 'Il futuro del web' "$page" | head -n1 | cut -d: -f1)"

  [ -n "$off_arrivo" ] && [ -n "$off2020" ] && [ -n "$off2018" ] \
    || fail "mancano le intestazioni di raggruppamento in $page"
  [ -n "$off_oggi" ] && [ -n "$off2099" ] \
    || fail "mancano gli eventi in arrivo in $page"

  [ "$off_arrivo" -lt "$off2020" ] || fail "il gruppo In arrivo non e' in testa in $page"
  [ "$off2020" -lt "$off2018" ] || fail "gli anni passati non sono dal piu' recente in $page"
  [ "$off_oggi" -lt "$off2099" ] || fail "gli eventi in arrivo non sono in ordine di data in $page"

  page="$OUT/onepage/index.html"
  assert_file "$page"
  grep -Eq 'http-equiv=[^ >]*refresh' "$page" || fail "meta refresh mancante in $page"
  assert_contains "$page" "url=https://monte97.github.io/devromagna-sito/"
  assert_contains "$page" "Vai alla home"
  assert_contains "$page" "noindex"

  prefix="$(site_base_path)"
  [ -n "$prefix" ] || prefix="/"

  page="$OUT/404.html"
  assert_file "$page"
  grep -Eq "href=[\"']?${prefix}" "$page" || fail "link alla home mancante in $page"
  grep -Eq "href=[\"']?${prefix}eventi/" "$page" || fail "link agli eventi mancante in $page"

  assert_file "$OUT/eventi/index.xml"
}

check_task6() {
  local eventi_dir="$ROOT/content/eventi"
  local cartelle voci_live id
  voci_live=32

  cartelle="$(find "$eventi_dir" -mindepth 1 -maxdepth 1 -type d | wc -l | tr -d ' ')"
  [ "$cartelle" -ge "$voci_live" ] \
    || fail "cartelle in content/eventi ($cartelle) meno delle voci della lista live ($voci_live)"

  for id in \
    303780376 303426360 301598446 296506014 296333460 293340671 292723436 \
    291862771 291027334 289709131 286896133 286413278 269579666 265866894 \
    260307622 258490013 257990206 256601308 255195925 250403502 249113255 \
    247896848 247045707 245313829 245283762 242114775 240838433 241083496 \
    238853473 239382597 239110404 238796165; do
    grep -Rq --include='index.md' -- "events/$id/" "$eventi_dir" \
      || fail "URL Meetup dell'evento $id assente da content/eventi"
  done

  grep -Rq -- "Il tuo collega più produttivo scrive test inutili" "$eventi_dir" \
    || fail "evento 'Il tuo collega più produttivo scrive test inutili' assente"
  grep -Rq -- "Web Components: a che punto siamo?" "$eventi_dir" \
    || fail "evento 'Web Components: a che punto siamo?' assente"

  page="$OUT/eventi/2025-10-30-web-components-a-che-punto-siamo/index.html"
  assert_file "$page"
  assert_contains "$page" "hanno subito evoluzioni significative"

  page="$OUT/eventi/2026-05-13-il-tuo-collega-piu-produttivo-scrive-test-inutili/index.html"
  assert_file "$page"
  assert_contains "$page" "segnaposto-01.svg"
  assert_contains "$page" "Le foto di questa pagina sono segnaposto."

  page="$OUT/eventi/2026-11-12-argus-sbom-guard-gestione-delle-vulnerabilita-a-partire/index.html"
  assert_file "$page"
  assert_contains "$page" "In arrivo"
  assert_contains "$page" "Matteo Vitali"
  assert_contains "$page" "Iscriviti su Meetup"
}

check_speaker_ospiti() {
  local page index sp_nicola sp_prossimi
  # Pagina speaker: ordinata per ultimo talk (Matteo Vitali, 12/11/2026, prima di Nicola Iarocci)
  page="$OUT/speaker/index.html"
  assert_file "$page"
  assert_contains "$page" "Nicola Iarocci"
  assert_contains "$page" "Matteo Galacci"
  assert_not_contains "$page" '"Mi"'
  sp_nicola="$(tr -d '\n' < "$page" | grep -o 'Nicola Iarocci.*' | wc -c)"
  sp_prossimi="$(tr -d '\n' < "$page" | grep -o 'Matteo Vitali.*' | wc -c)"
  [ "$sp_prossimi" -gt "$sp_nicola" ] || fail "speaker non ordinati per ultimo talk"
  # Pagina del singolo speaker, con i suoi talk
  page="$OUT/speaker/nicola-iarocci/index.html"
  assert_file "$page"
  assert_contains "$page" "6 talk"
  assert_contains "$page" "net-7-spotlight"
  assert_not_contains "$page" "LinkedIn"
  # Link LinkedIn e Sessionize dal file di dati (speaker delle fixture)
  page="$OUT/speaker/giulia-bianchi/index.html"
  assert_file "$page"
  assert_contains "$page" "linkedin.com/in/esempio-fixture"
  assert_contains "$page" "sessionize.com/esempio-fixture"
  # Dall'evento si arriva alla pagina dello speaker
  assert_contains "$OUT/eventi/2026-11-12-argus-sbom-guard-gestione-delle-vulnerabilita-a-partire/index.html" "speaker/matteo-vitali/"

  # Chi ci ha ospitato: ordinati per ultima serata, ognuno con la sua pagina
  page="$OUT/ospiti/index.html"
  assert_file "$page"
  assert_contains "$page" "Studio Mado"
  assert_contains "$page" "Iprel Progetti Srl"
  assert_not_contains "$page" "Online event"
  assert_not_contains "$page" "Viale Principe"
  local pos_lugo pos_mado
  pos_lugo="$(tr -d '\n' < "$page" | grep -o 'Incubatore U-Start.*' | wc -c)"
  pos_mado="$(tr -d '\n' < "$page" | grep -o 'Studio Mado.*' | wc -c)"
  [ "$pos_lugo" -gt "$pos_mado" ] || fail "ospiti non ordinati per ultima serata"
  assert_contains "$page" "poster"
  assert_contains "$page" "7 serate dal 2017"
  # Logo dai dati dove c'è, niente logo dove manca
  tr -d '\n' < "$OUT/ospiti/index.html" | grep -o 'poster-logo.\{0,200\}' | grep -q 'ospiti/abilio' || fail "logo di Abilio assente nella scheda"
  assert_contains "$OUT/ospiti/abilio-s.p.a./index.html" "term-logo"
  assert_contains "$OUT/ospiti/abilio-s.p.a./index.html" "abilio.com"
  assert_not_contains "$OUT/ospiti/studio-mado/index.html" "term-logo"
  # Il talk in fondo alla scheda è un link all'evento
  tr -d '\n' < "$OUT/ospiti/index.html" | grep -o 'poster-evento[^>]*' | grep -q 'eventi/' || fail "il talk nella scheda ospite non porta all'evento"
  page="$OUT/ospiti/studio-mado/index.html"
  assert_file "$page"
  assert_contains "$page" "7 serate"
  assert_contains "$page" "jest-painless-javascript-testing"
  # Schede poster: conteggio e anno del primo talk; foto dello speaker se c'è nei dati
  assert_contains "$OUT/speaker/index.html" "6 talk dal 2017"
  assert_contains "$OUT/speaker/index.html" "in arrivo"
  tr -d '\n' < "$OUT/speaker/index.html" | grep -o 'poster-foto[^>]*' | grep -q 'speaker/fixture-giulia' || fail "foto dello speaker assente nella scheda"
  assert_contains "$OUT/speaker/giulia-bianchi/index.html" "term-foto"
  assert_not_contains "$OUT/speaker/nicola-iarocci/index.html" "term-foto"

  # Navigazione e home: link alle pagine nuove, sponsor prima degli incontri passati
  index="$OUT/index.html"
  assert_contains "$index" "speaker/"
  assert_contains "$index" "ospiti/"
  local pos_partner pos_passati
  pos_partner="$(tr -d '\n' < "$index" | grep -o 'home-partner.*' | wc -c)"
  pos_passati="$(tr -d '\n' < "$index" | grep -o 'home-passati.*' | wc -c)"
  [ "$pos_partner" -gt "$pos_passati" ] || fail "gli sponsor devono stare prima degli incontri passati"
}

check_menu_attivo() {
  # La voce del menu della sezione in cui sei è marcata con aria-current
  nav_attiva() { tr -d '\n' < "$1" | grep -o '<nav class=site-nav.*</nav>' | grep -o '<a[^>]*aria-current=page[^>]*>[^<]*' | sed 's/.*>//'; }
  [ "$(nav_attiva "$OUT/eventi/index.html")" = "Eventi" ] || fail "menu: Eventi non attivo su /eventi/"
  [ "$(nav_attiva "$OUT/eventi/2026-11-12-argus-sbom-guard-gestione-delle-vulnerabilita-a-partire/index.html")" = "Eventi" ] || fail "menu: Eventi non attivo su un evento"
  [ "$(nav_attiva "$OUT/speaker/nicola-iarocci/index.html")" = "Speaker" ] || fail "menu: Speaker non attivo su uno speaker"
  [ "$(nav_attiva "$OUT/ospiti/index.html")" = "Chi ci ha ospitato" ] || fail "menu: Chi ci ha ospitato non attivo su /ospiti/"
  [ -z "$(nav_attiva "$OUT/index.html")" ] || fail "menu: nessuna voce va marcata in home"
}

check_evento_arricchito() {
  local page="$OUT/eventi/2026-05-13-il-tuo-collega-piu-produttivo-scrive-test-inutili/index.html"
  # locandina a lato, non nella galleria delle foto della serata
  assert_contains "$page" "evento-locandina"
  tr -d '\n' < "$page" | grep -o 'evento-gallery.*evento-testo' | grep -q 'locandina' && fail "la locandina e' finita nella galleria"
  assert_contains "$page" "Via san Giovanni Bosco"
  assert_contains "$page" "ospiti/fondazione-banca-del-monte"
  assert_contains "$page" "Apri la mappa"
  # descrizione completa anche dove prima c'era solo l'abstract
  assert_contains "$OUT/eventi/2025-10-30-web-components-a-che-punto-siamo/index.html" "evento-info"
}

bash "$ROOT/scripts/fixture-oggi.sh"
build_site
check_global
check_task2
check_task3
check_task4
check_task4_vuoto
check_task5
check_task6
check_speaker_ospiti
check_menu_attivo
check_evento_arricchito

printf 'PASS\n'
