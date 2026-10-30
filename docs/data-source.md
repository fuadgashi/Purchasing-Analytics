# Data source, refresh and publishing

[← README](../README.md)

One source: **SQL Server**, reached through two Power Query parameters, `pServer` and
`pDatabase`, never a literal connection string. Both hold placeholders in the repository;
set them to the real server and database in Desktop.

## Source views

The queries read seven views in schema `pur`. Each row below lists the columns the queries
select. Building these views over a source system is the only source-specific work: every
table, column and calculation of the model is named after them.

| View | One row is | Columns read |
|---|---|---|
| `pur.DocumentLine` | a purchase or sales document line, with its header's fields | `DocumentId`, `DocumentTypeId`, `OrgUnitId`, `PartnerId`, `DocumentDate`, `ProductId`, `Quantity`, `SupplierUnitPrice`, `NetUnitPrice` |
| `pur.DocumentType` | a document type | `DocumentTypeId`, `DocumentTypeName`, `IsPurchase`, `IsSalesOut` |
| `pur.Partner` | a business partner | `PartnerId`, `PartnerName`, `SortOrder`, `IsSupplier` |
| `pur.Product` | a product | `ProductId`, `ProductName`, `SortOrder`, `DivisionId`, `BrandId`, `IsGoods`, `CountsTowardReporting` |
| `pur.Brand` | a brand owner | `BrandId`, `BrandName` |
| `pur.Division` | a product division | `DivisionId`, `DivisionName` |
| `pur.OrgUnit` | an organisational unit | `OrgUnitId`, `OrgUnitName`, `SortOrder` |

**Classifications live in the source, not in the queries.** Which document types are purchases
or sales, which partners are suppliers, which products are goods and which count toward
reporting: each is a column of a view, so no query carries a list of codes. A new document type
is classified where it is created; until it is, it counts in no total.

**Units.** `SupplierUnitPrice` is without VAT. `NetUnitPrice` includes VAT,
after discounts.

**What the measures expect of the views.** The queries pass these columns through unchanged,
so the views must hold them as the measures read them:

- **`SupplierUnitPrice` is filled on purchase lines and blank on every other line.** It is what
  the supplier charged, after discounts and without VAT. A price that also holds transport,
  customs or other costs of bringing goods in would make purchases a landed cost, not a
  supplier price.
- **`PartnerId` on a purchase line is the supplier**, and `IsSupplier` is TRUE for it, or the
  Supplier slicer does not list it.
- **Every product has a brand and a division**, or its lines fall under a blank brand or
  division on the pages that group by them.

## Which model table reads which view

| Model table | Views |
|---|---|
| `FactInvoiceLine` | `pur.DocumentLine`, `pur.Product` (counts toward reporting) |
| `DimProduct` | `pur.Product`, `pur.Brand` |
| `DimPartner` | `pur.Partner` |
| `DimDivision` | `pur.Division` |
| `DimOrgUnit` | `pur.OrgUnit` |
| `DimDocumentType` | `pur.DocumentType` |

`DimDate` and `Labels` are built inside the model, from no source.

## Queries

Every source table is a **native SQL query** inside `Sql.Database(..., [Query = "..."])`
with an explicit one-hour `CommandTimeout`. The SQL does the work: joins, filters, the date
window. The M after it sets types and marks keys.

- **A native query does not fold.** The mashup engine can't fold steps after a native SQL
  query [[pq-folding]](sources.md#pq-folding), so every filter lives inside the SQL text.
- **`FactInvoiceLine` joins `pur.Product` with INNER on purpose**, to leave out at the source
  the products that do not count toward reporting. An inner join discards unmatched rows
  [[sql-from]](sources.md#sql-from): a line whose product is missing from the catalogue would
  drop out with its value.
- **The fact window** is `DocumentDate >= DATEFROMPARTS(YEAR(GETDATE()) - 1, 1, 1)`: the prior
  and the current year, rolling on 1 January. `DimDate` restates the same window; change the
  two together.

## Running it on your own data

The repository ships with no data and placeholder connection parameters. To run it:

1. **Build the seven views** in schema `pur`, with the columns above and the expectations
   they carry.
2. **Set `pServer` and `pDatabase`** in Desktop to the real server and database. Never commit
   them.
3. **Refresh**, then test as [dax-quality.md](dax-quality.md#how-a-dax-change-is-tested) says.

## Refresh and publishing

The model is refreshed in Desktop, tested, and published from `Purchasing.pbip`: publishing
creates a semantic model with the name of the file, and republishing replaces the model of
that name [[desktop-publish]](sources.md#desktop-publish). The order is always: commit → refresh →
test → publish.

**Credentials** live in each developer's Desktop and in the service, never in the repository.
