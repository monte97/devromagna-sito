#!/usr/bin/env bash
set -eu

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OGGI="$(TZ=Europe/Rome date +%Y-%m-%d)"
TMP="$ROOT/tests/fixtures/tmp"
DIR="$TMP/content/eventi/$OGGI-oggi"

rm -rf "$TMP"
mkdir -p "$DIR"

cat > "$DIR/index.md" <<EOF
---
title: "Incontro di oggi"
date: ${OGGI}T20:00:00
city: "Ravenna"
abstract: "L'incontro di questa sera."
tags: ["community"]
---

Ci vediamo stasera.
EOF
