# Contributor identity, attribution and review

Implemented by the shared 0.1.0 contracts and offline validator. [ADR 001](adr/001-contributor-identity.md) records the bounded differences from the Phase 8.1 proposal. No contributor account, private contact store or scholarly approval service is implied.

## Four distinct identities

| Identity | Structured location | Meaning |
| --- | --- | --- |
| Content credit | `attributions[]` on the affected record | Who authored, translated, edited or otherwise contributed to that material. |
| Editorial reviewer | `ReviewRecord.reviewerRef` | Public Agent at an exact revision, reviewing exact target bytes and scope. |
| Repository submitter | Optional `WorkflowRecord.submission.submitterRef` | Public Agent who submitted the repository change; optional public context URI and commit SHA are complementary evidence. |
| Git author / committer | Git's own metadata | Repository history only. The validator/reporter never reads commit author/email fields or turns them into content credit. |

The same participant can hold several roles. None is inferred from another. A host, importer, maintainer, PR submitter or reviewer is not thereby an author or rights holder.

## Agent

`data/agents/<uuid>.json` uses the common envelope: permanent UUID, `entityType: agent`, `schemaVersion`, positive `revision`, origin, attribution, rights, ownership and provenance. `agentKind` accepts `person`, `organisation` and the existing `pseudonym` value. A person can also use a preferred display name/pseudonym without a legal-name field. New Agents use random UUIDv4; PR-base checks reject newly introduced v5 Agents while retaining reviewed legacy v4/v5 identities.

A nonblank `displayName` is required. Optional `externalIdentifiers` currently accepts a GitHub handle (`scheme: github`) or a hyphenated ORCID (`scheme: orcid`); format checks do not establish account ownership, contributor consent, ORCID checksum validity or scholarly qualifications. Optional `publicLinks` are stable HTTPS links without credentials or query parameters. Duplicate scheme/value pairs are rejected case-insensitively. Public identifiers are voluntary; the UUID is independent of them. Renaming increments revision without replacing the Agent. Equal display names never merge identities.

No additional biography or institutional-affiliation field is needed for this increment. Do not encode an employer or private legal identity in prose. A later consented affiliation contract needs its own review.

## Attribution

Each record has one or more role entries. A known credit has `agentId`, `role`, optional `attributionStatus` (`established`, `traditional`, `disputed`), `evidenceRefs`, `note` and `scope`. Omitting status preserves the previous contract; it does not establish historical certainty. Agent IDs resolve to the current authoring Agent, or the pinned release default; content identity never depends on a display name.

Roles: `author`, `contributor`, `translator`, `transcriber`, `editor`, `commentator`, `annotator`, `curator`, legacy `reviewer`, `adapter`, `creator`, `narrator`, `producer`. Multiple roles for one Agent are valid. Duplicate Agent/role pairs fail even when their notes differ; combine qualification within one entry. A legacy `reviewer` credit remains credit only, never review approval.

Unknown authorship is explicit and requires no fabricated Agent:

```json
{
  "attributionStatus": "unknown",
  "note": "The legacy source does not identify the original author.",
  "role": "author"
}
```

Unknown entries prohibit `agentId` and require a nonblank note. `authorshipStatus: not-recorded` in a report means the existing record supplies no author entry; it is not a newly established historical conclusion. Existing resource metadata still credits its curator only. Source organisations belong in author/contributor roles only when evidence establishes that role. Hosting alone is not authorship. `sourceCreditLine` is retained literally, never parsed into invented Agents.

Ordinary corrections append an appropriate editor/contributor while preserving original author/translator credits, source pins and adaptation lineage. All changed bytes require a revision increase. PR-base validation rejects removal or reclassification of prior credit unless `provenance.attributionCorrection` binds `previousRevision` and supplies a nonblank reason and pinned evidence. This permits evidenced correction of a mistaken credit; it is not a human approval. Reviewers must assess that evidence. The check compares explicit Git base/current structured JSON, not blame or commit identities. CI runs it on PRs; local validation without `--base-commit` cannot detect removed prior credits.

## Review

Review records remain in `editorial/reviews/`, outside content payloads. Required existing fields remain: common envelope, `targetRef` (exact ID/revision), `targetSha256`, `reviewerRef` (exact Agent revision), `reviewScope`, `decision`, `reviewedAt`, `rationale`, `dependencyRefs`.

| Existing category (`reviewScope`) | Explicit `reviewType` | `reviewerRole` |
| --- | --- | --- |
| scholarly | sanskrit-domain | domain-reviewer |
| source-fidelity | source-fidelity | source-reviewer |
| pedagogical | pedagogical | pedagogical-reviewer |
| editorial | editorial | editorial-reviewer |
| rights | rights | rights-reviewer |
| technical | technical-schema | technical-reviewer |

New reviews should record explicit type/role. Old category-only records map through this table; reports label that mapping rather than invent a separate approval. `scope` defaults to the previous whole-record interpretation or explicitly selects `whole-record` / `fields` with nonempty JSON pointers and an optional note. Field approval cannot qualify the whole record. Outcomes are `approved`, `changes-requested`, `rejected`, `disputed`, `unable-to-determine`; approval is always bounded by type, target and scope. Optional `evidenceRefs`, `limitations`, `unresolvedIssues` and `conflictsOfInterest` retain qualifications.

A schema/technical review cannot satisfy Sanskrit, pedagogical or rights review. Actual independent approval additionally requires an appointed Agent for that category, correct digest and critical dependency pins, no contributor self-review, no declared conflict, whole-record scope and no unresolved issues. Latest eligible decisions use timezone-aware instants; a tied disagreement cannot be settled by UUID order. Contributor/conflicted reviews may record non-approval outcomes with a conflict declaration and `resolution: requires-independent-review`; they cannot self-certify independent approval. The empty real authority registry remains empty. Role/appointment evidence, appeal resolution and indirect conflicts remain human governance responsibilities.

Changed target bytes/revisions or dependency pins invalidate applicability. A local full Git checkout can resolve exact older structured blobs for review/workflow/retirement sidecars, retaining earlier decisions without applying them to a successor. It reads commit hashes and JSON blobs only. Missing history fails rather than substituting current bytes; shallow/downloaded checkouts need exact history or an archived release. Content/answer pins remain strict current-authoring pins. Releases resolve old content and reviewer profiles only from exact archived members; neither current main nor an API is consulted.

## Public/private boundary

Public preferred names/pseudonyms and voluntarily supplied public links are sufficient. No legal name, postal address, phone, private email, employer, government ID or private GitHub data is collected. Closed schemas reject extra fields. Identity/editorial/credit checks reject recognisable email/contact values; diagnostics omit schema input values. Report projection whitelists public Agent fields and refuses recognisable contact values anywhere in its output. It does not copy Git emails. The public-file audit checks real identity/editorial JSON and generated JSON reports as well as its existing credential/path checks.

There is no safe private-contact facility in this repository. Do not put private correspondence, permission letters, email addresses or contact details in issues, PRs, commits, examples or logs. Do not collect them here. Use only disclosure-safe evidence identifiers/digests if an approved external permission process exists; establishing that process remains an owner decision. Automated detection cannot prove absence of all personal data: maintainers still inspect intended public names, consent, prose and source evidence before publication. Synthetic negative tests use reserved non-deliverable example identifiers, never real private details.

## Rights and reports

Authorship, rights holder, source credit, reproduce/redistribute/adapt permission, licence and publication eligibility remain separate. RightsStatement still owns its rights-holder refs, evidence, proposed uses, obligations and uncertainty; no attribution entry or GitHub action grants rights.

```sh
python -m validation attribution-report --output /tmp/attribution.json
python -m validation attribution-report --format markdown --output /tmp/attribution.md
python -m validation attribution-report --release /tmp/exact-archive --output /tmp/release-attribution.json
```

JSON is the lossless export; Markdown is a compact reading view. Output is deterministic, without timestamps of generation, Git identities or GitHub access. Rows include safe labels, revisions/digests, all credits/uncertainty, source lineage/credit, exact reviewer profiles, type/scope/outcome/limitations, separate submitters and rights notices. Question prompts/answers are not copied as labels. A recorded review is distinguished from exact applicability, appointment and independent category approval; no report is an eligibility certificate.

New tooling archives include `attribution.json` and a manifest `attributionReport` entry binding path, format and SHA-256. Verification checks both digest and recomputed pinned projection. Tooling archives have no content members, so their report contains notices and an empty content list. Frozen older manifests remain valid without this optional field; they are never rewritten. The release report reader supports exact archived content records for downstream credit preservation but does not assemble or authorise learner releases. It verifies archived schema/policy file hashes and all member digests. Missing archive contracts fail; no current schema is silently substituted.

[Current safe metadata report](../reports/contributor-attribution-example.md) · [JSON](../reports/contributor-attribution-example.json) · [Migration strategy](../reports/PRAVESHA_ATTRIBUTION_MAPPING.md).
