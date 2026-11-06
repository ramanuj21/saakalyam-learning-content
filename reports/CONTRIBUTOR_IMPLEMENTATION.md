# Contributor identity, attribution and review — implementation evidence

Implemented locally on 6 November 2026 in `codex/contributor-identity`, based on `6c4fd389f2bf2a57e2e4636748187f7d2eed78c2`. The owner separately authorised committing and pushing this implementation branch. The public main branch and frozen initial tooling release are unchanged. No application files, source corpus, real credits, rights grants or reviewer appointments were modified.

## Implemented model

| Area | Executable behaviour |
| --- | --- |
| Agent | [Agent schema](../schemas/0.1.0/common/agent.schema.json): permanent UUID/common envelope, person/organisation/legacy pseudonym, nonblank public display name, optional GitHub/ORCID identifiers and safe HTTPS profile links. New Agents use UUIDv4; base checks distinguish legacy v5 continuity. Rename retains identity with increased revision; equal names do not merge Agents. |
| Attribution | [Common schema](../schemas/0.1.0/common/common.schema.json): existing Agent/role/status/evidence, optional note/scope, explicit unknown role with no Agent and required explanation. Duplicate Agent/role pairs fail; multiple different roles are allowed. Base-commit checks preserve prior credits; exceptional corrections need previous revision, reason and pinned evidence under provenance. |
| Roles | author, contributor, translator, transcriber, editor, commentator, annotator, curator, legacy reviewer, adapter, creator, narrator, producer. No role is compulsory merely because it exists. |
| Review | [Review schema](../schemas/0.1.0/publishing/review-record.schema.json): exact target revision/SHA-256, exact reviewer Agent revision, controlled category/type/role, whole-record/field scope, timestamp, outcome, rationale, dependency/evidence pins, limitations, unresolved issues and conflicts. Categories distinguish Sanskrit/domain, source fidelity, pedagogy, editorial, rights and technical checks. Outcomes: approved, changes requested, rejected, disputed, unable to determine. |
| Independent approval | Exact bytes/dependencies, appointed independent reviewer, category match, whole-record scope, no unresolved issue/conflict and latest eligible instant. Tied disagreement stays pending. A technical check never supplies Sanskrit, pedagogical or rights approval. |
| Earlier reviews | Historical editorial target/reviewer/dependency JSON may resolve from exact local Git blobs. They remain historical for successor content; missing history never substitutes current/main. Ordinary content/answer authoring pins remain strict. Archive reports instead use exact archived members/defaults, schema/policy files and digests without Git. |
| Submitter | [Workflow schema](../schemas/0.1.0/publishing/workflow-record.schema.json): optional submission Agent/ref, public context URI and commit SHA, independent of content attribution and review. Git author/committer identities stay in Git; the tools do not read their names/emails or infer credits. |
| Public/private policy | Closed public records, public Agent report whitelist, recognisable contact-value rejection, input-free schema diagnostics, report privacy checks and publication audit. No private contact facility, backend, OAuth, legal-name requirement or email collection. Public Git history remains visible and needs contributor privacy configuration. |
| Reports | [Offline generator](../validation/attribution.py): deterministic JSON and readable Markdown, safe labels, full credits/uncertainty, reviews with applicability and qualification, separate submitters, source credit/provenance and rights notices. No GitHub API. New tooling manifests pin `attribution.json` path/format/hash; verification recomputes the projection. Existing manifests without this additive field still verify. |

The full policy/field guide is [Contributor identity](../docs/CONTRIBUTOR_IDENTITY.md). [ADR 001](../docs/adr/001-contributor-identity.md) distinguishes existing Phase 8.1 proposals from implemented decisions. The authoritative application design documents were consulted and not changed.

## Report example

[Current safe report](contributor-attribution-example.md) and [lossless JSON](contributor-attribution-example.json) are generated from the eight unchanged real metadata records. Four Resource/MediaAsset rows retain the existing curator `ramanuj21`; author information is not recorded, no reviews/submissions are invented, and source reproduction rights remain unknown. Source credit is preserved literally rather than converted into an unverified author. Synthetic tests separately demonstrate authors, translators, editors, organisations, pseudonyms, unknown credits and exact reviewers.

```sh
python -m validation attribution-report --output /tmp/attribution.json
python -m validation attribution-report --format markdown --output /tmp/attribution.md
python -m validation attribution-report --release /tmp/exact-archive --output /tmp/release-attribution.json
```

Preserve the JSON report and original manifest with downstream exports. Markdown is a reading view. Reports are not rights grants or learner-eligibility certificates. Tooling archives contain no content members and therefore have an empty content report with manifest notices.

## Executed verification

| Check | Actual result |
| --- | --- |
| Full unit suite | `python -m unittest discover -s tests -q`: **97 passed**, zero failures/errors/skips. This is 63 existing tests plus 34 focused identity/privacy/report cases, with additional vocabulary/outcome subcases. |
| Current authoring validation and explicit base-commit check | Eight unchanged metadata records, **0 errors / 23 publication warnings**. |
| Current learner-release gate | **25 expected errors**, no release generated. Rights, reviews, governance and current-restriction trust remain blocking. |
| Offline/public/syntax checks | Public-file audit passed; Python compilation passed using a temporary bytecode-cache path; `git diff --check` passed. No new dependency was needed. |
| Determinism and archive integrity | Current JSON reports reproduce byte-for-byte. Synthetic tests verify exact release report resolution, pinned historical reviewer profiles, changed-policy/member rejection, report hash and recomputed-projection tampering checks. An independent checkout also ran the full suite and reproduced complete tooling archives; see the final verification note below. |
| Prior tooling release | `.local/tooling-release` verifies as the unchanged `0.1.0-tooling.1` archive using its own pinned schema/files. |
| Preservation | Hash comparison: 28 protected repository files unchanged, including real data, original fixtures, dependency/authority registry, inventory, frozen release and all unrelated domain schemas. All 1,284 application baseline files unchanged. No questions or source media were imported. |

Required scenario coverage in [test_identity.py](../tests/test_identity.py):

1. Author plus editor retains both credits.
2. Multiple contribution roles for one/different Agents remain distinct.
3. Pseudonymous contributor uses a public identity without legal/contact fields.
4. Organisation is a valid Agent, including equal display names without identity merging.
5. Unknown author has an explicit limitation and no fabricated Agent.
6. Adaptation preserves original author, source/input identity and translator.
7. Corrections retain author/translator, add editor, increase revision; unsupported credit removal fails.
8. Review binds exact revision/digest/dependencies; tampering fails.
9. New content revision retains old review history without inheriting applicability.
10. Private email/contact fields/values fail, without input leakage in diagnostics.
11. Repository submitter differs from original author and supplies no review approval.
12. Offline reports contain only public structured information and reproduce exactly.

Additional tests cover invalid Agent kind/name/refs, new v5 Agent rejection, identifier duplicates, unsafe public links, all six review categories/five outcomes, legacy category mapping, exact old reviewer names, conflicts, field scope, unresolved issues, timezone/tied decisions, report escaping, private notices/labels, policy/member integrity and pinned report verification. CI now repeats deterministic report generation and compilation alongside tests, validation, PR-base checks and audit. These results are local and independent-checkout evidence; no remote CI result is claimed for this implementation branch.

## Migration compatibility and remaining decisions

[Pravesha attribution mapping](PRAVESHA_ATTRIBUTION_MAPPING.md) defines the next migration's known author, source organisation, unknown author, imported legacy, retained/new credit, reviewer and uncertain-provenance rules. Preserve original source keys/IDs, evaluator evidence and uncertainty in an explicit reviewed identity ledger before reordering/importing. Do not make Saakalyam, the host or migration operator the author by default. No learner state is mapped. The eight excluded questions remain excluded.

That mapping is documentation-only preparation: the ledger, human identity reconciliation and migration itself have not been executed. Per-item authorship/consent, source edition/locator, rights for reproduce/redistribute/adapt, appointed reviewers and admitted knowledge/answer evidence remain unavailable or unresolved.

Owner/legal decisions still required: licence map and submission terms, public draft visibility, named qualified review authorities/minimums/conflicts/appeals, safe permission/contact-record handling, source-specific rights clearance, external canonical-package admission and current-restriction trust. No DCO/CLA, copyright transfer, blanket content licence, appointment or publication promise has been adopted.

Recommended next task: resolve the prerequisite rights/submission/reviewer decisions, then prepare a reviewed identity/provenance/attribution ledger and one small disclosure-cleared Pravesha sample with exact answer/knowledge dependencies. Validate that bounded sample before considering bulk migration. Frontend integration and learner delivery remain separately authorised work.

## Independent-checkout verification

A fresh temporary copy (without repository history, ignored state or application dependencies) passed all 97 tests and its publication audit. Two tooling archives built from one frozen temporary test commit each contained 71 files with identical hashes. Both verified, and regenerating each release attribution report reproduced the stored report exactly. This exercised standalone operation using only the pinned installed Python dependencies; it did not contact GitHub, fetch source media or access the application. The temporary verification commit is test evidence only, not a commit in this repository.

## Files changed

- [.github/ISSUE_TEMPLATE/new-question.md](../.github/ISSUE_TEMPLATE/new-question.md)
- [.github/ISSUE_TEMPLATE/new-resource.md](../.github/ISSUE_TEMPLATE/new-resource.md)
- [.github/ISSUE_TEMPLATE/question-correction.md](../.github/ISSUE_TEMPLATE/question-correction.md)
- [.github/ISSUE_TEMPLATE/review-metadata.md](../.github/ISSUE_TEMPLATE/review-metadata.md)
- [.github/PULL_REQUEST_TEMPLATE.md](../.github/PULL_REQUEST_TEMPLATE.md)
- [.github/workflows/validate.yml](../.github/workflows/validate.yml)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
- [GOVERNANCE.md](../GOVERNANCE.md)
- [README.md](../README.md)
- [docs/CONTRACTS.md](../docs/CONTRACTS.md)
- [docs/CONTRIBUTOR_IDENTITY.md](../docs/CONTRIBUTOR_IDENTITY.md)
- [docs/adr/001-contributor-identity.md](../docs/adr/001-contributor-identity.md)
- [policies/review.md](../policies/review.md)
- [reports/CONTRIBUTOR_IMPLEMENTATION.md](../reports/CONTRIBUTOR_IMPLEMENTATION.md)
- [reports/PRAVESHA_ATTRIBUTION_MAPPING.md](../reports/PRAVESHA_ATTRIBUTION_MAPPING.md)
- [reports/VALIDATION.md](../reports/VALIDATION.md)
- [reports/contributor-attribution-example.json](../reports/contributor-attribution-example.json)
- [reports/contributor-attribution-example.md](../reports/contributor-attribution-example.md)
- [schemas/0.1.0/common/agent.schema.json](../schemas/0.1.0/common/agent.schema.json)
- [schemas/0.1.0/common/common.schema.json](../schemas/0.1.0/common/common.schema.json)
- [schemas/0.1.0/publishing/manifest.schema.json](../schemas/0.1.0/publishing/manifest.schema.json)
- [schemas/0.1.0/publishing/registry.schema.json](../schemas/0.1.0/publishing/registry.schema.json)
- [schemas/0.1.0/publishing/review-record.schema.json](../schemas/0.1.0/publishing/review-record.schema.json)
- [schemas/0.1.0/publishing/workflow-record.schema.json](../schemas/0.1.0/publishing/workflow-record.schema.json)
- [tests/test_identity.py](../tests/test_identity.py)
- [validation/attribution.py](../validation/attribution.py)
- [validation/audit_publication.py](../validation/audit_publication.py)
- [validation/core.py](../validation/core.py)
- [validation/identity.py](../validation/identity.py)
