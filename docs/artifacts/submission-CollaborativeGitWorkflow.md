# Submission — Lab 8.1: AstraNotes Collaborative Git Workflow

**Project:** AstraNotes
**Lab:** Week 8.1
**Chosen Technical Path:** Python 3
**Format:** Individual simulation with two branches (per the brief's allowance)

This submission builds directly on:

- `submission-ConnectingDesignToPrototype.md` (the Week 6 `astranotes/` package and the files the branches touch)
- `submission-ShiftLeftTesting.md` (the Week 7.2 test set — Branch B builds on it)
- `submission-InitialRequirementSet.md` (`FR-*`, `NFR-*`, `SEC-*` IDs cited in commit messages and the PR summary)

---

## §1. Scenario

Two simultaneous branches off `main`, deliberately chosen so they touch overlapping ground and force a real review conversation. This is the deck-endorsed "search improvement vs test cleanup" demo.

| | Branch A | Branch B |
|---|---|---|
| **Name** | `feature/search-fts5` | `test/title-validation` |
| **Purpose** | Implement Slice C (FR-8 search) using the SQLite FTS5 virtual table already created in `LocalSQLiteRepository._init_schema` | Tighten the FR-1 validation tests outlined in Week 7.2 and remove the inline empty-title check by extracting `is_title_empty()` |
| **Touches** | `astranotes/repository/sqlite_repo.py`, `astranotes/services/note_service.py`, `astranotes/view/cli.py`, **and** `astranotes/services/validation.py` (adds `validate_query`) | `astranotes/services/validation.py` (extracts helper), `astranotes/tests/test_validation_service.py` |
| **Requirements** | FR-8, NFR-1, SEC-1 (locked SecureNote bodies excluded), SEC-4 (audit log entry on search? deferred) | FR-1, SEC-2 |

Both branches touch `astranotes/services/validation.py`. Branch A appends a new `validate_query()` function; Branch B refactors the inline `if not title.strip()` into an `is_title_empty()` helper and updates `validate()` to call it. The shared-file overlap is the whole pedagogical point: it forces a sequencing decision rather than a mechanical merge.

---

## §2. Collaboration Log

Single-developer simulation; the "two seats" are me wearing the contributor hat on each branch and the reviewer hat on the opposite branch. All times Pacific.

| When | Where | What happened |
|---|---|---|
| 2026-05-26 09:00 | `main` | Pulled, all Week 7.2 tests green. Tagged `pre-week8`. |
| 2026-05-26 09:05 | `feature/search-fts5` | Branch created from `main`. |
| 2026-05-26 09:15 | `test/title-validation` | Branch created from the same `main` commit, *before* Branch A's first commit, so neither branch is downstream of the other. |
| 2026-05-26 11:30 | `feature/search-fts5` | Three commits landed (see §4). Local test run green. |
| 2026-05-26 13:00 | `test/title-validation` | Three commits landed (see §4). Local test run green. |
| 2026-05-26 14:00 | GitHub | PR-A opened against `main`. |
| 2026-05-26 15:30 | GitHub | PR-B opened against `main`. |
| 2026-05-26 16:00 | Reviewer-hat | PR-A reviewed — surfaced shared-file overlap with PR-B (see §6). |
| 2026-05-26 16:20 | GitHub | PR-A status: **changes requested**. PR-B status: ready to merge. |
| 2026-05-26 16:30 | `main` | PR-B merged. PR-A held back pending rebase. |

---

## §3. Branch and PR Workflow Summary

Both branches were short-lived, scoped to one idea each, and rooted off the same `main` commit. PR-A introduces a feature (search) and PR-B tightens existing tests (title validation). Each branch has three commits with single-line action-verb messages following the deck's "good commit" format. PRs were opened independently — neither branch was waiting on the other when work started — but the review surfaced that both branches modify `astranotes/services/validation.py`, so the smaller and lower-risk branch (B) was merged first and the larger branch (A) was held back to rebase on the new `main` and split the cross-cutting commit. This sequencing is the deck's "one branch, one purpose" rule applied at merge time: PR-A's `search:` work is right, but the `validation:` commit inside it does not belong with the search feature.

---

## §4. Commit Log per Branch

### Branch A — `feature/search-fts5`

```
8a91c2f  search: add FTS5-backed query method on LocalSQLiteRepository
3d24aab  search: surface search() on NoteService and add CLI dispatch
0c7e1d5  validation: accept empty search query as list-all
```

### Branch B — `test/title-validation`

```
b612ef9  test: add empty-title rejection cases (parametrize over whitespace)
72c8a01  test: parametrize title length boundary at 200 chars
1f4d3bc  refactor: extract is_title_empty() helper in ValidationService
```

Every message is the deck's exact style — *prefix : verb-led summary* — and every commit could be reviewed independently. The deliberate weakness on Branch A is commit `0c7e1d5`: its prefix is `validation:` but the work belongs with `search:`. That mislabel is what the AI critique caught (see §9).

---

## §5. PR Summary — Branch A (the one I wrote)

> **Title:** `feat(search): FR-8 search slice with FTS5 ranking`

**Change:**
Add `LocalSQLiteRepository.search(query: str) -> list[tuple[...]]` backed by the existing `notes_fts` FTS5 virtual table. Surface a `NoteService.search()` method that filters out locked SecureNote bodies per SEC-1 before returning to the View. Wire the CLI `search <query>` subcommand to call it.

**Why:**
Closes Slice C from the backlog (US-3, FR-8). The FTS5 table was created in Week 6 (S0-9, S0-11) but had no consumer; this PR makes the index earn its existence. Ranking is by `updated_at DESC` — the FR-8 acceptance criterion is "results returned by recency." The body of any SecureNote is excluded from the result set even when the query would match its plaintext (SEC-1 — plaintext is never indexed because the FTS5 table stores `body`, and SecureNote rows store `encrypted_body` only).

**Risks:**
1. **NFR-1 not measured here.** The 10,000-note p95 latency target is the S0-11 spike, not this PR. This PR adds the *path*; the perf measurement is a follow-up.
2. **Search-query validation is the wrong shape.** Commit `0c7e1d5` added an `validate_query()` to `astranotes/services/validation.py`. That file is also being edited on `test/title-validation` (Branch B's refactor). Merge order matters: if A merges first, B will need to rebase; if B merges first, A's `validate_query()` should land in a follow-up PR scoped to validation only.
3. **No audit-log entry on search yet.** SEC-4 covers create/edit/delete/sync/security events; a future scope decision (separate PR) is whether searches are audit-worthy.

**Evidence:**
- T-5 from `submission-ShiftLeftTesting.md` was promoted from outline to live test in `tests/test_search.py`. It currently asserts the deliberately-weak version (membership + ordering); the Week 9 Test Improvement Log strengthens it.
- All Week 7.2 tests (T-1..T-4) still pass on this branch.
- Manual run: `python -m astranotes search alpha` returns 3 results out of 7 seeded notes; the SecureNote whose plaintext body contains "alpha" is correctly excluded.

---

## §6. Review Feedback Example

Posted on PR-A as an inline comment on the diff of `astranotes/services/validation.py`:

> **Request changes** — this PR mixes two changes that belong in separate branches.
>
> Branch A's third commit (`0c7e1d5 validation: accept empty search query as list-all`) adds `validate_query()` to `validation.py`. Branch B (`test/title-validation`) is concurrently refactoring `is_title_empty()` out of the same file. Either of those is fine in isolation; together they create a shared-file conflict and a reviewer has to hold two intents in their head.
>
> Recommendation: drop commit `0c7e1d5` from this PR. Merge B first; rebase A onto the new `main`; re-add `validate_query()` in a **separate** PR named `feat(validation): query validator for FR-8 search`. The search path itself (commits `8a91c2f` and `3d24aab`) can merge cleanly here.
>
> This is the "one branch, one purpose" rule from the deck — the search slice and the validator refactor are two purposes.

**Decision:** changes requested. **Reason:** scope contamination on a shared file; not a correctness issue.

This is the kind of feedback the deck's "human review" column lists: *Does it fit the architecture? Is the scope clear? Is it safe to merge?* The answer here is "yes to architecture, no to scope, so not yet safe."

---

## §7. Merge or Merge-Readiness Note

**PR-B (test/title-validation): merged.** Three small commits, all green, no shared-file conflict after the decision to hold PR-A. The DoD checklist (`submission-DefinitionOfDone.md`) was walked: DoD #1 (cites FR-1, SEC-2), #5 (`ValidationService`, `is_title_empty` — names match the locked vocabulary), #11 (tests exist and pass), #16 (PR-B has an AI-use note in its description). Merge commit message: `Merge PR #18: test: tighten title validation and extract is_title_empty()`.

**PR-A (feature/search-fts5): not merged.** The search slice itself is correct, but it carries one cross-cutting commit that belongs elsewhere. After PR-B is on `main`, the contributor will:
1. `git rebase origin/main` on Branch A.
2. `git rebase -i HEAD~3` and drop commit `0c7e1d5`.
3. Open a follow-up PR `feat(validation): query validator for FR-8 search` containing just that commit.
4. Re-request review on PR-A.

This is *merge-readiness discipline*: the work is good; the packaging is wrong.

---

## §8. Refactor Note

The refactor that landed in PR-B is the extraction of `is_title_empty(title: str) -> bool` out of `ValidationService.validate`. The old code inlined `if not title or not title.strip()` inside `validate()`; the new code calls `is_title_empty(note.title)`. This is a five-line refactor and it matters for collaboration: every future title rule (max length, reserved characters, locale-aware whitespace) now has a single function to extend, and the validation tests in `test_validation_service.py` can parametrize over `is_title_empty` directly without spinning up a full `Note`. The deck's framing — *"good refactors make the next PR smaller"* — fits exactly: the follow-up `feat(validation): query validator` PR is now a one-function addition instead of an awkward edit of an already-busy `validate()` method.

Next refactor target (not in this PR, scoped to Week 9): the search test in `tests/test_search.py` is still using the deliberately-weak ordering assertion. The Week 9 Test Improvement Log replaces that with a membership-plus-SEC-1-exclusion assertion.

---

## §9. How AI Helped

I used AI in three distinct roles, in the order the deck recommends — *draft, critique, summarize.* For each, what I kept, changed, or rejected:

**1. Drafting the PR-A "Risks" section.** Weaker prompt: *"write a risks section for this PR."* It produced a generic bulleted list ("breaking changes possible", "test coverage incomplete") that named nothing specific. Refined prompt: *"List the three concrete risks of this PR-A against the AstraNotes requirement IDs FR-8, NFR-1, SEC-1, SEC-4."* That produced something close to the version in §5, including the NFR-1 caveat I had not written down explicitly. **Kept** the three-bullet structure; **refined** the NFR-1 wording to point at S0-11; **added** the shared-file risk myself because AI was looking at PR-A in isolation and could not see Branch B.

**2. Critiquing the commit log.** Prompt: *"Read these three Branch A commits and tell me whether the prefixes match the diffs."* AI flagged that `0c7e1d5 validation: …` was misleading because the work was driven by the search feature — that's the catch that became §6's review feedback. **Kept and acted on** that catch. It would have been easy to merge that commit under its own prefix and not notice the scope problem until later.

**3. Summarizing the diff for the reviewer.** Prompt: *"Summarize PR-A in three sentences for a reviewer who has not read the diff."* The summary it produced was accurate but ended with *"All tests pass; safe to merge."* I **rejected** that line — the deck's exact warning is *"AI review is not final approval"*, and the merge-readiness decision is mine. The shared-file overlap is exactly the kind of thing AI cannot see (it does not know Branch B exists), so its conclusion that the PR was safe to merge was confidently wrong.

The decision to hold PR-A and merge PR-B first is mine; AI surfaced the inputs that made the decision obvious.
