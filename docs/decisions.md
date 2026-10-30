# Design decisions

[← README](../README.md)

The rules a future maintainer would otherwise re-litigate, each with the reason it holds.

- **Everything is named in English, after the source views.** Tables, columns, measures and
  functions read the same words as the `pur` views ([data-source.md](data-source.md)), so a
  figure traces from a visual to the SQL under one name. Mapping a source system to these
  names happens once, in the views, not in the model.
- **Classifications are columns of the source, not lists in the queries.** Purchase and sales
  document types, suppliers, goods and products that count toward reporting: each is a flag in
  a view. A code list inside a query goes stale silently when the source adds a code.
- **Purchases are at the supplier's price, not a landed cost.** What the supplier charged is
  comparable across suppliers and over time; transport and customs vary with the shipment, not
  the supplier ([measures.md](measures.md#prices-and-vat)).
- **Purchases count goods only.** A service or allowance line carries no real price per unit,
  so counting it would distort value, quantity and invoices alike.
- **The supplier is the partner on the document, the brand is the product's.** One column for
  both would answer "who did we buy from" and "whose products did we buy" with the same name
  and different numbers ([business.md](business.md#suppliers-and-brands)).
- **No supplier › product hierarchy.** The source stores no supplier per product, only per
  invoice, so a product can come from several suppliers. A hierarchy across the two would have to
  pick one, and would be wrong for the rest ([model.md](model.md#relationships)).
- **The range test is whether a product was bought, not how much.** A quantity threshold would
  move products between new and dropped on a unit-of-measure change
  ([purchasing.md](purchasing.md#the-range-of-products-bought)).
- **Averages are per working day**, not per day with a purchase, so a month with few
  deliveries is not read as a busy one ([measures.md](measures.md#working-days)).
- **Sort keys come from the source, not DAX**, in the same view as the name they sort, so the
  name and its key arrive together on every refresh ([report.md](report.md#sort-order)).
- **No section navigation.** Three pages need no menu: the tab row on each page is the whole
  navigation, so there is no menu page, drawer or bookmark to keep in step.
- **One language, kept in `Labels`.** The report is English only, yet every UI text stays a
  `Labels` row: titles never sit hard-coded on the canvas, and a language is added as data
  ([report.md](report.md#labels)).
- **The calendar restates the fact window instead of reading it.** A calendar derived from a
  fact query depends on that query, and goes short with no error when the query returns
  nothing.
