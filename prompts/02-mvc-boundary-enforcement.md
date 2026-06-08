# Session 02 — Enforcing the MVC boundary (NFR-2)

## Weaker prompt
> "Make sure the CLI doesn't import the database code."

Produced a code-review checklist ("remember not to import the repo in the view"). **
Rejected** as the primary mechanism — NFR-2 requires the violation to be *detected
automatically*, not left to discipline.

## Stronger prompt
> "NFR-2 requires that the View layer never imports `astranotes.repository` or
> `astranotes.services.encryption`, enforced automatically in CI. Give me (a) a ruff
> configuration that bans those imports, and (b) a small test that statically proves the
> View modules don't import them, independent of ruff."

## Kept
- ruff `flake8-tidy-imports.banned-api` entries in `pyproject.toml` with messages that
  cite the requirement, so a violation fails `ruff check` locally and in CI.
- `tests/test_mvc_boundary.py` parses each `view/*.py` with `ast` and asserts neither
  banned package is imported — a second, independent gate.
- A composition root (`app.py`) so the View receives a built `NoteService` and has no
  reason to import lower layers in the first place.

## Refined
- ruff's `TID` group also flags `TID252` (all relative imports). The codebase uses
  intra-package relative imports by convention, so I **narrowed** the rule to keep
  `TID251` (banned-api, the one NFR-2 needs) and ignore `TID252` — documented inline in
  `pyproject.toml`.

## Rejected
- A suggestion to merge services and repository into one module "to simplify imports."
  **Rejected**: collapsing the layers would erase the very boundary NFR-2 exists to
  protect.
