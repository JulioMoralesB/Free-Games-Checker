# Free Games Notifier — Claude Instructions

## Issue & PR workflow

- All PRs target `main` directly — there is no `QA` branch.
- Before writing any code: add the `in-progress` label to the issue.
- When opening the PR: include `Closes #N` in the PR body (not just the title) — the project board automation reads the body.
- On merge: the GitHub Action moves the issue to "Done" automatically.
- For a release-worthy merge: create an annotated tag `vX.Y.Z`, push it, and confirm the "Release" GitHub Actions workflow succeeds.

## Before committing

- Run the full test suite (`pytest tests/ -m "not integration and not production"`) and `ruff check .` — both must be clean.
- Review the README and `docs/` for staleness: new/removed env vars, changed setup steps, or new user-facing behavior must be reflected there before closing the issue.

## Language

All repo content — commit messages, PR titles/descriptions, code comments, documentation — must be in English, regardless of what language the conversation happens in.

## Project board (free-games-notifier)

- Project number: 2
- Owner: `JulioMoralesB`
- Status field ID: `PVTSSF_lAHOBgvcQc4BR2svzg_jvuU`
- Columns: Backlog → Ready → In progress → In review → Done
