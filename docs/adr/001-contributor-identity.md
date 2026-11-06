# ADR 001 — Public identity, credit and scoped reviews

Status: implemented in the bounded learning-content repository on 6 November 2026. This records software decisions, not approval of pending Phase 8.1 legal/governance policy.

## Existing proposal and observed gaps

The application's Phase 8.1 design package, DOMAIN_PROVENANCE_IDENTITY, REPOSITORY_GOVERNANCE_LICENSING, SCHEMAS_VALIDATION, RELATIONSHIPS_LEARNING and CONTENT_MODEL propose stable Agents, role credit, preservation of authorship, exact independent review, private-contact minimisation and Git as complementary evidence. They remain authoritative in their respective ownership areas and are unchanged.

The initial learning 0.1.0 implementation already had Agents (`person`, `organisation`, `pseudonym`), nine credit roles, attribution status/evidence, exact reviewer/digest/dependency fields, rights layers and a disabled learner-release gate. However, `unknown` credit still required an Agent; review categories/outcomes did not cover the requested distinctions; no explicit submission identity or attribution report existed. Review resolution only accepted current revisions, preventing retention of old decisions after a target update. Latest approval used string timestamps/UUID ties.

## Smallest bounded corrections

- Reuse Agent UUIDs/envelope and existing role arrays. Add optional qualification and media/adaptation roles; allow explicit unknown credit without an Agent. No fictional “Unknown Author”.
- Put exceptional attribution-correction evidence under common provenance. PR-base checks preserve prior credit. Question, resource, representation and other unrelated domain schema files remain byte-identical; shared metadata contract extends additively.
- Retain `reviewScope` as category for compatibility; add optional explicit type/role, bounded scope, evidence/limitations/conflicts and two uncertainty outcomes. Map legacy category-only reviews transparently. Existing metadata still validates.
- Preserve independent review authority and all rights/release gates. Approval uses exact bytes/dependencies and actual latest instants; tied disagreement, field-only approval and unresolved issues cannot grant whole-record approval.
- Resolve historical editorial targets/reviewer profiles only from exact local structured Git blobs. Content/answer refs keep their existing strict semantics. Offline release reports instead resolve only exact archived members/defaults and hash-pinned schema/policy files.
- Optional workflow submission metadata distinguishes PR submitter from author/reviewer. No Git author/email extraction, GitHub API, OAuth or new private identity system.
- Whitelist public Agent report fields, reject contact values, keep diagnostics free of input values, and generate deterministic JSON/Markdown reports. New archives bind attribution report digest; the frozen old tooling version is unchanged.

The current authoring schema bundle remains 0.1.0 because these are additive fields/vocabulary plus stricter correctness/privacy checks over unreleased authoring data. Immutable prior releases pin their own schema/code bytes and remain reproducible. Consumers must pin a commit/archive; stricter validation may reject previously accepted unsafe metadata. A future externally consumed incompatible contract requires explicit version review.

## Remaining approval

No appointments, rights grants, public draft intake, DCO/CLA, copyright transfer, blanket licence or private permission/contact process is adopted. Those decisions remain with the owner and qualified/legal reviewers. No Sanskrit question/source/media migration, application change or learner release occurred. Field-scope review is representable; current publication gates conservatively require whole-record independent approval. Expanding scope combination, external identifier schemes or consented affiliation fields needs a later bounded contract decision.
