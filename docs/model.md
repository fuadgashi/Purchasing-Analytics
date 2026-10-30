# The model

[← README](../README.md)

**Star schema.** The fact and the dimensions are separate tables. Every relationship is
many-to-one and single-direction, from the many side to the one side; none filters both ways.

## The fact — grain and window

| Fact | One row is | Window |
|---|---|---|
| **`FactInvoiceLine`** | one **document line**: a document, a partner, a product, a quantity, prices. Purchase and sales lines alike; `DimDocumentType` says which | 1 January of the prior year onwards |

Purchase lines carry the volumes, the invoices and the supplier price. Sales lines carry the
sales that the range measures set against purchases.

## Dimensions

| Dimension | Describes |
|---|---|
| `DimProduct` | products, with their brand and division; `IsGoods` tells goods from service and allowance lines |
| `DimPartner` | business partners: the supplier on a purchase, the customer on a sale; `IsSupplier` marks the partners the company buys from — see [business.md](business.md#suppliers-and-brands) |
| `DimDivision` | the commercial book a product is bought and sold under |
| `DimOrgUnit` | organisational units: the warehouses and other units documents are booked in |
| `DimDocumentType` | document types, with the flags `IsPurchase` and `IsSalesOut` |
| `DimDate` | the calendar: one row per day of the prior and the current year, marked as the date table; `Working Day` holds the working-day rule |

## Infrastructure

| Table | Role |
|---|---|
| `Measure` | the measure host: every business measure lives here |
| `Labels` | every user-facing string of the report, one row per owner, label type and culture |
| `LabelMeasures` | one text measure per label, each a `LabelText` lookup against `Labels`; also `User Culture` — see [report.md](report.md#labels) |

## Relationships

| From (many) | To (one) |
|---|---|
| `FactInvoiceLine[ProductId]` | `DimProduct[ProductId]` |
| `FactInvoiceLine[PartnerId]` | `DimPartner[PartnerId]` |
| `FactInvoiceLine[OrgUnitId]` | `DimOrgUnit[OrgUnitId]` |
| `FactInvoiceLine[DocumentTypeId]` | `DimDocumentType[DocumentTypeId]` |
| `FactInvoiceLine[Date]` | `DimDate[Date]` |
| `DimProduct[DivisionId]` | `DimDivision[DivisionId]` |

- **A single-direction relationship filters from the one side to the many side**
  [[relationships]](sources.md#relationships), so a product, partner, unit or date pick reaches
  the document lines.
- **The supplier never filters sales.** The supplier is the partner on a purchase; on a sales
  line the partner is a customer, so a supplier pick on sales would find almost nothing. The
  one measure family that reads sales, the new and dropped sales shares, removes the partner
  filter from its sales side (`REMOVEFILTERS` on `DimPartner`) — see
  [purchasing.md](purchasing.md#the-range-of-products-bought).
- **There is no supplier › product hierarchy.** `DimPartner` and `DimProduct` are not related:
  each reaches `FactInvoiceLine` on its own, and a supplier is known only from each invoice. A
  slicer cannot drill from a supplier to its products; the Supplier slicer and the
  Division / Product slicer are separate, and picking both shows what was bought of those
  products from that supplier.
- **Key columns share a data type** across every relationship. `ProductId` and `PartnerId` are
  text, so their slicers offer a search box; the other keys are whole numbers.

## Query groups

Every query sits in one of four groups, declared in `model.tmdl`:

| Group | Queries |
|---|---|
| `Fact` | `FactInvoiceLine` |
| `Dimension` | `DimProduct`, `DimPartner`, `DimDivision`, `DimOrgUnit`, `DimDocumentType` |
| `Model` | `DimDate`, `Measure`, `Labels`, `LabelMeasures` |
| `Parameters` | `pServer`, `pDatabase` |

## Captions

`cultures/en-US.tmdl` gives fields short captions for the report — `Current Year`,
`Prior Year` — where the name is long. Captions translate object metadata, not data values
[[translations]](sources.md#translations); the report text that is data lives in `Labels`.

## Data access options

`model.tmdl` sets two options of the M data engine, `legacyRedirects` and
`returnErrorValuesAsNull` [[data-access-options]](sources.md#data-access-options).

- **`returnErrorValuesAsNull`** makes an error in one cell of a query's result load as a
  null instead of failing the refresh, so a refresh can succeed with missing values. It does
  not touch DAX.
- **`legacyRedirects`** allows redirects from HTTPS to HTTP. The only data source is SQL
  Server, so there is nothing to redirect.
