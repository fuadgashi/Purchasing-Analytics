# The report

[← README](../README.md)

**Three pages**, in English. The report opens on `Supply`.

| Page | Asks | Main visuals |
|---|---|---|
| `Supply` | how much is bought, and how does it compare? | value, quantity and invoice cards with last year to date, the monthly average and the change; value, quantity and invoices by month, last year against this year; the invoices received, line by line |
| `Purchase` | what is bought, and from whom? | value and quantity by product, last year against this year, with the change; value by brand; the top fifteen suppliers' share of purchases |
| `Assortment` | which products enter and leave the range? | cards for products bought, new and dropped, the net change, their value and their share of sales; the movement by brand and product; the value of new against dropped products by brand |

What each figure means is in [purchasing.md](purchasing.md).

## Page navigation

Each page carries a **tab row** at the top right: one button per page, Supply · Purchase ·
Assortment, each reading its text from a label measure (`PageNav1 | Title` …). The tab
of the page you are on is filled. There is no menu page and no section drawer; the three tabs
are the whole navigation. Every page also has a phone layout — see [mobile.md](mobile.md).

## Slicers

Every page has **five slicers in a row** (x = 725, 965, 1205, 1445, 1685), each under a
title button that reads a `… | SlicerTitle` label measure. A field sits in the same slot on
every page, and every slicer is synced across the three pages.

| Slot | Slicer | Fields | Sync group |
|---|---|---|---|
| 1 | Date Range | `DimDate[Date]` | `Date` |
| 2 | Supplier | `DimPartner[PartnerName]`, suppliers only | `Supplier` |
| 3 | Division / Product | `DivisionName` › `Brand` › `ProductName` › `ProductId` | `Product` |
| 4 | Invoice Number | `FactInvoiceLine[DocumentId]` | `Invoice` |
| 5 | Org / Depot | `OrgUnitName` › `OrgUnitId` | `OrgUnit` |

- **The date slicer saves no dates.** It opens on the whole calendar, so it never goes stale at
  New Year; the measures cut at today themselves.
- **The Supplier slicer lists suppliers only**: a visual filter on `DimPartner[IsSupplier]`.
- **Division / Product** is `DivisionName` › `Brand` › `ProductName` › `ProductId`, divisions
  listed Z→A.
- **A supplier pick and the sales shares**: the shares keep a value — see
  [purchasing.md](purchasing.md#the-range-of-products-bought).

## Labels

**No text is typed into a visual.** Page titles and subtitles, tab labels, visual titles and
subtitles, slicer titles, the captions under card values and every alt text are label
measures in `LabelMeasures`, each a call to `LabelText( LabelType, OwnerType, OwnerNumber )`,
which reads one row of `Labels`.

- **Owner numbers are one sequence**: pages 1–3, then the slicers, then the visuals. A number
  is never shared across owner types.
- **A missing row shows ⚠**, never a quiet fallback, so a gap is seen in review.
- **One language, English.** `User Culture` returns `en-US`, and `Labels` holds one row per
  label. To add a language: add its rows to `Labels`, and make `User Culture` return the
  viewer's culture.
- **Alt texts** are `Alt … | VisualSubtitle` label measures: the visual's kind, then what it
  shows.
- **Field names** come from captions (`cultures/en-US.tmdl`): a field shows its caption in a
  visual, never a name typed into it.

## Number formats

- **`NumberFormat`** on the sales values, **`IndexFormat`** on the indexes — see
  [measures.md](measures.md#formats). A dynamic format string keeps the measure numeric
  [[dynamic-format-strings]](sources.md#dynamic-format-strings).
- **Colours** are theme sentiment names — good, neutral, bad — from the colour measures, so
  they follow the theme. The theme is `cortnes-light.json`.

## Sort order

Three names sort by a hidden column that comes from the source:

| Column | Sorted by |
|---|---|
| `DimProduct[ProductName]` | `ProductSortOrder` |
| `DimPartner[PartnerName]` | `PartnerSortOrder` |
| `DimOrgUnit[OrgUnitName]` | `OrgUnitSortOrder` |
