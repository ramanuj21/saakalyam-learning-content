# Executed validation

6 November 2026. This records actual local implementation checks; no learner-ready dataset or scholarly approval is claimed.

| Check | Actual result |
| --- | --- |
| Schema bundle | 20 closed JSON Schema Draft-07 contracts, checked and registered entirely offline. Unsupported formats and external schema fetches fail. |
| Automated tests | `python -m unittest discover -v`: 63 passed, zero failures/errors. Includes seven primary synthetic English question families, nine additional language/open-family subcases, invalid task/evaluation combinations, keys/blanks/matching, exact revisions, Unicode preservation, references/ownership, collection memberships, review digests/independence, media integrity/public-disclosure gates, revision history and release reproducibility/tampering. |
| Authoring | `python -m validation validate --json`: 8 metadata records, zero structural errors and 23 explicit publication warnings. No Sanskrit questions or binaries in data. |
| Learner-release gate | `python -m validation validate --mode release --json`: rejected with 25 expected errors and no output release. Missing rights/reviews/governance/current-restriction trust remain blocking. |
| Byte/JSON/code checks | `python -m compileall -q validation tests` and public-file UTF-8/JSON/credential/path/binary preflight passed. The preflight scans all proposed files and is separate from human disclosure review. |
| Observed application inventory | 18 PDF sizes/digests/signatures; 273 WebP signatures/digests; 249 image hashes additionally checked against lesson metadata; 22 external recording links; 20 lesson parts; 5 unavailable presentations; 1 asset manifest. No streams fetched, source text copied or original files modified. |
| Question inventory | Actual current local packages: 1,513 available, 8 excluded, 1,521 source records. Only counts, source-file identity/hashes and migration metadata were recorded; questions/keys were not migrated. |
| Application preservation | Task-start SHA-256 baseline: all 1,284 protected application files unchanged, including its pre-existing edits. The application Git repository is not committed or pushed by this task. |
| Documentation | Every local Markdown file link checked; zero missing targets. |

The synthetic fixture identities/decisions are isolated software tests, not real authors, source witnesses, reviewers, grants or Sanskrit claims. Current real metadata rights are explicitly unknown; no independent content approval is invented. Exact archive reference resolution and tooling-file reproduction do not imply learner eligibility. External canonical-package admission and authenticated current-restriction distribution remain deliberately unavailable.

The first implementation supports tooling-only archives from clean frozen Git snapshots, with exact file hashes, member/default manifest contracts and an immutable historical-reference resolver. Historical synthetic answer pins are tested against newer release defaults, including missing/tampered/duplicate/orphan historical bytes. A new learner release remains forbidden until its human and technical admission requirements are met.

## Initial GitHub publication

- Repository: https://github.com/ramanuj21/saakalyam-learning-content — owner `ramanuj21`, public, default branch `main`, all verified through authenticated GitHub API.
- Initial implementation commit: `a61665a86495444f26009922e792532d6a143315`.
- Tooling manifest commit: `715015a410acf3117461a3bec4d1d9b20c342542`. Remote main was checked against that exact SHA after its push.
- Initial GitHub Actions execution: [successful run](https://github.com/ramanuj21/saakalyam-learning-content/actions/runs/42243968444) for that manifest commit. It ran the tests, authoring validator and public-file audit.
- Tooling snapshot `0.1.0-tooling.1` pins the initial implementation commit and 59 exact files; its local archive verifier passed. No learner records or binary media are members.
- Follow-up release hardening prevents reusing a dataset version from another commit; synthetic regression added. No published snapshot is rewritten.
