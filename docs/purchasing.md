# Purchasing

[← README](../README.md)

What the model measures about buying, and the rules behind each figure. The base measures and
their filters are in [measures.md](measures.md#purchases-are-one-measure).

## Volumes and invoices

Three volumes, each in the same five views:

| Volume | Base measure |
|---|---|
| value | `Purchases Value` |
| quantity | `Purchases Quantity` |
| invoices | `Purchases Invoices Count` |

| View | Measures | Window |
|---|---|---|
| this year to date | `… Actual Year` | `YearToDay` |
| last year | `… Prior Year` | `PrevYear` |
| last year to date | `… Prior Year YTD` | `YearToDay` over `PrevYear` |
| monthly average | `… Actual Year Monthly Average` | `AvgDayConst` × `Working Days per Month` |
| change | `Index … Actual/Prior YTD` (like for like), `Index … Actual/Prior` (this year to date against the whole of last year's window), `Index … Monthly Average Actual/Prior` | `IndexDif` |

- **The cards compare like for like.** Each card shows this year to date with last year to
  date and the monthly average beside it, and the change on both.
- **The monthly charts set this year against last**, month by month: last year in full, this
  year up to today. The Purchase tables compare the same way, with `Index … Actual/Prior`.
- **An invoice is a purchase document with at least one line of goods.** A document holding
  only service lines is not counted.

## Suppliers

- **The supplier is the partner on the purchase document**, `DimPartner`; the brand is a
  product attribute — see [business.md](business.md#suppliers-and-brands).
- **`Purchases Value Actual Year Share`** is a supplier's share of purchase value this year to
  date. Its denominator removes the partner filter only (`REMOVEFILTERS` on `DimPartner`), so a
  Top N chart shows each bar's real share of the total and a supplier pick does not turn its
  share into 100%. The date, product and unit slicers narrow both sides.
- **The Supplier slicer lists suppliers only**: it is filtered to `DimPartner[IsSupplier]`.

## The range of products bought

A product's place in the range is read from whether it was bought, this year to date against
the same period last year (`Purchases Quantity Actual Year` against
`Purchases Quantity Prior Year YTD`):

| Product is | Bought this year | Bought last year to date | Counted by |
|---|---|---|---|
| **new** | yes | no | `Purchases New Products Count` |
| **dropped** | no | yes | `Purchases Dropped Products Count` |
| kept | yes | yes | not counted on its own |

- **Net change** is new minus dropped (`Variance Purchases Products Count New/Dropped`). It
  equals this year's product count minus last year's to date.
- **Value**: a new product is valued at what was bought of it this year, a dropped one at what
  was bought of it last year to date. Both are shown as positive amounts.
- **Sales share**: the share of this year's sales that comes from new products
  (`Purchases New Product Sales Share`), and from dropped ones
  (`Purchases Dropped Product Sales Share`). A low new share means new listings are not yet
  earning their place; a high dropped share means stock still selling is no longer being
  bought.
- **With a supplier picked**, the products are the ones newly bought, or no longer bought, from
  that supplier, and their sales are set against all of this year's sales. The sales side
  ignores the partner filter: on a sales line the partner is a customer, not the supplier
  ([model.md](model.md#relationships)). With no supplier picked the figures are the same either
  way.
- **Read the three counts, not only the net change.** A range down by seven products can be
  seven dropped, or twelve dropped against five new: a range being rebuilt. Only new and
  dropped side by side tell them apart.
- **The test is whether a product was bought, not how much**, so a change in a product's unit
  of measure does not move it between new and dropped.

## Known limitations

- **No purchase orders.** The model reads invoices; what was ordered and not yet delivered is
  not in it.
- **Two years of history.** The fact window is the prior and the current year, so "last year"
  is the furthest back any figure goes ([data-source.md](data-source.md#queries)).
