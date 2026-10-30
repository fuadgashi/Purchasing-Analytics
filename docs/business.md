# The business

[← README](../README.md)

A distributor buys fast-moving consumer goods from its suppliers, keeps them in its warehouses
and sells them to shops and other customers. The model answers three questions about the buying
side:

1. **How much is bought, and is it more or less than last year?** Value, quantity and invoices,
   this year to date against last year and against the monthly average — see
   [purchasing.md](purchasing.md#volumes-and-invoices).
2. **From whom?** Each supplier's purchases and its share of the total — see
   [purchasing.md](purchasing.md#suppliers).
3. **Which products enter and leave the range?** Products bought this year and not last year,
   and the reverse, with their value and their share of sales — see
   [purchasing.md](purchasing.md#the-range-of-products-bought).

All three are answered from one source: the purchase and sales document lines since 1 January
of the prior year. There is no purchase-order data: the model reads what was invoiced, not what
was ordered.

## Suppliers and brands

Two different things can be called the supplier, and the model keeps them apart:

- **The supplier on the document** is the business partner on the purchase invoice
  (`DimPartner`). The Supplier slicer and the supplier share read it.
- **The brand** is the brand owner a product is booked under (`DimProduct[Brand]`). It is
  usually, not always, the company the product is bought from: a brand can be bought through
  a distributor. The tables and charts by brand read it.

A business partner can be a supplier and a customer at once; `DimPartner[IsSupplier]` says
which partners the company buys from.

## Products and divisions

- A **product** is one catalogue article, counted in its base unit.
- Its **division** is the commercial book it is bought and sold under.
- **Service and allowance lines** sit in the catalogue too. They carry no real cost or price
  and are not purchases of goods (`IsGoods`): every purchase measure leaves them out.
