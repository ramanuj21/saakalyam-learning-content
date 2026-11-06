# Governance and release authority

GitHub repository owner: `ramanuj21`, explicitly confirmed for this task. Repository administration is not proof of Sanskrit expertise, rights ownership or scholarly approval. No real reviewer appointments or content approvals are fabricated; `policies/registry.json` starts with an empty reviewer-authority list and learner releases disabled.

Responsibilities remain separate: contributors supply attributable, disclosure-safe evidence; subject reviewers check Sanskrit/source correctness; pedagogical reviewers check task/rubric suitability; editorial reviewers check clarity and metadata; rights reviewers assess exact grants/intended uses; schema maintainers review contract changes; release maintainers freeze dependency closure and notices. The owner must appoint qualified individuals and resolve conflicts of interest before their decisions can count. Required independent review cannot be self-certified by an author.

Draft → Review comes from workflow sidecars. Approved comes from authorised reviews of exact revision bytes and critical dependency pins. Published means selected membership in a specific eligible immutable release. Retired/withdrawn comes from a separate target-pinned record. A GitHub merge, green CI check or a filled title is none of these approvals.

Corrections retain source evidence and prior Git bytes. Increase revision for changed payloads, re-review changed dependencies, and use replacement/tombstone records rather than deleting accepted identities. A retirement/withdrawal excludes that revision and relevant dependants from learner release; it cannot promise remote erasure of Git/forks.

## Pending owner decisions

- Final database/content/schema/tooling licence map, submission terms and public Draft visibility clarification.
- Named independent scholarly, pedagogical, editorial and rights authorities, qualification evidence, conflict/appeal handling and escalation contacts.
- Source-specific rights compatibility, source identity reconciliation and public/private permission-record handling.
- External canonical-package admission and reference ownership closure.
- Current restriction/withdrawal trust, authentication, expiry/distribution, retention and dispute handling before learner delivery.

This task authorises public initial scaffolding and safe metadata, not these unresolved approvals. Do not amend the application’s authoritative Phase 8 documents to manufacture agreement.

## Identity and scoped review implementation

[Identity/review guide](docs/CONTRIBUTOR_IDENTITY.md) distinguishes content Agents, exact reviewer profiles, optional repository submitters and Git metadata. Agent identity is stable across display-name changes and supports people, organisations and pseudonyms. Unknown authorship has no fabricated Agent. Curator/hosting/submission credit is never substituted for original authorship or rights ownership.

Review categories now distinguish Sanskrit/domain, source fidelity, pedagogical, editorial, rights and technical checks. Conflicts must be disclosed; contributors/conflicted reviewers cannot approve required independent review. Non-approval observations can record a conflict and require independent review. Same-time eligible disagreement remains pending. Partial-scope approval and unresolved issues do not qualify the whole record. Earlier exact reviews remain historical after a content revision; a fresh target digest/dependency review is needed. Qualification, appointments, indirect conflicts, appeals and role-specific minimum reviewer counts still require owner decisions. The real registry is unchanged.

This increment implements metadata/privacy/reporting mechanics only. There is no private contact store/facility; public records must not contain private contact details. No submission terms, new licences, DCO/CLA, copyright transfer, draft-visibility decision or rights clearance is enacted. See [implementation ADR](docs/adr/001-contributor-identity.md).
