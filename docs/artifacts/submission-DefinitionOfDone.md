# Submission — Lab 2.1 (Part 2): Definition of Done for AstraNotes

**Project:** AstraNotes
**Lab:** Week 2.1 — Part 2
**Chosen Technical Path:** Python 3

The Definition of Done (DoD) below applies to every AstraNotes artifact — requirements, planning documents, UML, code, and tests. An artifact is not "done" until every applicable item is satisfied.

---

## Definition of Done

### A. Traces to a real objective

1. The artifact references at least one stable requirement ID (`FR-*`, `NFR-*`, `SEC-*`) from `submission-InitialRequirementSet.md` (or its refined successor).
2. If the artifact introduces new scope, the new scope has been added to the requirement set as a numbered ID first; "drive-by" scope is not allowed.

### B. Logic and design are explainable

3. I can explain the design choice and the rejected alternative in my own words, without referencing the AI.
4. The architecture remains MVC-consistent (NFR-2): the View does not import persistence or encryption; the Model does not import view-layer code.
5. Naming uses the locked vocabulary (`Note`, `SecureNote`, `NoteRepository`, `NoteService`, `EncryptionService`, `PluginManager`, `SyncService`). Any new name has been added to the Architecture Decision Log.

### C. Quality and realism are checked

6. AI-generated content has been read line-by-line, not skimmed.
7. The artifact has been compared against at least one prior artifact in the chain (Requirements ↔ Stories, Stories ↔ Backlog, UML ↔ Requirements, etc.) and contradictions have been resolved.
8. Edge cases relevant to the artifact have been listed (empty input, missing passphrase, corrupted file, sync conflict, plugin failure) and either handled or explicitly deferred with a `TODO` referencing a backlog item.

### D. Testing, traceability, or validation has been considered

9. For functional artifacts: at least one acceptance criterion is written in observable form (Given/When/Then or "the user shall be able to verify…").
10. For design artifacts: every major design element has a requirement ID it justifies. Elements without a requirement reason are removed or flagged.
11. For code artifacts: a unit or integration test exists, or a written walkthrough demonstrates the artifact would behave correctly on the named edge cases.

### E. Security, privacy, and governance have not been ignored

12. SEC-1 (encryption at rest) is preserved — no SecureNote plaintext leaks into logs, files, or prints.
13. SEC-3 (dependency hygiene) is preserved — any new third-party package is pinned and justified in writing.
14. SEC-4 (audit log) is preserved — create / edit / delete / sync events are still recorded.
15. The artifact does not weaken privacy of private notes for convenience.

### F. AI use is honest and refined

16. The artifact has a "How AI helped" note that names what was kept, refined, or rejected.
17. The artifact does not contain text I cannot defend.

### G. The artifact deserves to move forward

18. A retrospective check: would I be willing to defend this artifact in the Mid-Term or Final technical review? If not, return it to In Progress.

---

## How this DoD applies right now (test against current AstraNotes work)

- **Would this DoD accept my current AI-generated work yet?** Not without revision. My first AI-drafted requirement list violated DoD #1 (no IDs), #5 (vague naming like "the cloud thing"), and #16 (no AI-use note). Refining against this DoD produced `submission-InitialRequirementSet.md`.
- **Which workflow gap would create confusion later if I do not fix it now?** The trace-to-ID rule (DoD #1, #10) is the gap that would silently break Week 5 traceability. Catching it now is cheap; catching it in Week 5 means rewriting four upstream artifacts.

---

## Reflection

This Definition of Done is deliberately blunt about AI: items #3, #6, #16, and #17 exist because the failure mode of an AI-native workflow is not "the AI wrote bad code" but "the student accepted plausible-looking output without thinking." Items #1 and #10 (traceability) are the spine — they are what will let the Week 5 traceability matrix actually be evidence-based instead of guesswork. Items #12–#15 are the non-negotiables that protect AstraNotes' identity as a privacy-respecting tool, not a generic note app.

---

## How AI helped

I asked Copilot Chat for a generic agile DoD checklist and used it as a sanity check, not as a draft. About half of its items (formatting, lint, code review) were not applicable to documentation artifacts; I dropped those. The AI did not propose anything in section F (AI use) — that section is mine and is the one most specific to this course. I kept its phrasing of the traceability and edge-case items because they were already concrete.
