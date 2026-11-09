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
  assert_not_contains "$page" "Speaker"
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
  assert_contains "$index" "2099-01-15-futuro"
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

bash "$ROOT/scripts/fixture-oggi.sh"
build_site
check_global
check_task2
check_task3
check_task4
check_task4_vuoto

printf 'PASS\n'
