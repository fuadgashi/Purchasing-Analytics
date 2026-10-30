# DAX quality

[← README](../README.md)

How the model's DAX is kept to its standards: nothing unused, no duplicate, one folder per
subject, every measure described and captioned, and every change proven not to move a number.

**Everything here is measured from the files.** `scripts/dax_audit.py` reads the model and the
report: every measure and function, and every place a visual, page or filter binds a measure.
It sees this report only: it cannot see Analyze in Excel or another report built on the
model.

| Command | Does |
|---|---|
| `python scripts/dax_audit.py` | prints every count below |
| `python scripts/dax_audit.py --strict` | the same, and exits 1 if a count that must be zero is not; runs on every pull request |
| `python scripts/dax_audit.py --register` | regenerates the [measure register](#measure-register) in this document |
| `python scripts/dax_audit.py --baseline baseline.dax` | writes the regression query of [How a DAX change is tested](#how-a-dax-change-is-tested) |
| `powershell -File scripts/dax_baseline.ps1 -QueryFile baseline.dax -OutCsv before.csv` | runs it against the model open in Desktop |
| `python scripts/dax_audit.py --compare before.csv after.csv` | compares two runs, measure by measure |
| `python scripts/dax_audit.py --json out.json` | writes every name behind every number |
| `python scripts/rag_colors.py` | writes the colour measure of every index that asks for one — see [Colour measures](#colour-measures) |

## What counts as used

A measure is **used** when a visual, page or filter of the report binds it, when a used
measure references it, or when a function a used measure calls reads it (`User Culture`, read
by `LabelText`). A measure no visual binds is still **kept when the docs name it** in
backticks, or name its folder. Everything a kept measure calls is kept with it. Today every
analytical measure is bound by a visual or reached through one.

## Counts that must be zero

`--strict` fails the pull request when any of these is not zero.

| Count | What it catches |
|---|---|
| unresolved report references | a visual bound to a measure that no longer exists |
| unused measures, unused label measures, unused functions | DAX nothing reaches: removed, not kept "in case" |
| exact duplicates | two measures with the same expression, ignoring spaces and comments |
| text typed into visuals | a field renamed inside a visual instead of captioned in the model — see [report.md](report.md#labels) |
| fields sharing one caption in a visual | two columns of one table or matrix under the same heading |
| colour measures out of date | a colour measure that no longer matches its index's annotation |
| measures without a description, format or folder | the standards in [maintenance.md](maintenance.md#engineering-standards); a colour measure is text and carries the text format hint instead of a format |
| variables without the `_` prefix | a `VAR` not in English snake_case with the `_` prefix — see [maintenance.md](maintenance.md#naming) |
| colours not from `RagColor` | a theme colour name typed into a measure instead of returned by `RagColor` |
| `IFERROR` | an error hidden instead of prevented: the model divides with `DIVIDE` and tests with `ISBLANK` |
| `FILTER` over a whole table | a filter argument built on a whole table: the model's filter arguments name columns |
| sales rebuilt inline | quantity × net price summed outside `Sales Net Price` — see [measures.md](measures.md#sales-is-one-measure) |
| purchases rebuilt inline | quantity × supplier price summed outside `Purchases Value` — see [measures.md](measures.md#purchases-are-one-measure) |
| visible measures without a caption | a field that would show its model name in a visual |

The audit also prints, without failing, the **shapes** that three or more measures share: the
expression with each measure reference replaced by a placeholder.

| Shape | Measures | Why they stay named measures |
|---|---|---|
| `YearToDay( [x] )` | 9 | the year-to-date window is already one function; each measure is a figure a card, chart or table shows under its own caption |
| `PrevYear( [x] )` | 4 | the same, one year back |
| `IndexDif( [x], [y] )` | 6 | the change is already one function; each index pairs two named figures and carries its own format and colour |
| `AvgDayConst( [x] ) * [Working Days per Month]` | 3 | the monthly averages of value, quantity and invoices: one line each, a card reference each |

## Colour measures

An index asks for a colour with one annotation on the measure:

- `annotation RagColor = UpIsGood`: a rise is good.
- `annotation RagColor = UpIsBad`: a rise is bad.

`python scripts/rag_colors.py` then writes its colour measure, hidden, in
`Formatting\RAG Color`: `RagColor( [index], centre )`, or with the sign turned for `UpIsBad`.
Edit the annotation, never the colour measure; `--check` runs on every pull request and fails
when a colour measure is out of step. A colour measure with its own rule — anything but one
`RagColor` call on one index — would be written by hand and left alone by the script; today
there is none.

## How a DAX change is tested

Run before the change and after it, on the same refresh.

| Test | How | Passes when |
|---|---|---|
| **Numbers unchanged** | `--baseline`, then `dax_baseline.ps1` on the model open in Desktop, before and after; `--compare` | every kept numeric measure, every year: no value appears or vanishes, and a number differs by less than one part in 10¹² |
| **No broken binding** | `python scripts/model_check.py` and `python scripts/dax_audit.py` | 0 findings; `unresolved report references: 0` |
| **The audit's counts** | `python scripts/dax_audit.py --strict` | every count that must be zero is zero |
| **Visuals render** | open the pages listed under *Used on* in the register | no visual shows an error or a blank |
| **Documents** | `python scripts/docs_check.py` | 0 findings |

**The baseline needs data.** `dax_baseline.ps1` reads the model open in Power BI Desktop, so
it runs only once the model is connected to a source and refreshed — see
[data-source.md](data-source.md#running-it-on-your-own-data). The baseline query itself is generated from the files and
needs nothing: `--baseline` writes one query per folder, every measure by `DimDate[Year]`, and
the PowerShell script runs them as one query and saves one row per year. The comparison allows
a relative difference of 10⁻¹², so two runs may differ only in their last digits; a real change
moves a figure by far more.

## Measure register

Every analytical measure in its place: its folder, whether it is visible, and the visuals
that use it. Regenerated by `python scripts/dax_audit.py --register`; edit the model, not
this table.

<!-- register:start -->
43 analytical measures.

### Calculation Roots

| Measure | Folder | Visible | Used on |
|---|---|---|---|
| Purchases Invoices Count | Purchases | yes | inside 2 measures (Purchases Invoices Count Actual Year, …) |
| Purchases Products Count | Purchases | yes | inside 2 measures (Purchases Products Count Actual Year, …) |
| Purchases Quantity | Purchases | yes | Supply table |
| Purchases Value | Purchases | yes | Supply table |
| Sales Net Price | Sales | yes | inside 1 measure (Sales Net Price Actual Year) |

### Calendar

| Measure | Folder | Visible | Used on |
|---|---|---|---|
| Working Days per Month | Working Days | no | inside 6 measures (Index Purchases Invoices Count Monthly Average Actual/Prior, …) |

### Formatting

| Measure | Folder | Visible | Used on |
|---|---|---|---|
| Index Purchases Quantity Actual/Prior Color | RAG Color | no | Purchase table |
| Index Purchases Value Actual/Prior Color | RAG Color | no | Purchase table |

### Purchasing

| Measure | Folder | Visible | Used on |
|---|---|---|---|
| Index Purchases Invoices Count Actual/Prior YTD | Invoices Count | yes | Supply card |
| Index Purchases Invoices Count Monthly Average Actual/Prior | Invoices Count | yes | Supply card |
| Purchases Invoices Count Actual Year | Invoices Count | yes | Supply card, Supply combo chart |
| Purchases Invoices Count Actual Year Monthly Average | Invoices Count | yes | Supply card |
| Purchases Invoices Count Prior Year | Invoices Count | yes | Supply combo chart |
| Purchases Invoices Count Prior Year YTD | Invoices Count | yes | Supply card |
| Index Purchases Products Count Actual/Prior YTD | Products Count | yes | Assortment card |
| Purchases Dropped Product Sales Share | Products Count | yes | Assortment card |
| Purchases Dropped Products Count | Products Count | yes | Assortment card, Assortment matrix |
| Purchases New Product Sales Share | Products Count | yes | Assortment card |
| Purchases New Products Count | Products Count | yes | Assortment card, Assortment matrix |
| Purchases Products Count Actual Year | Products Count | yes | Assortment card, Assortment matrix |
| Purchases Products Count Prior Year | Products Count | yes | inside 1 measure (Purchases Products Count Prior Year YTD) |
| Purchases Products Count Prior Year YTD | Products Count | yes | Assortment card, Assortment matrix |
| Variance Purchases Products Count New/Dropped | Products Count | yes | Assortment card |
| Index Purchases Quantity Actual/Prior | Quantity | yes | Purchase table |
| Index Purchases Quantity Actual/Prior YTD | Quantity | yes | Supply card |
| Index Purchases Quantity Monthly Average Actual/Prior | Quantity | yes | Supply card |
| Purchases Quantity Actual Year | Quantity | yes | Supply combo chart, Supply card, Purchase table |
| Purchases Quantity Actual Year Monthly Average | Quantity | yes | Supply card |
| Purchases Quantity Prior Year | Quantity | yes | Supply combo chart, Purchase table |
| Purchases Quantity Prior Year YTD | Quantity | yes | Supply card |
| Index Purchases Value Actual/Prior | Value | yes | Purchase table |
| Index Purchases Value Actual/Prior YTD | Value | yes | Supply card |
| Index Purchases Value Monthly Average Actual/Prior | Value | yes | Supply card |
| Purchases Dropped Product Avg Value | Value | yes | Assortment card |
| Purchases Dropped Product Value | Value | yes | Assortment card, Assortment matrix, Assortment bar chart |
| Purchases New Product Avg Value | Value | yes | Assortment card |
| Purchases New Product Value | Value | yes | Assortment card, Assortment matrix, Assortment bar chart |
| Purchases Value Actual Year | Value | yes | Supply card, Supply combo chart, Purchase combo chart +1 |
| Purchases Value Actual Year Monthly Average | Value | yes | Supply card |
| Purchases Value Actual Year Share | Value | yes | Purchase bar chart |
| Purchases Value Prior Year | Value | yes | Supply combo chart, Purchase combo chart, Purchase table |
| Purchases Value Prior Year YTD | Value | yes | Supply card |

### Sales

| Measure | Folder | Visible | Used on |
|---|---|---|---|
| Sales Net Price Actual Year | Net Price | yes | inside 2 measures (Purchases Dropped Product Sales Share, …) |
<!-- register:end -->
