#!/bin/sh
set -e

# Set locale environment variables from the LOCALE env var.
# All UTF-8 locales are pre-generated at build time — no locale-gen needed at runtime.
LOCALE="${LOCALE-es_ES.UTF-8}"

if [ -n "$LOCALE" ]; then
    export LANG="$LOCALE"
    export LANGUAGE="$LOCALE"
    export LC_ALL="$LOCALE"
fi

exec /usr/local/bin/python main.py
