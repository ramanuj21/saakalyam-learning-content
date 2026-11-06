# Implemented contracts and Phase 8 compatibility

This is the independent `urn:saakalyam:learning:0.1.0:` contract, not a relabelling of the application or a new canonical vocabulary database. JSON Schema dialect is Draft-07; content schema version is 0.1.0.

The Phase 8.1 common envelope, UUID/revision/ownership/provenance principles, Question/representation pinning, independent review/workflow and five rights layers were inspected. Common, Agent, TextRepresentation, SourceWork/Edition/Reference, RightsStatement and ReviewRecord shapes derive from the proposed design 0.2.0 contract. Collection/Membership/Workflow shapes also account for the currently implemented 0.3.0 package. The authoritative application design files were not edited or promoted to approved policy.

| Domain | Implemented behaviour |
| --- | --- |
| Common | Permanent UUID; new entities use random UUIDv4, retained v4/v5 identities allowed after review. Entity type, schema version, positive revision, origin, attribution, rights, ownership and pinned provenance. No filenames/URLs/text-derived identity. |
| Question | Prompt, knowledge and answer-dependency pins; optional instruction/explanation/feedback components, topics, difficulty and contextual suitability. Choice keys, accepted variants, blanks, matching and rubric modes are disjoint; evaluation is separate from assessment configuration. |
| Question families | Single choice, multiple select, true/false, fill-in-blanks, matching, word-form identification, sentence correction, word formation, grammatical analysis, translation, sentence construction, Sanskrit composition, short/long answer, explanation and open-ended. These are definition/validation contracts, not execution support. |
| Text / component / rubric | Question-owned formulations are TextRepresentations; the established ScholarlyComponent identity has bounded learning-instruction/explanation/feedback variants. Rubric is an independently versioned learning-support record with pinned criterion descriptions and qualified-human-review method. No generic knowledge/analysis payload is implemented. |
| Collection / Membership | Shared explicit ordered question collections. Membership owns order and an exact question pin; definitions are not duplicated. Duplicate collection positions and exact targets fail. A question may be in several collections. Programme-owned collections are not quietly added to the current shared-only contract. |
| Resource / MediaAsset | Resource describes intended learning use and points to specific media revisions. MediaAsset owns particular file/external-item identity and reproduction-rights reference; storage is separate. One asset may serve several resources. Programme/related-question associations are references. |
| Source / rights | Work, consulted edition and locator are separate. Catalogue metadata rights never clear source reproduction. Representations, authored learning, material inputs and corpus/database rights remain distinct. Unknown rights are explicitly representable, never a grant. |
| Editorial | Draft/Review workflow sidecars, exact target-digest reviews, independent appointed reviewers and separate retirement/withdrawal records. Approved is derived from reviews; Published from selected immutable release membership; Retired from sidecars. No payload `published` or `verified` switch. |
| External dependencies | `dependencies.json` pins declared canonical knowledge/programme/taxonomy identity, revision, digest and dataset. Optional offline payload is hash-checked. Missing payload warns in authoring. This is not a canonical-domain implementation or learner-admission adapter; release remains blocked for external dependencies. |

## Type-specific evaluation

Single choice has exactly one correct local key; multiple select accepts an explicit nonempty key set; true/false has two labelled options and one correct key. Each blank has a stable key, a literal `{{key}}` marker in the prompt, and one list of accepted representation pins. Matching lists both sides and `matchingPolicy: one-right-per-left`; every left key maps exactly once to a valid right key, with shared right targets explicitly permitted by that policy.

Short answers support several explicitly recorded variants. Translation, formation, correction and composition can use approved variants or rubrics; long/explanation/open tasks require rubrics. Rubrics have no automatic equality judgement or scoring engine. Irrelevant option/blank/matching fields fail.

`identity-v1` preserves exact Unicode; `trim-edge-unicode-v1` describes edge whitespace trimming only; `manual-review-v1` requires qualified rubric review. These are pinned policy definitions, not an implemented answer comparator. No Devanagari/IAST equivalence, diacritic stripping, fuzzy acceptance, automatic Sanskrit explanation or learner grading is implemented.

## Versioning and resolution

Authoring has one current file per UUID. Critical refs always pin revision; a stale/missing pin fails, with no current/main fallback. A changed accepted payload requires an increased revision; CI compares the exact PR base commit. Changing type/ownership cannot silently repurpose an ID. Retire duplicate identities with replacement refs; do not erase old records. Human concept-equivalence decisions are not automated.

Tooling archives contain exact files from a frozen Git commit and SHA-256 manifest; current authoring files are not a historical revision archive. `validation.resolution.ReleaseResolver` verifies exact archived member paths, identities/revisions/types and digests, rejects duplicates/missing history/orphan historical members, and resolves pinned or release-default references without consulting main. A historical answer pin stays old even when the release default is newer. This is exact resolution, not evidence of learner admission. Learner manifests define exact `(id,revision,path,sha256)` members, resolution defaults, review dependencies, asset digests and database rights. **Learner archive assembly, external canonical admission and authenticated current-restriction distribution are not enabled.** No old-revision fallback or made-up approval compensates for these missing release gates.

## Deliberate extension decisions

The design package's minimal Question shape did not fully define blanks, matching, rubric records, difficulty, suitability or Resource/MediaAsset. This task expressly authorises those bounded executable extensions. They are documented here as learning 0.1.0 decisions requiring review before external content admission; they do not amend or claim sign-off for Phase 8.1. Source-text/lemma/grammar/literary authoring, full Programme/Activity, database services and learner state remain outside scope.
