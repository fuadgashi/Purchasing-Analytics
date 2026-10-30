"""mobile_check - space budget and component audit for the PBIR mobile layer.

    python scripts/mobile_check.py            every page
    python scripts/mobile_check.py Supply     one page
    python scripts/mobile_check.py --strict   exit 1 on any finding but CUSTOM

Read-only; runs from anywhere in the repo. For every visible visual it resolves each
component the mobile layer inherits or overrides, computes the usable content box, and
compares it to the demand. The rules are the ones in docs/mobile.md; a finding is a
candidate to confirm in Desktop, not a verdict.

Reading rules the script depends on:
  * selector-scoped entries are never read as a global value (per-column
    `columnWidth` is declared with selectors).
  * grid width is decided by `columnHeaders.columnAdjustment`, not by summing
    column widths; the standard is 'fixedWidth'.
  * a container title bound to a measure is the header band, not a title-shown
    violation, and its strip is its content, not chrome.
  * reference labels bind through objects.referenceLabel[].properties.value
    (a Measure) keyed by selector.id = field-<guid>, not through queryState.
  * tooltip pages are skipped - the phone shows their desktop layout.
"""
import collections
import glob
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / 'Purchasing.Report'
os.chdir(REPORT)

LH = 1.3
CHAR_W = 0.55
CANVAS = 324
DATA = {'pivotTable', 'tableEx', 'cardVisual', 'lineClusteredColumnComboChart',
        'clusteredBarChart', 'lineChart', 'barChart', 'clusteredColumnChart',
        'donutChart', 'areaChart', 'gauge'}
CUSTOM_PREFIX = 'htmlContent'
TXT = re.compile(r'(fontSize|textSize|FontSize)$')

# A canvas unit is not a CSS pixel: the 324u canvas maps to the device width, so
# 1u = deviceWidth/324. 25u clears WCAG's 24 CSS px on every common phone.
WCAG_TARGET = 24
HOUSE_TARGET = 25

GUTTER = 10      # between blocks
GAP = 20         # empty scroll between two blocks beyond this is a finding
HEADER_ZONE = 250   # content origin: the page header above it is not checked for frames


def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def lit(p):
    try:
        return p['expr']['Literal']['Value']
    except (KeyError, TypeError):
        return None


def num(x):
    if x is None:
        return None
    try:
        return float(str(x).rstrip('LD'))
    except ValueError:
        return None


class V:
    def __init__(self, vdir):
        self.v = load(vdir + 'visual.json')
        self.m = load(vdir + 'mobile.json') if os.path.exists(vdir + 'mobile.json') else None
        self.t = self.v['visual']['visualType']
        self.pos = (self.m or {}).get('position', {})
        self.hidden = bool(self.v.get('isHidden'))

    def raw(self, obj, prop):
        """selector-less only; mobile wins over desktop. Returns (value, 'M'|'D'|'-')."""
        for bag in ('objects', 'visualContainerObjects'):
            for src, tag in (((self.m or {}).get(bag), 'M'), (self.v['visual'].get(bag), 'D')):
                for e in (src or {}).get(obj, []) or []:
                    if 'selector' in e:
                        continue
                    if prop in (e.get('properties') or {}):
                        return e['properties'][prop], tag
        return None, '-'

    def get(self, obj, prop):
        return lit(self.raw(obj, prop)[0])

    def src(self, obj, prop):
        return self.raw(obj, prop)[1]

    def n(self, obj, prop):
        return num(self.get(obj, prop))

    def maxfont(self, obj, prop='fontSize'):
        """EFFECTIVE size: most specific selector wins, mobile before desktop at
        the same scope."""
        for pred in (lambda sel: sel is not None and 'metadata' in sel,
                     lambda sel: sel is not None and sel.get('id') == 'default',
                     lambda sel: sel is None):
            for bag in ('objects', 'visualContainerObjects'):
                for src in ((self.m or {}).get(bag), self.v['visual'].get(bag)):
                    for e in (src or {}).get(obj, []) or []:
                        if not pred(e.get('selector')):
                            continue
                        x = num(lit((e.get('properties') or {}).get(prop)))
                        if x:
                            return x
        return None

    def ref_slots(self):
        """Reference labels bind through objects.referenceLabel[].properties.value
        (a Measure) with selector.id = field-<guid> - not through queryState."""
        ids, meas = set(), []
        for src in ((self.m or {}).get('objects'), self.v['visual'].get('objects')):
            for grp in ('referenceLabel', 'referenceLabelTitle',
                        'referenceLabelValue', 'referenceLabelDetail'):
                for e in (src or {}).get(grp, []) or []:
                    sid = (e.get('selector') or {}).get('id', '')
                    if isinstance(sid, str) and sid.startswith('field-'):
                        ids.add(sid)
                    val = (e.get('properties') or {}).get('value')
                    if val and 'Measure' in json.dumps(val):
                        meas.append(val)
        return len(ids), len(meas)

    def roles(self):
        q = self.v['visual'].get('query', {}).get('queryState', {})
        return {k: len(x.get('projections', [])) for k, x in q.items()}

    def title_text(self):
        t, _ = self.raw('title', 'text')
        if t is None:
            return ''
        v = lit(t)
        return v.strip("'") if isinstance(v, str) else '<measure>'

    def title_is_measure(self):
        t, _ = self.raw('title', 'text')
        return t is not None and 'Literal' not in json.dumps(t)

    def page_link(self):
        return self.get('visualLink', 'show') == 'true' and \
            self.get('visualLink', 'type') == "'PageNavigation'"


# The type scale from docs/mobile.md. Total and subtotal rows are left out on
# purpose: they follow the desktop formatting (reset to default on the phone).
SCALE = {'callout': 12, 'above': 9, 'button': 9, 'inside': 8, 'tab': 8, 'caption': 8}
INSIDE = {
    ('pivotTable', 'values', 'fontSize'), ('pivotTable', 'rowHeaders', 'fontSize'),
    ('pivotTable', 'columnHeaders', 'fontSize'), ('pivotTable', 'grid', 'textSize'),
    ('tableEx', 'values', 'fontSize'), ('tableEx', 'columnHeaders', 'fontSize'),
    ('tableEx', 'grid', 'textSize'),
    ('*', 'categoryAxis', 'fontSize'), ('*', 'categoryAxis', 'titleFontSize'),
    ('*', 'valueAxis', 'fontSize'), ('*', 'valueAxis', 'titleFontSize'),
    ('*', 'y2Axis', 'fontSize'), ('*', 'y2Axis', 'secFontSize'),
    ('*', 'legend', 'fontSize'), ('*', 'labels', 'fontSize'),
    ('*', 'labels', 'detailFontSize'), ('*', 'target', 'fontSize'),
    ('cardVisual', 'label', 'fontSize'),
    ('cardVisual', 'referenceLabelTitle', 'titleFontSize'),
    ('cardVisual', 'referenceLabelValue', 'valueFontSize'),
    ('cardVisual', 'referenceLabelDetail', 'detailFontSize'),
    ('slicer', 'items', 'textSize'), ('slicer', 'date', 'textSize'),
    ('slicer', 'header', 'textSize'),
}


def scale_for(vis, grp, prop):
    """(tier label, wanted pt) for this property, or None if it is not typed.
    Action buttons are typed by their role on screen, not by visualType: the slicer
    captions (Button1 .. Button5) and the page tabs (visible, PageNavigation link)
    take 8pt; every other button takes the 9pt tier."""
    t = vis.title_text()
    if grp == 'text' and prop == 'fontSize':
        if vis.t == 'actionButton' and re.fullmatch(r'Button\d', t):
            return 'caption', SCALE['caption']
        if vis.t == 'actionButton' and not vis.hidden and vis.page_link():
            return 'tab', SCALE['tab']
    if (vis.t, grp, prop) in INSIDE or ('*', grp, prop) in INSIDE:
        return 'inside', SCALE['inside']
    if (vis.t, grp, prop) == ('cardVisual', 'value', 'fontSize'):
        return 'callout', SCALE['callout']
    if grp in ('title', 'subTitle') and prop == 'fontSize':
        return 'above', SCALE['above']
    if vis.t in ('actionButton', 'shape') and grp == 'text' and prop == 'fontSize':
        return 'button', SCALE['button']
    return None


def text_scale(vis, pg):
    """Every typed text size against the scale."""
    ref = f"{pg}/{vis.t[:24]}"
    box = f"{vis.pos['width']}x{vis.pos['height']}"
    seen, bad = set(), []
    for bag in ('objects', 'visualContainerObjects'):
        for src in (vis.m.get(bag), vis.v['visual'].get(bag)):
            for grp, arr in (src or {}).items():
                for e in arr or []:
                    for prop in (e.get('properties') or {}):
                        if not TXT.search(prop):
                            continue
                        hit = scale_for(vis, grp, prop)
                        if not hit or (grp, prop) in seen:
                            continue
                        seen.add((grp, prop))
                        # a title nobody shows is not a type defect
                        if grp in ('title', 'subTitle'):
                            sh = vis.get(grp, 'show')
                            if sh == 'false' or (sh is None and vis.t in ('actionButton', 'shape')):
                                continue
                        tier, want = hit
                        cur = vis.maxfont(grp, prop)
                        if cur is not None and cur != want:
                            bad.append(f"{grp}.{prop} {cur:g} (want {want})")
    return [('TEXT', ref, box, '; '.join(sorted(bad)))] if bad else []


FRAME = ('border', 'background', 'padding')


def frame(vis, pg):
    """On data visuals below the header zone, border, background and padding are
    declared together - all three (values or [] = reset to default) or none.
    One left out falls to Power BI's system default, not to the theme: the wrong
    border colour and radius. visualHeader is left as it is."""
    if vis.t in ('actionButton', 'shape', 'image', 'textbox') or vis.hidden:
        return []
    if vis.pos['y'] < HEADER_ZONE:
        return []
    vco = vis.m.get('visualContainerObjects') or {}
    have = [k for k in FRAME if k in vco]
    if not have or len(have) == len(FRAME):
        return []
    miss = [k for k in FRAME if k not in have]
    return [('FRAME', f"{pg}/{vis.t[:24]}", f"{vis.pos['width']}x{vis.pos['height']}",
             f"mobile declares {', '.join(have)}; missing {', '.join(miss)}")]


def budget(vis):
    w, h = vis.pos['width'], vis.pos['height']
    eaten = []
    pl, pr = vis.n('padding', 'left') or 0, vis.n('padding', 'right') or 0
    ptop, pb = vis.n('padding', 'top') or 0, vis.n('padding', 'bottom') or 0
    if pl or pr or ptop or pb:
        eaten.append(f"padding {pl:.0f}/{ptop:.0f}/{pr:.0f}/{pb:.0f}")
    w -= pl + pr
    h -= ptop + pb
    if vis.get('border', 'show') == 'true':
        bw = vis.n('border', 'width') or 1
        w -= 2 * bw
        h -= 2 * bw
        eaten.append(f"border {bw:.0f}x2")
    # a measure-bound title IS the visual's content (header button) - not chrome
    if vis.get('title', 'show') != 'false' and not vis.title_is_measure():
        fs = vis.n('title', 'fontSize') or 12
        strip = fs * LH + (vis.n('spacing', 'spaceBelowTitle') or 5)
        h -= strip
        eaten.append(f"title {strip:.0f}")
    if vis.get('subTitle', 'show') == 'true':
        fs = vis.n('subTitle', 'fontSize') or 10
        strip = fs * LH + (vis.n('spacing', 'spaceBelowSubTitle') or 5)
        h -= strip
        eaten.append(f"subtitle {strip:.0f}")
    return w, h, eaten


def target(vis, pg):
    """Tap-target check. Decided by the link, not the visual type: an image or
    shape with a live visualLink is a control."""
    if vis.get('visualLink', 'show') != 'true':
        return []
    ref, box = f"{pg}/{vis.t[:24]}", f"{vis.pos['width']}x{vis.pos['height']}"
    side = min(vis.pos['width'], vis.pos['height'])
    name = vis.title_text() or vis.t
    if side < WCAG_TARGET:
        return [('TARGET', ref, box, f"{name} {side:.0f}u - under WCAG 2.5.8's {WCAG_TARGET} on every device")]
    if side < HOUSE_TARGET:
        return [('TARGET', ref, box, f"{name} {side:.0f}u - clears WCAG but under the {HOUSE_TARGET}u house minimum")]
    return []


def check(vis, pg):
    uw, uh, eaten = budget(vis)
    ref = f"{pg}/{vis.t[:24]}"
    box = f"{vis.pos['width']}x{vis.pos['height']}"

    if uw <= 0 or uh <= 0:
        return [('CONTAINER', ref, box, f"chrome consumes the visual: {', '.join(eaten)}")]

    out = target(vis, pg)

    if vis.t.startswith(CUSTOM_PREFIX):
        return out + [('CUSTOM', ref, box, "custom visual - no layout model; verify in Desktop")]

    if vis.t in ('pivotTable', 'tableEx'):
        fl = vis.roles()
        cols = sum(fl.values()) if vis.t == 'tableEx' else (
            fl.get('Rows', 0) + fl.get('Values', 0) * max(1, fl.get('Columns', 0)))
        # grids keep their desktop column widths on the phone and scroll sideways:
        # columnAdjustment 'fixedWidth', widths untouched
        adj = vis.get('columnHeaders', 'columnAdjustment')
        if adj != "'fixedWidth'":
            out.append(('GRIDFIT', ref, box,
                        f"columnAdjustment {adj} from {vis.src('columnHeaders', 'columnAdjustment')} "
                        f"- the standard is 'fixedWidth' ({cols} cols)"))
        vfs = vis.n('values', 'fontSize') or 10
        hfs = vis.n('columnHeaders', 'fontSize') or 10
        rowh = max(vfs, hfs) * LH + (vis.n('grid', 'rowPadding') or 3)
        rows_fit = int((uh - rowh) // rowh)
        if rows_fit < 6:
            out.append(('ROWS', ref, box, f"row {rowh:.0f}u -> {rows_fit} data rows in {uh:.0f}u"))
        if vis.get('visualHeader', 'show') == 'false':
            out.append(('FOCUS', ref, box,
                        f"visualHeader.show=false from {vis.src('visualHeader', 'show')} "
                        f"- no ellipsis, so no focus mode on a {cols}-column grid"))

    elif vis.t == 'cardVisual':
        tiles = sum(vis.roles().values()) or 1
        cols = vis.n('layout', 'columnCount') or 1
        rows = vis.n('layout', 'rowCount') or -(-tiles // int(cols))
        mt = vis.n('layout', 'maxTiles')
        cell = vis.n('layout', 'cellPadding') or 0
        fixed = vis.get('layout', 'showFixedSize') == 'true'
        fh, fw = vis.n('layout', 'fixedHeight'), vis.n('layout', 'fixedWidth')
        tile_h = fh if (fixed and fh) else uh / max(rows, 1) - cell
        tile_w = fw if (fixed and fw) else uw / max(cols, 1) - cell
        cs = (vis.n('layout', 'calloutSize') or 35) / 100
        band = cs * tile_h
        vfs = vis.maxfont('value') or 12
        lfs = vis.maxfont('label') or 10
        if mt and mt < tiles:
            out.append(('TILECAP', ref, box, f"maxTiles {mt:.0f} < {tiles} fields - {tiles - int(mt)} never render"))
        # `fixedWidth` only constrains a card whose tiles run horizontally; with
        # `orientation: 1` they stack vertically and the width is not applied.
        orient = vis.n('layout', 'orientation')
        if fixed and fw and fw > uw + 0.5 and orient != 1:
            out.append(('TILEW', ref, box, f"fixedWidth {fw:.0f} > {uw:.0f}u usable"))
        if band < vfs * LH:
            out.append(('CALLOUT', ref, box,
                        f"band {band:.1f}u < {vfs:.0f}pt line {vfs * LH:.1f}u (tile {tile_w:.0f}x{tile_h:.0f}, {cs * 100:.0f}%)"))
        if tile_h - band < lfs * LH:
            out.append(('LABEL', ref, box, f"{tile_h - band:.1f}u under the callout, {lfs:.0f}pt label needs {lfs * LH:.1f}u"))
        nslots, nmeas = vis.ref_slots()
        # reference slots belong to a tile, not to the visual
        ntiles = max(int(mt) if mt else tiles, 1)
        nmeas = -(-nmeas // ntiles) if ntiles > 1 else nmeas
        if vis.maxfont('referenceLabelValue', 'valueFontSize') and nslots == 0:
            out.append(('INERT', ref, box, "referenceLabel fonts declared, no field-guid slot bound"))
        if nslots:
            rvfs = vis.maxfont('referenceLabelValue', 'valueFontSize') or 10
            rtfs = vis.maxfont('referenceLabelTitle', 'titleFontSize') or 10
            vspace = vis.n('spacing', 'verticalSpacing') or 2
            rowh = max(rvfs, rtfs) * LH + vspace
            need = vfs * LH + nmeas * rowh
            if need > tile_h + 0.5:
                out.append(('TILEBUDGET', ref, box,
                            f"callout {vfs:.0f}pt ({vfs * LH:.1f}u) + {nmeas} ref rows x {rowh:.1f}u "
                            f"= {need:.1f}u > tile {tile_h:.0f}u"))
            elif band + nmeas * rowh > tile_h + 0.5:
                out.append(('TILEBUDGET', ref, box,
                            f"band {band:.1f}u + {nmeas} ref rows x {rowh:.1f}u "
                            f"= {band + nmeas * rowh:.1f}u > tile {tile_h:.0f}u"))

    elif vis.t == 'slicer':
        ifs = vis.n('items', 'textSize') or 10
        if ifs * LH + 12 > uh + 0.5:
            out.append(('SLICER', ref, box, f"{ifs:.0f}pt item needs {ifs * LH + 12:.0f}u, {uh:.0f}u usable"))

    elif vis.t == 'actionButton':
        tfs = vis.n('text', 'fontSize') or 12
        if not vis.title_is_measure() and tfs * LH > uh + 0.5:
            out.append(('BUTTON', ref, box, f"{tfs:.0f}pt text needs {tfs * LH:.0f}u, {uh:.0f}u usable"))

    elif vis.t in DATA:
        chrome = 0
        if vis.get('categoryAxis', 'show') != 'false':
            chrome += (vis.n('categoryAxis', 'fontSize') or 9) * LH + 4
        if vis.get('legend', 'show') == 'true':
            chrome += (vis.n('legend', 'fontSize') or 9) * LH + 6
        if vis.get('categoryAxis', 'showAxisTitle') == 'true':
            chrome += (vis.n('categoryAxis', 'titleFontSize') or 9) * LH
        if uh - chrome < uh * 0.55:
            out.append(('PLOT', ref, box, f"axis+legend {chrome:.0f}u of {uh:.0f}u -> plot {100 * (uh - chrome) / uh:.0f}%"))
    return out


def page_flow(pg, items):
    """Page-level rules, on the visible visuals of one page.
    GAP: the page scrolls as far as its furthest visual, so empty space between two
    blocks is scroll with nothing in it. A visual that starts inside another (a card
    framing a grid, a card inside a chart's corner) is not a gap.
    ORDER: tab order follows the phone reading order, ascending by (y, x)."""
    out = []
    reach = None
    for vis in sorted(items, key=lambda v: (v.pos['y'], v.pos['x'])):
        y, bottom = vis.pos['y'], vis.pos['y'] + vis.pos['height']
        if reach is not None and y - reach > GAP:
            out.append(('GAP', f"{pg}/{vis.t[:24]}", f"{vis.pos['width']}x{vis.pos['height']}",
                        f"starts at {y:.0f}, {y - reach:.0f}u below the block above (gutter {GUTTER}u)"))
        reach = bottom if reach is None else max(reach, bottom)
    # TABS: the page-tab row spans the canvas edge to edge, with no hole between tabs
    tabs = sorted((v for v in items if v.t == 'actionButton' and v.page_link()), key=lambda v: v.pos['x'])
    edge = 0
    for v in tabs:
        if abs(v.pos['x'] - edge) > 0.5:
            out.append(('TABS', f"{pg}/tab row", '', f"tab at x={v.pos['x']:.0f}, the row reached x={edge:.0f}"))
        edge = v.pos['x'] + v.pos['width']
    if tabs and abs(edge - CANVAS) > 0.5:
        out.append(('TABS', f"{pg}/tab row", '', f"the row ends at x={edge:.0f}, not at the canvas edge {CANVAS}"))
    by_place = sorted(items, key=lambda v: (v.pos['y'], v.pos['x']))
    orders = [v.pos.get('tabOrder', 0) for v in by_place]
    for i in range(1, len(orders)):
        if orders[i] < orders[i - 1]:
            v = by_place[i]
            out.append(('ORDER', f"{pg}/{v.t[:24]}", f"{v.pos['width']}x{v.pos['height']}",
                        f"tabOrder {orders[i]} at ({v.pos['x']:.0f},{v.pos['y']:.0f}) comes before "
                        f"{orders[i - 1]} placed above it"))
    return out


def fonts():
    """One family, Segoe UI; weight from `bold`, never from the family name. Microsoft's
    base theme under SharedResources is overridden, not edited, so it is not read."""
    out = []
    for path in glob.glob('definition/**/*.json', recursive=True) + \
            glob.glob('StaticResources/RegisteredResources/*.json'):
        with open(path, encoding='utf-8-sig') as f:
            for i, line in enumerate(f, 1):
                m = re.search(r'Segoe UI (Bold|Semibold|Light)', line)
                if m:
                    out.append(('FONT', f"{path}:{i}", '', f"'{m.group(0)}' - use Segoe UI with bold"))
    return out


pages, tooltip = {}, set()
for f in glob.glob('definition/pages/*/page.json'):
    d = load(f)
    pages[d['name']] = d.get('displayName', '')
    if d.get('type') == 'Tooltip':
        tooltip.add(d['name'])
pages_named = [a for a in sys.argv[1:] if not a.startswith('--')]
only = pages_named[0] if pages_named else None
strict = '--strict' in sys.argv
if only and only not in pages.values():
    sys.exit(f"mobile_check: no page named {only!r} - pages are {', '.join(sorted(pages.values()))}")

findings, scanned = [], 0
visible = collections.defaultdict(list)
for d in sorted(glob.glob('definition/pages/*/visuals/*/')):
    pid = os.path.normpath(d).split(os.sep)[-3]
    pg = pages[pid]
    if pid in tooltip or (only and pg != only):
        continue
    vis = V(d)
    if vis.m is None:
        findings.append(('MISSING', f"{pg}/{vis.t[:24]}", '', f"{d}mobile.json is missing - every visual has one"))
        continue
    if vis.hidden:
        findings += target(vis, pg) + text_scale(vis, pg)
        continue
    scanned += 1
    visible[pg].append(vis)
    findings += check(vis, pg) + text_scale(vis, pg) + frame(vis, pg)
for pg, items in sorted(visible.items()):
    findings += page_flow(pg, items)
if not only:
    findings += fonts()

print(f"mobile_check - {scanned} visible visuals" + (f" on {only}" if only else " report-wide"))
print(f"assumptions: line height {LH}x pt, glyph {CHAR_W}x pt, 9-glyph figure, canvas {CANVAS}u")
print()
by = collections.Counter(f[0] for f in findings)
if not findings:
    print("  no findings")
for k, n in by.most_common():
    print(f"  {k:<10}{n}")
print()
for cls, _ in by.most_common():
    for c, ref, box, msg in [f for f in findings if f[0] == cls]:
        print(f"  {cls:<10}{ref:<34}{box:<10}{msg}")

# docs/mobile.md: CUSTOM (a custom visual with no layout model) is the only class left
# open on purpose; any other is work to do.
if strict:
    open_ones = [f for f in findings if f[0] != 'CUSTOM']
    print()
    print(f"strict: {len(open_ones)} finding(s) outside CUSTOM")
    sys.exit(1 if open_ones else 0)
