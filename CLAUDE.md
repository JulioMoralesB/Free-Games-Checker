# Free Games Notifier — Claude Instructions

## Issue & Project Board Workflow

When working on an issue, follow this lifecycle:

1. **When starting work** on an issue:
   - Add the `in-progress` label → the GitHub Action moves it to "In progress" on the board automatically.

2. **When creating a PR**:
   - Include `Closes #N` (or `Fixes #N`) in the PR body so the Action detects the linked issue and moves it to "In review".
   - The PR title should include `(#N)` for reference, but what triggers the board move is `Closes #N` in the body.

3. **When the PR is merged**:
   - The Action moves the issue to "Done" automatically.

### Project Board (free-games-notifier)
- Project number: 2
- Owner: JulioMoralesB
- Status field ID: `PVTSSF_lAHOBgvcQc4BR2svzg_jvuU`
- Columns: Backlog → Ready → In progress → In review → Done
