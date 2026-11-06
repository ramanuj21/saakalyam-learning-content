# Saakalyam Learning Content

Independent editorial foundations for reusable questions, collections, learning resources and media. This repository runs without Saakalyam, Next.js, a backend, accounts or runtime GitHub access.

**Current scope:** executable JSON Schema Draft-07 contracts, offline validation, synthetic English test fixtures, and two real Pravesha resource/media references as metadata only. The 1,513 application questions and all source media remain in their current application/source locations. Nothing here is an approved Sanskrit question bank or learner-ready release.

## Run locally

Use Python 3.9 or later (CI uses 3.12). Installation uses PyPI once; validation and tests then run offline.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python -m validation validate
python -m unittest discover -v
python -m validation validate --mode release --json
```

Authoring validation should pass with explicit publication warnings. Release validation **must fail** for the initial metadata: source rights, reviews, appointed authorities, external knowledge admission and current-restriction policy are unresolved. Passing structure is never scholarly approval.

[Domain contracts](docs/CONTRACTS.md) · [Contributing](CONTRIBUTING.md) · [Governance](GOVERNANCE.md) · [Migration/readiness inventory](reports/MIGRATION_READINESS.md) · [Licensing status](LICENSING.md) · [Validation evidence](reports/VALIDATION.md).

## Responsibilities

- `schemas/0.1.0/`: exact local, closed Draft-07 contracts and supporting primitives.
- `data/`: one current JSON file per entity UUID. Initial records are safe metadata, not source media or Sanskrit teaching.
- `tests/fixtures/`: deliberately synthetic English software fixtures, excluded from learner release.
- `policies/`: provenance, rights, review, eligibility and asset-storage decisions; no author-controlled approval flags.
- `validation/`: offline structural, semantic, history and tooling-archive validation; no answer grading.
- `reports/`: observed application inventory, contract compatibility and executed results.

The logical Resource, its particular MediaAsset, file bytes and physical storage location have separate responsibilities. Questions keep type-specific evaluation definitions inline, as in Phase 8; assessments, timing, marks and learner attempts are outside this repository.

## Reproducible tooling archives

From a clean committed snapshot:

```sh
python -m validation release --version 0.1.0-tooling.2 --output /tmp/saakalyam-tooling-archive
python -m validation verify-release /tmp/saakalyam-tooling-archive
```

The manifest pins the exact Git commit and file SHA-256 values. Output is generated outside the source snapshot to avoid a self-referential commit/digest. An existing output/version is never overwritten or rebound to a different Git commit; select an unused version or reproduce from the exact recorded commit. This initial command supports **tooling-only** archives: no learner records, source binaries or approved rights are implied. Learner archive assembly remains deliberately blocked until the governance and external-package admission requirements are met.

Public GitHub records, source text and answer keys are readable by everyone. This is appropriate for formative editorial content, not secret examinations. Future applications must make their own approved delivery projections; this repository implements no backend enforcement. Public media can be copied by third parties, and public forks cannot be remotely erased.


## Contributor attribution and review reports

[Implemented model and commands](docs/CONTRIBUTOR_IDENTITY.md) · [Safe current report](reports/contributor-attribution-example.md) · [JSON export](reports/contributor-attribution-example.json) · [Pravesha mapping strategy](reports/PRAVESHA_ATTRIBUTION_MAPPING.md) · [Increment validation](reports/CONTRIBUTOR_IMPLEMENTATION.md).

```sh
python -m validation attribution-report --output /tmp/attribution.json
python -m validation attribution-report --format markdown --output /tmp/attribution.md
python -m validation attribution-report --release /tmp/saakalyam-tooling-archive --output /tmp/release-attribution.json
```

New tooling archives bind an `attribution.json` digest in their manifest. Their content list remains empty; existing frozen tooling manifests stay valid. Reports resolve only local structured records or exact archived members/defaults. They do not query GitHub or turn Git identities into authors. See [ADR 001](docs/adr/001-contributor-identity.md) for compatibility and outstanding approval boundaries.
