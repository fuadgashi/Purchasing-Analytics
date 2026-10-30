# Core measure rules

[← README](../README.md)

## Purchases are one measure

Purchase value anywhere in this model means **`Purchases Value`**: quantity × supplier price
across `FactInvoiceLine` under two filters, `DimDocumentType[IsPurchase] = TRUE` and
`DimProduct[IsGoods] = TRUE`. Without the first, sales and every other document type count as
purchases; without the second, service and allowance lines do. **Never rebuild this measure
inline; call it.**

Its twins, under the same two filters: `Purchases Quantity`, `Purchases Invoices Count`
(distinct documents) and `Purchases Products Count` (distinct products).

## Sales is one measure

Sales means **`Sales Net Price`**: quantity × net price under `DimDocumentType[IsSalesOut] =
TRUE`. This model reads sales in one place only, the share of sales that new and dropped
products carry — see [purchasing.md](purchasing.md#the-range-of-products-bought). Never
rebuild it inline either.

## Prices and VAT

| Measure | Price | Lines | VAT |
|---|---|---|---|
| `Purchases Value` | supplier price, after discounts | purchase, goods only | without |
| `Sales Net Price` | net price, after discounts | sales-out | with |

- **Purchases are without VAT and net of discount.** The price with VAT would overstate what
  is bought, and the supplier's discounts are taken off.
- **The supplier price is what the supplier charged**, not a landed cost: transport, customs
  and other costs of bringing goods in are not in it ([data-source.md](data-source.md#source-views)).

## Working days

A working day is Monday to Saturday. The rule lives once, in the `DimDate` query
(`IsWorkingDay`); every working-day count reads `DimDate[Working Day]` and
`DimDate[Working Day Index]`.

- **`AvgDay`** divides the measure passed in by the working days of its window, ending on the
  latest date in context and never past today. On a product row the days start on the
  product's first sale in the window, company-wide; on any other row they start on the
  company's first day with a value, so the rows add up. Additive measures only.
- **`AvgDayConst`** is `AvgDay` over the whole calendar: the date slicers do not change it.
- **Monthly averages** are `AvgDayConst` × `Working Days per Month`: per month of working days,
  not per month with a purchase.

## Time windows are functions

A time window is a call to a user-defined function, never written out in a measure.

| Function | Window |
|---|---|
| `YearToDay` | the date slicers' window within the current year, cut at today |
| `PrevYear` | the window one year back, inside last calendar year |

A prior year **to date** is `YearToDay` over `PrevYear`: last year, cut at today's date one year
back. The `… Actual/Prior YTD` indexes compare like for like on it; the `… Actual/Prior`
indexes compare this year to date with the whole window a year back.

`IndexDif` is the change against a prior value, (current − prior) / prior, with guards for
blank and negative priors. `RagColor` turns a value into a theme colour name — `good`,
`bad` or `neutral` — so colours follow the theme. An index's colour measure is generated
from an annotation — see [dax-quality.md](dax-quality.md#colour-measures).

## Formats

- **`NumberFormat`** shows at most three significant digits with K, M or B, as the measure's
  whole dynamic format string; it returns a quoted literal, so the measure stays a number
  [[dynamic-format-strings]](sources.md#dynamic-format-strings).
- **`IndexFormat`** shows an arrow and a percentage with one decimal, ▲ at or above its
  centre and ▼ below.
- **No currency symbol.** Values are plain numbers; the report shows no currency.
