# Glossary

[← README](../README.md)

The model's own terms. Each rule is stated only in its own document; this page says what a
word means and where to read more.

| Term | Means | See |
|---|---|---|
| **Purchases** | quantity × supplier price on purchase documents, goods only | [measures.md](measures.md#purchases-are-one-measure) |
| **Supplier** | the business partner on a purchase document, `DimPartner` | [business.md](business.md#suppliers-and-brands) |
| **Brand** | the brand owner a product is booked under, `DimProduct[Brand]` | [business.md](business.md#suppliers-and-brands) |
| **Supplier price** | what the supplier charged per unit, after discounts, without VAT | [measures.md](measures.md#prices-and-vat) |
| **Net price** | the selling price after discounts, with VAT | [measures.md](measures.md#prices-and-vat) |
| **Goods** | products that are not service or allowance lines, `DimProduct[IsGoods]` | [business.md](business.md#products-and-divisions) |
| **Invoice** | a purchase document with at least one line of goods | [purchasing.md](purchasing.md#volumes-and-invoices) |
| **SKU** | a product, as the range measures count it | [purchasing.md](purchasing.md#the-range-of-products-bought) |
| **New product** | bought this year to date, not in the same period last year | [purchasing.md](purchasing.md#the-range-of-products-bought) |
| **Dropped product** | bought last year to date, not this year | [purchasing.md](purchasing.md#the-range-of-products-bought) |
| **Supplier share** | a supplier's share of purchase value this year to date | [purchasing.md](purchasing.md#suppliers) |
| **Working day** | Monday to Saturday | [measures.md](measures.md#working-days) |
| **Actual Year** | this year to date, cut at today | [measures.md](measures.md#time-windows-are-functions) |
| **Prior Year YTD** | last year, cut at today's date one year back | [measures.md](measures.md#time-windows-are-functions) |
| **Organisational unit** | a warehouse or other unit documents are booked in | [model.md](model.md#dimensions) |
