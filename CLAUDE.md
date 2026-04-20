# Free Games Notifier — Claude Instructions

## Issue & Project Board Workflow

When working on an issue, follow this lifecycle:

1. **Al empezar a trabajar** en un issue:
   - Añadir label `in-progress` al issue → el GitHub Action lo mueve a "In progress" en el board automáticamente.

2. **Al crear un PR**:
   - Incluir `Closes #N` (o `Fixes #N`) en el cuerpo del PR para que el Action detecte el issue vinculado y lo mueva a "In review".
   - El formato del título del PR debe incluir `(#N)` para referencia, pero lo que mueve el board es `Closes #N` en el body.

3. **Al hacer merge del PR**:
   - El Action mueve automáticamente el issue a "Done".

### Project Board (free-games-notifier)
- Project number: 2
- Owner: JulioMoralesB
- Status field ID: `PVTSSF_lAHOBgvcQc4BR2svzg_jvuU`
- Columns: Backlog → Ready → In progress → In review → Done
