# Mobile layout

[← README](../README.md)

The standard for the phone layer of the report. Nothing here changes the desktop canvas.
`scripts/mobile_check.py` checks the report against it.

- [How the layer works](#how-the-layer-works)
- [Which pages have a phone layout](#which-pages-have-a-phone-layout)
- [Type scale](#type-scale)
- [Fonts](#fonts)
- [Canvas and geometry](#canvas-and-geometry)
- [Page structure](#page-structure)
- [Component rules](#component-rules)
- [Checking](#checking)
- [Not standardised](#not-standardised)

## How the layer works

Every visual has a `mobile.json` beside its `visual.json`:

```
definition/pages/<page>/visuals/<id>/
    visual.json     desktop
    mobile.json     phone - position, objects, visualContainerObjects
```

**It overrides per property, not per visual.** A property `mobile.json` does not declare
takes the desktop value [[mobile-format-visuals]](sources.md#mobile-format-visuals), and a
property desktop does not declare takes the theme or Power BI's default
[[theme-defaults]](sources.md#theme-defaults). Most of what the phone shows is inherited, so
*silence is not neutral*: a property missing from `mobile.json` is a desktop decision arriving
on a 324-unit canvas.

**Clear mobile changes** reconnects a setting to the desktop layout
[[mobile-format-visuals]](sources.md#mobile-format-visuals); in the files a cleared object is an
empty entry (for example `"total": []`).

**It restyles and repositions; it cannot add or remove.** There is no `isHidden` in
`mobile.json` [[pbir-mobile-schema]](sources.md#pbir-mobile-schema). Visibility lives in
`visual.json` and is shared by both layouts, so there are no phone-only visuals: anything the
phone needs is a desktop container first, and hiding one on desktop hides it on the phone.

**The render is the authority on appearance.** What a reader sees comes from five layers: the
theme (`visualStyles`), `visual.json`, `mobile.json`, the model's captions
(`cultures/en-US.tmdl`) and the text label measures return. The files are authoritative for
geometry, inheritance and wiring. Anything about how a visual *looks* is confirmed in the
Desktop mobile view or on a phone.

## Which pages have a phone layout

| Pages | Phone layout |
| --- | --- |
| `Supply`, `Purchase`, `Assortment` | yes — the standard applies |

## Type scale

```
card callout ..................... 12 pt
container title / subTitle ........ 9 pt
button text ....................... 9 pt
page-tab strip .................... 8 pt
slicer captions (Button1 - Button5) 8 pt
anything inside a visual .......... 8 pt
total and subtotal rows ........... desktop formatting
```

- **Inside a visual**: text the visual draws in its own plot, grid or tile — cells, row and
  column headers, axes, legends, data labels, card labels and reference labels, slicer items.
- **Callout**: the single figure a `cardVisual` exists to show. Its own tier, never pulled down
  to 8.
- **Buttons** take 9, except the two rows in the tight header band: the page tabs (visible
  action buttons with a `PageNavigation` link) and the five slicer captions. Both are 8, so
  every label fits its box on every page and the strip is uniform. A button is typed by its
  role on screen, not by its `visualType`.
- **Total and subtotal rows** are reset to default on the phone, so they carry the desktop
  formatting. Do not restyle them in `mobile.json`.

**Below Microsoft's 9 pt floor [[mobile-best-practices]](sources.md#mobile-best-practices), on
purpose.** On a 324-unit canvas, 8 pt is what keeps a formatted figure (nine characters, about
40 u at 8 pt) inside a column, and more columns on screen before the grid scrolls.

## Fonts

**One family, `Segoe UI`. Weight comes from `bold`, never from the family name.**

```
'''Segoe UI'', wf_segoe-ui_normal, helvetica, arial, sans-serif'   + bold true | false
```

`Segoe UI Bold`, `Segoe UI Semibold` and `Segoe UI Light` are not used anywhere — theme,
`visual.json` or `mobile.json`. The rule applies at the source, not only in `mobile.json`,
because the phone inherits desktop and theme values.

- Card reference values use `valueFontFamily` + `valueBold`, not `fontFamily` + `bold`.
- `textClasses` has `fontFace` and no bold, so weights are set in `visualStyles`.
- The registered theme (`cortnes-light.json`) sets `Segoe UI` + `bold: true` for container
  titles, grid column headers, the slicer header, the button title, the card value and card
  reference values. The `cardVisual` block matters: Microsoft's base theme sets the card value
  to `Segoe UI Semibold` [[ms-base-theme]](sources.md#ms-base-theme), and this block is what
  overrides it.
- Subtitles stay regular, with no font declared.
- Slicer captions (`Button1` – `Button5`) are bold on desktop and regular on the phone: their
  `mobile.json` carries an explicit `bold: false`.

`mobile_check.py` reports any of the three family names as `FONT`. Microsoft's base theme under
`SharedResources` still names them; it is overridden, not edited, and not read.

## Canvas and geometry

```
canvas width ............ 324 u
header band ............. y = 30 to 275
content origin .......... y = 285
gutter between blocks ... 10 u
chart inset ............. x = 10, width 304 (Supply's monthly charts, inside their card)
tap target minimum ...... 25 u on the shorter side
```

The inset holds only for the charts framed by a card. Every other chart, table and card runs
the full width: x = 0, 324 u.

**Tap targets.** Anything with a live `visualLink` — buttons, slicers, images, shapes — is at
least 25 u on its shorter side. WCAG 2.5.8 asks for 24 × 24 CSS px
[[wcag-target-size]](sources.md#wcag-target-size); a canvas unit is the device width over 324,
so 25 u clears it on every common phone. There is no exception.

## Page structure

**Page tabs.** One row at the top, y = 0, 25 u tall: Supply · Purchase · Assortment,
three tabs of 108 u that span the canvas edge to edge. There is no menu button and no drawer; the tabs are the
whole navigation, on the phone as on desktop.

**Header band.** One full-width `actionButton` carries the page title as a measure-bound
container title and backs the five slicer rows (y = 85 to 260, a 35 u pitch): a caption button
of 130 u on the left, its slicer of 200 u on the right. It is the one non-data visual that
shows a title.

**Content** starts at y = 285 and runs down the page in reading order, 10 u apart.

- **Nothing on the canvas is sticky.** Every visual scrolls with the page. The mobile app's own
  footer (Pages list, swipe between pages [[mobile-app-reports]](sources.md#mobile-app-reports))
  is always reachable, so changing page never depends on the tab row. The slicers are only at
  the top: a reader scrolls back up to change a filter.
- **A page scrolls as far as its last visual**, so nothing sits below the content and there is
  no empty band between blocks. `GAP` reports one.
- **Tab order follows the phone reading order**, ascending by `(y, x)`. `ORDER` reports a visual
  reached before one placed above it.

## Component rules

Properties of PBIR and Power BI, so they hold on any page.

- **The container frame.** On data visuals below the header zone (y = 250), `border`,
  `background` and `padding` are declared in `mobile.json` together — all three (values or
  `[]`, Reset to default, meaning "follow desktop and the theme") or none. A partial set is the
  defect. `visualHeader` is set per visual and is not part of this rule.
- **Grids are `fixedWidth`.** Every table and matrix keeps its desktop column widths on the
  phone and scrolls sideways: `columnHeaders.columnAdjustment` is `fixedWidth`, and the
  per-column `columnWidth` values are not changed.
- **Focus mode needs the header.** `visualHeader.show: false` removes the header icons
  [[format-pane-header]](sources.md#format-pane-header), and on a phone focus mode opens from
  the ellipsis [[mobile-phone-report]](sources.md#mobile-phone-report). Grids wider than the
  canvas keep their header.
- **Card reference labels are not in `queryState`.** They bind through
  `objects.referenceLabel[].properties.value` keyed by `field-<guid>`. Count those selectors to
  know what a card shows.
- **Card callout band = `fixedHeight × calloutSize`.** The callout needs `pt × 1.3`; the rest of
  the tile holds the reference rows, each `max(valuePt, titlePt) × 1.3 + verticalSpacing`. Both
  must fit.
- **A card can frame a chart.** On `Supply` the volume card is a panel: each volume's tile
  sits at the top of its block, and its monthly chart in the block's lower part. A visual that
  starts inside another is not a gap.
- **Unset is not off.** A missing property means the theme or Power BI decides; confirm on the
  render what each one shows.
- **A tap target is its link, not its type.** An image or shape with `visualLink.show: true` is
  a control.
- **Labels come from the model.** Displayed names are the `caption:` entries in
  `cultures/en-US.tmdl`, and titles the text label measures read from `Labels` — not the names
  in the report files.
- **Siblings drift by omission.** Visuals with the same role rarely disagree on a value; they
  differ in which properties they declare. Compare key sets, and check geometry separately from
  formatting.

## Checking

```
python scripts/mobile_check.py            every page
python scripts/mobile_check.py Supply     one page
python scripts/mobile_check.py --strict   exit 1 on any finding but CUSTOM
```

Runs from anywhere in the repo and only reads files. It resolves each property mobile →
desktop, computes the usable box after padding, border and title, and compares it with what the
content needs. Assumptions (printed on every run): line height 1.3 × pt, glyph width 0.55 × pt,
a nine-glyph formatted figure.

| Class | Meaning |
| --- | --- |
| `TEXT` | a size off the type scale |
| `FONT` | a weight named in the family (`Segoe UI Bold`, `Semibold`, `Light`) |
| `FRAME` | a data visual declares only some of border / background / padding |
| `GRIDFIT`, `ROWS`, `FOCUS` | grids (`GRIDFIT`: not on `fixedWidth`) |
| `TILEW`, `TILECAP`, `TILEBUDGET`, `CALLOUT`, `LABEL`, `INERT` | card tiles |
| `TARGET` | a tap target under 25 u |
| `BUTTON`, `SLICER`, `PLOT`, `CONTAINER` | content does not fit its box |
| `TABS` | the tab row leaves a hole or stops short of the canvas edge |
| `GAP` | empty scroll between two blocks |
| `ORDER` | tab order out of reading order |
| `MISSING` | a visual with no `mobile.json` |
| `CUSTOM` | custom visual with no layout model — check in Desktop |

A finding is a candidate to confirm in Desktop, not a verdict. The check runs in CI with
`--strict` and reports nothing today.

**Edit these files with Desktop closed.** Desktop and an external edit can overwrite each other
([maintenance.md](maintenance.md#before-you-edit)). Close Desktop first; after the edit, open a
fresh session, check, save. Afterwards confirm the layer survived: nearly every `mobile.json`
should still carry `objects` or `visualContainerObjects`.

## Not standardised

Left to each page on purpose:

- **Page height.** Set by content, not by a template.
- **Card sizing and tile geometry.** Per page, within the tile budget.

**What the phone carries is decided:** every page has a phone layout, and it carries every
visual and grid column, as on desktop. A visual added to the report
gets a `mobile.json` like the rest.
