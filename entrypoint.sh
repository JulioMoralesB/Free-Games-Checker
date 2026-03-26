#!/bin/bash
set -e

# Use the LOCALE env var; default to es_ES.UTF-8 only when LOCALE is truly unset
LOCALE="${LOCALE-es_ES.UTF-8}"

if [ -n "$LOCALE" ]; then
    # Escape special regex characters so the locale string is safe to use in sed
    LOCALE_ESCAPED="$(printf '%s\n' "$LOCALE" | sed 's/[].*[\^$\/]/\\&/g')"

    # Uncomment the requested locale in /etc/locale.gen and generate it
    sed -i "/^# *${LOCALE_ESCAPED}[[:space:]]/s/^# *//" /etc/locale.gen

    # Verify the locale is available before generating
    if ! grep -Eq "^[[:space:]]*${LOCALE_ESCAPED}[[:space:]]" /etc/locale.gen; then
        echo "Error: Locale '${LOCALE}' not found in /etc/locale.gen. Please use a supported locale." >&2
        exit 1
    fi

    locale-gen

    export LANG="$LOCALE"
    export LANGUAGE="$LOCALE"
    export LC_ALL="$LOCALE"
fi

# Ensure the application data directory exists and is writable by appuser
mkdir -p /app/data
chown appuser:appuser /app/data
exec gosu appuser python main.py
