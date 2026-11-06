# Pravesha migration and readiness inventory

Observed 6 November 2026 from actual current application files. Application HEAD `2b15e738e0e97e29b4c66bf2855fcca42d429f52`; prior uncommitted learning and usability work is included in the inspected state. No application file, legacy service or learner data was changed/queried.

[Complete machine-readable inventory](application-inventory.json) records every inspected local file, external recording and lesson/placeholder association, exact file sizes/hashes where bytes are available, credits, original/adapted/external status and migration recommendations. The inventory is metadata, not copied teaching or question content.

## Observed resources

| Resource class | Count / verification |
| --- | --- |
| asset-manifest-metadata | 1 |
| derived-slide-image | 273 |
| external-recording | 22 |
| lesson-metadata | 20 |
| original-pdf | 18 |
| unavailable-presentation-placeholder | 5 |
| Local audio / video binaries | 0 / 0; recording URLs remain external |

All 18 PDF byte counts, SHA-256 values and PDF signatures were checked against current application metadata. Physical page counts in this report are **declared by the app**, not independently re-parsed. All 273 WebP signatures/hashes/sizes were checked against the asset manifest; 249 lesson image hashes were additionally checked against lesson metadata. The other 24 belong to the supplemental first practice class and are not assigned to individual chapters. The app’s asset manifest is separately inventoried. No OCR, source-PDF rewrite, caption/playback qualification or scholarly/rights approval occurred.

Twenty lesson parts contain four readable adaptations, eleven original-presentation parts and five recording-only parts. Adapted text is recorded as an adaptation and is not copied. The five unavailable presentation placeholders are Chapter 6–10 Part 2; they remain unavailable, with no fabricated asset/resource entities. The workbook remains thematic; no chapter mapping is inferred. Twenty lesson recordings and two supplemental recordings are inventoried without fetching streams.

## Existing questions

| Chapter | Available | Excluded | Source records | Families |
| --- | --- | --- | --- | --- |
| 1 | 150 | 0 | 150 | short-answer: 20, single-choice: 107, true-false: 23 |
| 2 | 142 | 8 | 150 | short-answer: 7, single-choice: 127, true-false: 8 |
| 3 | 171 | 0 | 171 | short-answer: 26, single-choice: 138, true-false: 7 |
| 4 | 150 | 0 | 150 | short-answer: 17, single-choice: 117, true-false: 16 |
| 5 | 150 | 0 | 150 | short-answer: 6, single-choice: 138, true-false: 6 |
| 6 | 150 | 0 | 150 | short-answer: 1, single-choice: 149 |
| 7 | 150 | 0 | 150 | short-answer: 11, single-choice: 131, true-false: 8 |
| 8 | 150 | 0 | 150 | short-answer: 13, single-choice: 125, true-false: 12 |
| 9 | 150 | 0 | 150 | short-answer: 13, single-choice: 129, true-false: 8 |
| 10 | 150 | 0 | 150 | short-answer: 18, single-choice: 118, true-false: 14 |

Observed totals: **1513 available + 8 excluded = 1521 source records**. These local projections retain original source evidence and source keys; none is migrated into this repository. Subject approval, per-item attribution/rights, canonical knowledge/answer-dependency mappings and source/identity reconciliation remain pending. The eight Chapter 2 exclusions remain excluded. Historical key recovery is not independent Sanskrit approval.

## Application-to-repository mapping and identity strategy

| Current application concept | New repository / migration decision |
| --- | --- |
| Normalized Question + separately identified evaluator | Future Question retains reviewed UUID/revision; evaluation payload is inline, preserving original evaluator identity/digest in migration evidence. No bulk import now. |
| Prompt / choices / accepted variants | Independently pinned TextRepresentations, exact Unicode, question ownership and reviewed rights. No transliteration/fuzzy equivalence. |
| Line-derived v5 question IDs | Preserve as identity candidates; freeze an explicit source-to-ID ledger before any source reorder/re-import. New unrelated records use random v4. Do not derive new IDs from lines. |
| Fifteen-question UI chunk | Presentation configuration, not permanent collection identity or prerequisite. Future explicit Collections/Memberships require reviewed selection. |
| Existing PDF asset UUID | Introduction PDF ID `2658da4b-e869-4642-84d4-5b1fbb196c05` retained for the same exact byte-identified media item; this is identity continuity, not rights approval. |
| Logical PDF teaching use | New independently allocated Resource UUID; points to the media revision. Moving storage does not create another logical resource. |
| Recording URL without stable app asset UUID | New random MediaAsset UUID for the particular external item and separate Resource identity; URL is not an ID. |
| Rendered slide / adapted text | Derivation provenance to original presentation, new identities only after review; source/adaptation/representation rights remain distinct. |
| Programme / lessons / chapter sequence | Existing application IDs remain candidate external references. No Programme or Activity domain is recreated here. The app programme UUID is not assumed to be a registered canonical knowledge programme. |
| Practice visit state, accounts, attempts | Never imported, published or modelled as corpus entities. |

## What is published initially

Schemas, offline code/tests, new documentation/policies/templates, the safe inventory and **eight metadata records**: one public attribution handle, three explicit unknown-rights statements, two logical resources and two external media references (introduction PDF and introduction recording). No real reviewer appointments, scholarly approvals, grants, source teaching or source binaries. Metadata records are structural drafts with publication warnings, not a learner dataset.

The PDF metadata retains its actual application SHA-256/byte length and source credit. The external recording omits unknown stream MIME, size, duration and checksum. Its link and source association are recorded, without a playback/caption claim. Current public link facts/short credits are appropriate inventory metadata; disclosure of source text or media is not inferred.

## What is blocked / not migrated

All 18 PDFs, 273 rendered images, 22 recording payloads, adapted lesson prose and 1,513 questions/keys remain excluded. Access/link is known from existing app metadata; reproduce, redistribute, adapt and applicable licence obligations require exact evidence and independent rights review. Five absent presentations stay absent. No full Pravesha, other-course, legacy learner or Phase 8 knowledge migration is attempted.

## Next bounded increment

Appoint rights and Sanskrit/pedagogical reviewers and approve submission/licence boundaries. Clear one actual small Pravesha question sample and one real resource (or obtain explicit binary redistribution evidence), establish exact knowledge/answer-evidence dependencies and the identity ledger, then admit those records through the existing contracts. Establish external canonical-package/restriction-trust admission before learner release. A frontend adapter or assessment execution remains separately authorised work.
