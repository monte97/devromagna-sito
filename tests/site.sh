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

check_global() {
  local index="$OUT/index.html"
  assert_file "$index"
  assert_contains "$index" "DevRomagna"

  local file
  while IFS= read -r file; do
    if grep -Eq '(href|src)=["'"'"']?/([^/]|$)' "$file"; then
      fail "link o asset root-relative in $file (usare relURL/absURL/.RelPermalink)"
    fi
  done < <(find "$OUT" -type f -name '*.html')
}

build_site
check_global

printf 'PASS\n'
