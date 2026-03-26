#!/bin/sh
# Docker health check: verify main.py Python process is running.
# Iterates /proc entries with error handling to avoid race-condition failures.
python - <<'EOF'
import os, sys

found = False
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    try:
        with open(f"/proc/{pid}/cmdline", "rb") as f:
            if b"main.py" in f.read():
                found = True
                break
    except OSError:
        pass  # process may have exited between listing and reading

sys.exit(0 if found else 1)
EOF
