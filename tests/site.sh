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
  trap 'rm -rf "$OUT"' EXIT
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

build_site
check_global
check_task2

printf 'PASS\n'
