# Purchasing Analytics — notes for Claude

Power BI project (PBIP). [README.md](README.md) maps every document in `docs/`. The rules
live in those documents; this file only says where to look.

## Before any change

- Read [docs/maintenance.md](docs/maintenance.md): editing while Desktop is open, what
  blocks loading, the engineering standards.
- Open the document for the subject in the table below and follow it.
- Work on a short-lived branch and a pull request; `main` is always deliverable.

## Never

- Rebuild purchases or sales inline: purchases are `Purchases Value`, sales are
  `Sales Net Price` — [docs/measures.md](docs/measures.md).
- Count a service or allowance line as a purchase of goods — [docs/measures.md](docs/measures.md).
- Write figures, or the name of a business, person, place or source system, anywhere in
  the repository — [README.md](README.md). The author's name and contact address appear in
  `LICENSE` and the README's licence section only.
- Type text into a visual: every UI text is a row in `Labels` — [docs/report.md](docs/report.md).
- State how Power BI, DAX or SQL Server behaves without an entry in
  [docs/sources.md](docs/sources.md). No source, not written.

## Where each subject lives

| Changing | Read |
|---|---|
| the purchase, supplier and range measures | [docs/purchasing.md](docs/purchasing.md) |
| `Measure.tmdl`, `functions.tmdl`, `DimDate` | [docs/measures.md](docs/measures.md), [docs/dax-quality.md](docs/dax-quality.md), then [docs/purchasing.md](docs/purchasing.md) |
| any table, `relationships.tmdl`, `model.tmdl`, a source query | [docs/model.md](docs/model.md), [docs/data-source.md](docs/data-source.md) |
| report pages, slicers, formats, `Labels`, `LabelMeasures` | [docs/report.md](docs/report.md) |
| a `mobile.json`, the phone layout | [docs/mobile.md](docs/mobile.md) |
| `README.md`, `docs/` | [docs/sources.md](docs/sources.md) |

Not sure what a term means: [docs/glossary.md](docs/glossary.md).

## Checks

- After changing `README.md`, `CLAUDE.md` or `docs/`: `python scripts/docs_check.py`.
- After changing the model or the report: `python scripts/model_check.py` and
  `python scripts/dax_audit.py --strict`; after a DAX change, the test in
  [docs/dax-quality.md](docs/dax-quality.md#how-a-dax-change-is-tested).
- After changing an index's `RagColor` annotation: `python scripts/rag_colors.py` —
  [docs/dax-quality.md](docs/dax-quality.md#colour-measures).
- After changing a page, a visual or a `mobile.json`: `python scripts/mobile_check.py --strict`.
