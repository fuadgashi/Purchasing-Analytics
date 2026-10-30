# Sources

[← README](../README.md)

**Every statement in these documents about how something outside the project behaves — Power BI Desktop and the service, DAX, Power Query M, TMDL and PBIR, SQL Server, the mobile app, or an outside standard — cites an entry here. A statement with no entry is not written.** What the model and the report themselves do needs no citation: the files are the record.

A citation looks like [[relationships]](#relationships): the entry's name, linking here. Each entry gives the page, what it is cited for, and the date it was read. Power BI changes monthly, so an entry is re-read before a change relies on it, and its date updated. `scripts/docs_check.py` fails on a citation with no entry and on an entry nothing cites.

## Microsoft Learn — Power BI projects (PBIP, TMDL, PBIR)

### desktop-publish

[Publish semantic models and reports from Power BI Desktop](https://learn.microsoft.com/power-bi/create-reports/desktop-upload-desktop-files#republish-or-replace-a-semantic-model-published-from-power-bi-desktop)
— publishing creates a semantic model with the same name as the Desktop file;
republishing replaces the model of that name, and a renamed file creates a new one.
Read 2026-10-08.

### pbip-external-editing

[Edit PBIP files outside Power BI Desktop](https://learn.microsoft.com/power-bi/developer/projects/projects-external-editing)
— Desktop writes its changes to the files only on save; with the preview *Detect
and reload external PBIP changes* (August 2026 release or later) it offers
**Apply external changes**, which discards unsaved Desktop changes; it does not
reload `cache.abf`; `unappliedChanges.json` discards external expression
changes; Desktop and external tools can overwrite each other. Read 2026-10-07.

### pbip-overview

[Power BI Desktop projects](https://learn.microsoft.com/power-bi/developer/projects/projects-overview#changes-outside-power-bi-desktop)
— one project folder can hold several reports and semantic models; `report.json`, `mobileState.json`, `semanticModelDiagramLayout.json` and
`diagramLayout.json` don't support editing outside Desktop; changes outside
Desktop can stop the project opening. Read 2026-10-08.

### pbip-semantic-model

[Power BI Desktop project semantic model folder](https://learn.microsoft.com/power-bi/developer/projects/projects-dataset)
— `.pbi\cache.abf` holds a local copy of the model *and data* and should be
git-ignored; an invalid TMDL edit shows an error with the location to fix when
the change is applied or the project opened. Read 2026-10-07.

## Microsoft Learn — data, model and DAX

### pq-folding

[Query folding guidance in Power BI Desktop](https://learn.microsoft.com/power-bi/guidance/power-query-folding)
— the mashup engine can't fold query steps after a native SQL query. Read
2026-10-07.

### data-access-options

[Model.DataAccessOptions](https://learn.microsoft.com/dotnet/api/microsoft.analysisservices.tabular.model.dataaccessoptions?view=analysisservices-dotnet)
and [DataAccessOptions](https://learn.microsoft.com/dotnet/api/microsoft.analysisservices.tabular.dataaccessoptions?view=analysisservices-dotnet)
— a model's data access options are options for the M data engine;
`returnErrorValuesAsNull` (the property ReturnErrorValuesAsNull) is whether individual
query errors are returned as nulls in the query result instead of failing the query,
and `legacyRedirects` (LegacyRedirects) whether unsafe legacy redirects from HTTPS to
HTTP are enabled. Read 2026-10-11.

### translations

[Translations in tabular models](https://learn.microsoft.com/analysis-services/tabular-models/translations-in-tabular-models-analysis-services)
— translations are for object metadata (names and descriptions), not data
values. Read 2026-10-07.

### relationships

[Model relationships in Power BI Desktop](https://learn.microsoft.com/power-bi/transform-model/desktop-relationships-understand)
— a single-direction relationship filters from the one side to the many side;
several paths of the same priority and weight return an ambiguous path error.
Read 2026-10-07.

### sql-from

[FROM clause plus JOIN (Transact-SQL)](https://learn.microsoft.com/sql/t-sql/queries/from-transact-sql#inner)
— `INNER` returns matching pairs of rows and discards unmatched rows from both
tables. Read 2026-10-07.

## Microsoft Learn — report

### dynamic-format-strings

[Create dynamic format strings for measures](https://learn.microsoft.com/power-bi/create-reports/desktop-dynamic-format-strings)
— a dynamic format string keeps the measure numeric; single quotes make the
formatted string a literal; set a visual's display units from Auto to None when
they alter how the format string shows. Read 2026-10-07.

### theme-defaults

[Visual defaults in Power BI reports](https://learn.microsoft.com/power-bi/create-reports/power-bi-reports-visual-defaults)
— styling set on a visual takes precedence over the theme's defaults. Read
2026-10-07.

### format-pane-header

[Format pane General tab overview](https://learn.microsoft.com/power-bi/visuals/power-bi-visualization-format-pane-overview#header-icons)
— turning **Header icons** off hides every header icon, including *More
options* and *Focus mode*. Read 2026-10-07.

### pbir-mobile-schema

[PBIR visual container mobile state schema](https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definition/visualContainerMobileState)
— `mobile.json` holds `position`, `objects` and `visualContainerObjects`; it has
no `isHidden` (version 2.7.0 read; the report's files also use 2.8.0, not yet
published). Read 2026-10-07.

### ms-base-theme

`Purchasing.Report/StaticResources/SharedResources/BaseThemes/CY25SU12.json`,
Microsoft's base theme as Desktop ships it into the project — sets the
`cardVisual` value font to `Segoe UI Semibold`. Read 2026-10-07.

## Microsoft Learn — mobile

### mobile-format-visuals

[Optimize visual formatting](https://learn.microsoft.com/power-bi/create-reports/power-bi-create-mobile-optimized-report-format-visuals)
— most mobile format settings take their value from the desktop layout until
changed; a changed setting is independent; **Clear mobile changes** reconnects
it; size and position are never inherited. Read 2026-10-07.

### mobile-best-practices

[Best practices for creating mobile-optimized reports](https://learn.microsoft.com/power-bi/create-reports/power-bi-create-mobile-optimized-report-best-practices)
— "Don't use fonts smaller than nine points"; add only significant and regularly
used visuals to the mobile layout. Read 2026-10-07.

### mobile-phone-report

[View Power BI reports optimized for your phone](https://learn.microsoft.com/power-bi/explore-reports/mobile/mobile-apps-view-phone-report#open-visuals-in-focus-mode)
— on a phone, focus mode opens from the visual's ellipsis (**...**). Read
2026-10-07.

### mobile-app-reports

[Explore reports in the Power BI mobile apps](https://learn.microsoft.com/power-bi/explore-reports/mobile/mobile-reports-in-the-mobile-apps#interact-with-reports)
— the report footer lists all pages; swiping from the screen edge moves between
pages. Read 2026-10-07. A long tap (tap and hold) on a data point shows its tooltip,
and a report page tooltip replaces the default one; report tooltips need a device of
at least 640 pixels and a 320-pixel viewport, below that the app shows default
tooltips. Read 2026-10-12.

## Standards

### wcag-target-size

[WCAG 2.2, Understanding 2.5.8 Target Size (Minimum)](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html)
— a pointer target is at least 24 × 24 CSS pixels, with listed exceptions. Read
2026-10-07.

