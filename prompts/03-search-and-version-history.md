# Session 03 — Search + version history (FR-8 / NFR-1 / SEC-1 / FR-6)

## Weaker prompt
> "Add search to the notes app."

Produced `SELECT * FROM notes WHERE body LIKE '%' || ? || '%'`. **Rejected**: a `LIKE`
scan does not meet NFR-1 (< 100 ms p95 at 10k notes) and would happily match the
plaintext of notes — but it also wouldn't help us with SEC-1 reasoning.

## Stronger prompt
> "Implement FR-8 search using SQLite FTS5 so it meets NFR-1 at 10k notes, ranked by
> recency. Locked SecureNote bodies must not contribute to results (SEC-1). Also
> implement FR-6 version history as append-only with restore. Show the schema, the
> triggers that keep the FTS index in sync, and tests."

## Kept
- External-content FTS5 table `notes_fts` with `AFTER INSERT/UPDATE/DELETE` triggers
  mirroring `notes`.
- SecureNote bodies are stored **blank** in `notes.body`, so the FTS index never contains
  locked ciphertext — SEC-1 is satisfied at the storage layer, and the service filter is
  a second line of defense. Proven by `test_locked_secure_body_not_searchable`.
- Append-only `version_history`; `restore_version` appends a new entry rather than
  overwriting (`test_restore_appends_rather_than_overwrites`).
- A `tools/seed.py` generator + `tests/perf` spike that asserts the p95 budget (S0-11).

## Refined
- The AI stored only second-resolution ISO timestamps, which made "ranked by recency"
  non-deterministic when two notes were edited in the same second (a test caught this).
  **Fixed** by moving `now_iso()` to microsecond precision (still ISO 8601) and parsing
  with `datetime.fromisoformat`.
- Free-text queries were passed straight into `MATCH`, which crashes on FTS operator
  characters. **Refined** to quote each term and AND them, degrading to "no matches"
  rather than an exception (SEC-2).

## Rejected
- Implementing version history as line diffs (the requirement says `body_diff`).
  **Rejected for now** in favor of full snapshots — simpler, robust, and behaviorally
  identical for list/restore. Documented honestly in `docs/architecture.md` and
  `docs/traceability.md` rather than hidden.
