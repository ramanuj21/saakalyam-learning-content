# Pravesha attribution mapping for the next migration

Preparation only; none of the 1,513 available questions or eight excluded records was imported. The [existing inventory](MIGRATION_READINESS.md) remains the observed source baseline. No item-level authorship/permission is established by this implementation.

| Available evidence | Future population rule |
| --- | --- |
| Known original individual author | Reconcile an existing Agent by evidence, not name alone; otherwise allocate UUIDv4 with consented public display name. Preserve author role/status and exact evidence refs. |
| Known organisation as actual author/contributor | Use organisation Agent only for an evidenced role. Do not turn a hosting/source organisation into the author. |
| Known source organisation; individual author absent | Retain source work/edition/locator and literal established source credit. Record unknown author without Agent when supported; organisation credit only when its contribution is established. |
| Legacy author unknown or incomplete | `author` with `attributionStatus: unknown`, nonblank limitation note, no Agent. Traditional/disputed named attribution uses its established Agent plus that uncertainty/evidence. Missing evidence is visible and blocks eligibility. |
| Imported legacy question | `origin: imported`, pinned original inputs and method; retain source key, original question/evaluator IDs, source revision/digest and attribution status in a reviewed migration ledger. Import operator is submission evidence only. |
| Existing structured credits | Copy the exact Agent/role/status/qualification and evidence; reconcile IDs explicitly. Do not drop credits when representations/evaluation are reorganised. |
| New adaptation / translation | Preserve original author/source, add only evidenced adapter/translator/editor credit and pin inputs; map translation to `origin: derived` plus method and translator role, as there is no new translated-origin vocabulary. |
| Punctuation/correction after import | Increment affected revision; preserve author/translator, add editor/contributor only for actual work. Exceptional mistaken-credit correction needs prior revision, reason and pinned evidence. |
| Reviewer | Separate exact revision/digest ReviewRecord with type/role/scope/outcome/limitations and independent appointment. Migration does not create approvals. |
| Repository submitter / Git committer | Optional WorkflowRecord submission Agent/context/SHA. Git identities remain complementary history; neither populates every question's contributor array. |
| Missing or uncertain provenance | Keep explicit public limitation and empty unresolved source refs until evidence exists. Do not invent a source edition, author, licence, answer dependency or Sanskrit judgement. |

Freeze a source-key → retained/candidate UUID ledger before reordering or bulk import. Retain reviewed existing v4/v5 question identities; allocate new unrelated identities randomly. Map prompt/options/accepted variants to exact representations without normalising Sanskrit bytes. Preserve evaluator identity/digest in migration evidence even though this repository's evaluation is inline. Source associations and source permission remain different facts.

The ledger format and human reconciliation are preparation for the next task, not a new ad hoc field on every Question. Build one small disclosure-cleared sample with all legacy credits and uncertain facts accounted for before scaling. Compare before/after credit sets and validate against the explicit base commit; retain all eight exclusions. Reviewers must check intended roles, public attribution consent, source independence, rights uses and required knowledge/answer dependencies.

Unavailable today: reliable per-question original authorship, consent/identity reconciliation, complete consulted edition/locator evidence, source-specific reproduction/redistribution/adaptation grants, qualified reviewer appointments and fully admitted external canonical dependencies. Do not infer these from Saakalyam branding, public hosting, importer identity or source-key recovery. Resolve licence/submission/draft-visibility and permission handling decisions before publishing any actual question sample.
