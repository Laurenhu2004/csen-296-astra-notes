# Definition of Done — AstraNotes

Every artifact (requirement, design element, code slice, test) is "Done" only when it
meets the criteria below. This is the same DoD developed in Week 2.1 and applied across
the whole traceability chain.

## A. Traces to a real objective
1. References at least one stable requirement ID (`FR-*` / `NFR-*` / `SEC-*`).
2. New scope gets a requirement ID first — no drive-by scope.

## B. Logic and design are explainable
3. The author can defend the design in their own words, without citing AI.
4. It stays MVC-consistent (NFR-2): the View reaches the system only via `NoteService`.
5. It uses the locked vocabulary: `Note`, `SecureNote`, `NoteRepository`, `NoteService`,
   `EncryptionService`, `VersionHistoryService`, `AuditLogService`, `PluginManager`,
   `SyncService`.

## C. Quality and realism checked
6. AI-generated content was read line-by-line, not skimmed.
7. It was compared against prior artifacts; contradictions were resolved.
8. Edge cases were listed (empty input, missing passphrase, corrupted file, sync
   conflict, plugin failure) and either handled or deferred with a noted TODO.

## D. Testing / traceability / validation considered
9. Functional behavior has acceptance criteria in Given/When/Then form.
10. Each major design element has a requirement ID justifying it.
11. Code has a unit/integration test, or a walkthrough demonstrating correctness.

## E. Security, privacy, governance not ignored
12. **SEC-1** preserved — no SecureNote plaintext in logs, files, or prints.
13. **SEC-3** preserved — new packages pinned and justified.
14. **SEC-4** preserved — create/edit/delete/restore/sync/security events audited.
15. Privacy is not weakened for convenience.

## F. AI use is honest and refined
16. A "how AI helped" note names what was kept, refined, or rejected.
17. No text the author cannot defend.

## G. Deserves to move forward
18. It would pass a mid-term or final technical review.
