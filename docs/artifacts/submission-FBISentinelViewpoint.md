# Submission — FBI Sentinel Case Study Viewpoint

**Format:** 1-Page Viewpoint (BLUF)
**Course:** CSEN 296B-2

---

**Bottom Line Up Front.** Sentinel's ~$400M loss was a process failure, not a coding failure. Big-Design-Up-Front Waterfall plus a contractor-controlled feedback loop guaranteed that real engineering risk could not be discovered until too late. An AI-native SDLC, used as a discipline rather than a code generator, would have surfaced those risks in the first six months.

**1. The BDUF Fallacy — A Point of No Return.** Lockheed Martin's contract locked scope and architecture before any usable feature existed. The first three years were dominated by SDDs, ICDs, and component specs; agents in the field saw nothing they could exercise. By the time the FBI began acceptance work, roughly $170M had been spent and Phase 1 was already failing. Because Waterfall sequences requirements → design → code → test as non-overlapping phases, every late defect forced rework into phases already "signed off," and Year-1 architectural choices (SOA backbone, case-management data model) could not be revised without invalidating downstream artifacts. The methodology made it cheaper on paper to keep building than to admit the foundation was wrong — which is the structural reason the $400M was spent before any usable feature shipped.

**2. The Feedback Vacuum — Where "Trust but Verify" Failed.** The contract made Lockheed both the producer of work products and the de-facto judge of their readiness. The FBI relied on Lockheed-authored status reports and milestone reviews that measured *artifact completeness* rather than *working software*. When Aerospace Corporation's IV&V eventually surfaced thousands of defects and missing requirements, the gap between reported and actual progress was already enormous. The verification step that should have run quarterly was instead an audit conducted years in. Any process that separates the people who build from the people who can call "stop" by years and millions of dollars produces exactly this failure.

**3. The Agentic Alternative — Restructuring the First 6 Months.** As Lead Architect today with AI-native SDLC tooling I would replace BDUF with a thin-slice, evidence-driven plan:

- **Month 1.** AI-assisted requirements deconstruction: chain-of-thought prompting on stated objectives to surface ambiguity, generate edge cases, and lock a stable requirement-ID baseline so every later artifact traces back. AI-driven hallucination review flags unsupported library/protocol claims.
- **Months 2–3.** Vertical-slice MVP — one end-to-end case-management workflow, deployed to one field office, demoed weekly. The point is the closed feedback loop with a real user who can call "stop"; this alone defeats Pillar 2.
- **Months 4–5.** A live requirements-to-design-to-test traceability matrix (the artifact assigned in Week 5 of this course) maintained by AI and verified by engineers. Any design element without a requirement reason is removed before it accretes mass.
- **Month 6.** Architectural commitment review. Only after five months of working software in front of real users do we lock in SOA / data-model / vendor decisions — on evidence, not estimates.

Total six-month spend under this plan is a small fraction of $170M, and at the end either working software exists with a closed feedback loop, or the team has discovered cheaply that the chosen architecture cannot meet the mission. That is the answer Sentinel did not get until $400M had been spent.

**Verdict.** Sentinel was a process failure that an AI-native SDLC — disciplined around traceability and weekly working-software demos — would have made structurally impossible.

*How AI helped: Copilot Chat drafted a first version of the Agentic Alternative. I rejected its framing of the failure as "poor agile adoption" — Sentinel was a Waterfall program, and the lesson is about Waterfall + feedback isolation. The BLUF structure and the six-month plan are mine.*
