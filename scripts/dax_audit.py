"""Audit the model's DAX against the report: what is unused, what is duplicated, which
expression shapes repeat, and where the measures miss the standards.

Read-only on the model. python scripts/dax_audit.py [--strict] [--register] [--baseline file.dax]
                                                    [--compare before.csv after.csv] [--json file.json]
The summary prints. --strict then exits 1 if a count docs/dax-quality.md says is zero is not.
--register rewrites the measure register in docs/dax-quality.md. --baseline writes the
regression query run before and after a DAX change; --compare compares two runs of it.
--json writes every name behind every number.

A measure counts as used when a visual, page or filter of the report binds it, or when a used
measure references it. A measure no visual uses is still kept when the docs name it. Nothing
outside the report is visible here (Analyze in Excel, other reports on the model).
"""

import glob
import json
import os
import re
import sys
from collections import Counter, defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(REPO, "Purchasing.SemanticModel", "definition")
REPORT = os.path.join(REPO, "Purchasing.Report", "definition")
DOC = os.path.join(REPO, "docs", "dax-quality.md")


def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().replace("\r\n", "\n")


def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def indent(line):
    return len(line) - len(line.lstrip("\t"))


def unquote(name):
    name = name.strip()
    if name.startswith("'") and name.endswith("'"):
        return name[1:-1].replace("''", "'")
    return name


HEADER = re.compile(r"^(measure|column|calculationItem|function|table|partition|hierarchy|calculationGroup)\s+('(?:[^']|'')*'|[^\s=]+)\s*(=\s*(.*))?$")


def read_block(lines, i, base):
    """Collect expression lines after a header at indent `base`.

    Expression lines are deeper than base+1 or blank; a fenced ``` block runs to its close.
    Returns (expr_lines, next_index).
    """
    out = []
    n = len(lines)
    if i < n and lines[i].strip().startswith("```"):
        i += 1
        while i < n and not lines[i].strip().startswith("```"):
            out.append(lines[i])
            i += 1
        return out, i + 1
    while i < n:
        ln = lines[i]
        if ln.strip() == "":
            out.append(ln)
            i += 1
            continue
        if indent(ln) >= base + 2:
            out.append(ln)
            i += 1
            continue
        break
    while out and out[-1].strip() == "":
        out.pop()
    return out, i


def dedent(lines):
    nonblank = [l for l in lines if l.strip()]
    if not nonblank:
        return ""
    m = min(indent(l) for l in nonblank)
    return "\n".join(l[m:] if l.strip() else "" for l in lines).strip("\n")


def parse_tmdl_objects(path):
    """Yield dicts for measures, calc items, columns (with expressions), functions, partitions."""
    with open(path, encoding="utf-8-sig") as f:
        lines = f.read().split("\n")
    lines = [l.rstrip("\r") for l in lines]
    objs = []
    table = None
    desc = []
    i = 0
    n = len(lines)
    current = None
    while i < n:
        ln = lines[i]
        s = ln.strip()
        lvl = indent(ln)
        if s.startswith("///"):
            desc.append(s[3:].strip())
            i += 1
            continue
        m = HEADER.match(s)
        if m:
            kind, raw, has_eq, rest = m.group(1), m.group(2), m.group(3), m.group(4)
            name = unquote(raw)
            if kind == "table":
                table = name
                current = None
                desc = []
                i += 1
                continue
            obj = {"kind": kind, "table": table, "name": name, "line": i + 1,
                   "description": " ".join(desc), "props": {}, "file": os.path.relpath(path, REPO).replace(os.sep, "/")}
            desc = []
            i += 1
            expr_lines = []
            if has_eq:
                if rest and rest.strip() and not rest.strip().startswith("```"):
                    expr_lines = [rest]
                    more, i = read_block(lines, i, lvl)
                    expr_lines += more
                else:
                    if rest and rest.strip().startswith("```"):
                        i -= 1
                        more = []
                        i += 1
                        while i < n and not lines[i].strip().startswith("```"):
                            more.append(lines[i])
                            i += 1
                        i += 1
                        expr_lines = more
                    else:
                        more, i = read_block(lines, i, lvl)
                        expr_lines = more
            obj["expression"] = dedent(expr_lines) if len(expr_lines) > 1 or (expr_lines and indent(expr_lines[0]) > 0) else (expr_lines[0].strip() if expr_lines else "")
            # properties at lvl+1
            while i < n:
                pl = lines[i]
                ps = pl.strip()
                if ps == "":
                    i += 1
                    continue
                if indent(pl) <= lvl:
                    break
                if indent(pl) == lvl + 1:
                    pm = re.match(r"^(formatStringDefinition|detailRowsDefinition|expression|source)\s*=\s*(.*)$", ps)
                    if pm:
                        key, rest2 = pm.group(1), pm.group(2)
                        i += 1
                        if rest2.strip().startswith("```"):
                            more = []
                            while i < n and not lines[i].strip().startswith("```"):
                                more.append(lines[i])
                                i += 1
                            i += 1
                            obj["props"][key] = dedent(more)
                        elif rest2.strip():
                            more, i = read_block(lines, i, lvl + 1)
                            obj["props"][key] = (rest2 + ("\n" + dedent(more) if more else "")).strip()
                        else:
                            more, i = read_block(lines, i, lvl + 1)
                            obj["props"][key] = dedent(more)
                        continue
                    km = re.match(r"^([A-Za-z]+)\s*:\s*(.*)$", ps)
                    if km:
                        obj["props"][km.group(1)] = km.group(2).strip()
                    elif re.match(r"^[A-Za-z]+$", ps):
                        obj["props"][ps] = True
                    elif ps.startswith("annotation "):
                        am = re.match(r"^annotation\s+(\S+)\s*=\s*(.*)$", ps)
                        if am:
                            obj["props"]["annotation:" + am.group(1)] = am.group(2)
                    elif ps.startswith("changedProperty"):
                        obj["props"].setdefault("changedProperty", []).append(ps.split("=", 1)[1].strip())
                i += 1
            objs.append(obj)
            continue
        desc = [] if s and not s.startswith("///") else desc
        i += 1
    return objs


def strip_comments_strings(expr):
    """Remove DAX comments; replace string literals with empty strings."""
    out = []
    i, n = 0, len(expr)
    while i < n:
        c = expr[i]
        if expr.startswith("//", i) or expr.startswith("--", i):
            j = expr.find("\n", i)
            i = n if j < 0 else j
            continue
        if expr.startswith("/*", i):
            j = expr.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if c == '"':
            j = i + 1
            while j < n:
                if expr[j] == '"':
                    if j + 1 < n and expr[j + 1] == '"':
                        j += 2
                        continue
                    break
                j += 1
            out.append('""')
            i = j + 1
            continue
        out.append(c)
        i += 1
    return "".join(out)


REF = re.compile(r"('(?:[^']|'')+'|[A-Za-z_][A-Za-z0-9_\.]*)?\s*\[((?:[^\]]|\]\])+)\]")


def dax_refs(expr):
    code = strip_comments_strings(expr)
    refs = []
    for m in REF.finditer(code):
        t = m.group(1)
        c = m.group(2).replace("]]", "]")
        refs.append((unquote(t) if t else None, c))
    return refs


# ---------- what the model holds ----------
objs = []
for path in sorted(glob.glob(os.path.join(MODEL, "**", "*.tmdl"), recursive=True)):
    if os.sep + "cultures" + os.sep not in path:
        objs.extend(parse_tmdl_objects(path))
for o in objs:
    if o["kind"] == "partition" and o["props"].get("source"):
        o["expression"] = o["props"]["source"]
    o["refs"] = dax_refs(o.get("expression", ""))
    o["fs_refs"] = dax_refs(o["props"].get("formatStringDefinition", ""))
measures = [o for o in objs if o["kind"] == "measure"]
by_name = {m["name"].lower(): m for m in measures}
assert len(by_name) == len(measures), "duplicate measure names"
functions = {o["name"]: o for o in objs if o["kind"] == "function"}
analytic = [m for m in measures if m["table"] != "LabelMeasures"]

# captions per culture: measure name -> caption
captions = {}
for path in glob.glob(os.path.join(MODEL, "cultures", "*.tmdl")):
    captions[os.path.basename(path)[:-5]] = {
        unquote(m.group(1)): m.group(2)
        for m in re.finditer(r"\n\t\t\t\tmeasure ('(?:[^']|'')*'|[^\s\n]+)\n\t\t\t\t\tcaption: ([^\n]*)", load(path))}


# ---------- dependencies ----------
def measure_refs(refs):
    out = set()
    for t, c in refs:
        m = by_name.get(c.lower())
        if m and (t is None or t.lower() == m["table"].lower()):
            out.add(m["name"])
    return out


def func_calls(expr):
    code = strip_comments_strings(expr)
    return {f for f in functions if re.search(r"(?<![\w\.])" + re.escape(f) + r"\s*\(", code)}


deps, fdeps = {}, {}
for m in measures:
    deps[m["name"]] = (measure_refs(m["refs"]) | measure_refs(m["fs_refs"])) - {m["name"]}
    fdeps[m["name"]] = func_calls(m["expression"]) | func_calls(m["props"].get("formatStringDefinition", ""))
rdeps = defaultdict(set)
for a, bs in deps.items():
    for b in bs:
        rdeps[b].add(a)


def closure(seed):
    seen, stack = set(), list(seed)
    while stack:
        x = stack.pop()
        if x not in seen:
            seen.add(x)
            stack.extend(deps.get(x, ()))
    return seen


# ---------- what the report binds ----------
VISUAL_NAMES = {"cardVisual": "card", "card": "card", "pivotTable": "matrix", "tableEx": "table",
                "clusteredBarChart": "bar chart", "clusteredColumnChart": "column chart",
                "lineClusteredColumnComboChart": "combo chart",
                "barChart": "bar chart", "lineChart": "line chart", "donutChart": "donut",
                "actionButton": "button", "textbox": "text box", "slicer": "slicer",
                "advancedSlicerVisual": "slicer", "shape": "shape", "image": "image"}
bound = defaultdict(set)       # measure -> files that bind it
bindings = defaultdict(list)   # measure -> (page, visual kind)
unresolved = []


def walk(node, where, found):
    if isinstance(node, dict):
        for k, v in node.items():
            if k == "Measure" and isinstance(v, dict) and "Property" in v:
                found.append(v["Property"])
            walk(v, where, found)
    elif isinstance(node, list):
        for x in node:
            walk(x, where, found)


for path in sorted(glob.glob(os.path.join(REPORT, "**", "*.json"), recursive=True)):
    rel = os.path.relpath(path, REPO).replace(os.sep, "/")
    found = []
    data = load_json(path)
    walk(data, rel, found)
    page = None
    if os.path.basename(path) == "visual.json":
        page = load_json(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(path))), "page.json")).get("displayName")
        vt = data.get("visual", {}).get("visualType", "")
        kind = VISUAL_NAMES.get(vt, vt)
    for prop in found:
        m = by_name.get(prop.lower())
        if not m:
            unresolved.append((prop, rel))
            continue
        bound[m["name"]].add(rel)
        if page and (page, kind) not in bindings[m["name"]]:
            bindings[m["name"]].append((page, kind))

# a used measure reaches the functions it calls, and a used function the measures it reads
used, used_funcs = closure(bound), set()
grew = True
while grew:
    grew = False
    funcs = set().union(*(fdeps[n] for n in used))
    funcs |= {g for f in funcs | used_funcs for g in func_calls(functions[f]["expression"])}
    reads = closure(set().union(*(measure_refs(functions[f]["refs"]) for f in funcs))) if funcs else set()
    if funcs - used_funcs or reads - used:
        used_funcs |= funcs
        used |= reads
        grew = True

# the documents: a measure, or its folder, named in backticks is part of the design
DOC_TEXT = "\n".join(load(p) for p in sorted(glob.glob(os.path.join(REPO, "docs", "*.md"))) if p != DOC)


def documented(m):
    folder = m["props"].get("displayFolder", "")
    if f"`{m['name']}`" in DOC_TEXT:
        return m["name"]
    if folder and f"`{folder}`" in DOC_TEXT:
        return folder
    return None


doc_kept = {m["name"] for m in analytic if m["name"] not in used and documented(m)}
kept = used | closure(doc_kept)
unused = sorted(m["name"] for m in analytic if m["name"] not in kept)
unused_labels = sorted(m["name"] for m in measures if m["table"] == "LabelMeasures" and m["name"] not in used)
unused_functions = sorted(set(functions) - used_funcs - {f for n in kept for f in fdeps[n]})


# ---------- duplicates ----------
def norm(expr):
    code = strip_comments_strings(expr).lower()
    parts = re.split(r"(\[[^\]]*\]|'[^']*')", code)
    return "".join(p if i % 2 else re.sub(r"\s+", "", p) for i, p in enumerate(parts))


exact = defaultdict(list)
for m in analytic:
    exact[norm(m["expression"])].append(m["name"])
duplicates = [v for v in exact.values() if len(v) > 1]


def template(m):
    """The expression with every measure reference replaced by [@]: the shape it shares."""
    code = re.sub(r"\s+", " ", strip_comments_strings(m["expression"])).strip()
    refs = []

    def rep(mt):
        mm = by_name.get(mt.group(2).replace("]]", "]").lower())
        if mm and (mt.group(1) is None or mt.group(1).strip("' ").lower() == mm["table"].lower()):
            refs.append(mm["name"])
            return "[@]"
        return mt.group(0)
    return re.sub(r"('(?:[^']|'')+'|[A-Za-z_][\w\.]*)?\s*\[((?:[^\]]|\]\])+)\]", rep, code), refs


templates = defaultdict(list)
for m in analytic:
    t, refs = template(m)
    if refs and len(set(refs)) <= 2:
        templates[t].append(m["name"])
shapes = sorted((v for v in templates.values() if len(v) >= 3), key=len, reverse=True)

# ---------- the standards ----------
quality = defaultdict(list)
for m in analytic:
    n, p = m["name"], m["props"]
    code = strip_comments_strings(m["expression"])
    if not m["description"]:
        quality["measures without a description"].append(n)
    if "formatString" not in p and "formatStringDefinition" not in p and "isText" not in p.get("annotation:PBI_FormatHint", ""):
        quality["measures without a format"].append(n)
    if "displayFolder" not in p:
        quality["measures without a folder"].append(n)
    for v in re.findall(r"\bVAR\s+([A-Za-z_]\w*)", code, re.I):
        if not re.fullmatch(r"_[a-z0-9]+(_[a-z0-9]+)*", v):
            quality["variables without the _ prefix"].append(n)
            break
    if re.search(r'"(good|bad|neutral)"', m["expression"]):
        quality["colours not from RagColor"].append(n)
    if re.search(r"\bIFERROR\s*\(", code, re.I):
        quality["IFERROR"].append(n)
    if re.search(r"\bFILTER\s*\(\s*(ALL\s*\(\s*)?'?[A-Za-z][\w ]*'?\s*[,)]", code, re.I):
        quality["FILTER over a whole table"].append(n)
    # quantity x net price summed outside Sales Net Price, not divided back into a price per unit
    if re.search(r"FactInvoiceLine\s*\[\s*Quantity\s*\]\s*\*\s*FactInvoiceLine\s*\[\s*NetPrice\s*\]", code) and \
            not re.search(r"\bDIVIDE\s*\(", code, re.I) and n != "Sales Net Price":
        quality["sales rebuilt inline"].append(n)
    # quantity x supplier price summed outside Purchases Value, not divided back into a price per unit
    if re.search(r"FactInvoiceLine\s*\[\s*Quantity\s*\]\s*\*\s*FactInvoiceLine\s*\[\s*SupplierPrice\s*\]", code) and \
            not re.search(r"\bDIVIDE\s*\(", code, re.I) and n != "Purchases Value":
        quality["purchases rebuilt inline"].append(n)

caption_gaps = {c: sorted(m["name"] for m in analytic if not m["props"].get("isHidden") and m["name"] not in caps)
                for c, caps in captions.items()}


def visual_names():
    """Each field of a visual shows under its own caption: no text typed into a visual, and no
    two fields of one visual with the same caption."""
    typed, clashes = [], []
    for path in sorted(glob.glob(os.path.join(REPORT, "pages", "*", "visuals", "*", "visual.json"))):
        rel = os.path.relpath(path, REPO).replace(os.sep, "/")
        shown = []
        for x in load_json(path).get("visual", {}).get("query", {}).get("queryState", {}).values():
            for pr in x.get("projections", []):
                fld = pr["field"]
                k = next(iter(fld))
                if "displayName" in pr:
                    typed.append((rel, fld[k].get("Property"), pr["displayName"]))
                if k == "Measure":
                    shown.append(fld[k].get("Property"))
        for culture, caps in captions.items():
            for name, count in Counter(caps.get(s, s) for s in shown).items():
                if count > 1:
                    clashes.append((rel, culture, name))
    return typed, clashes


typed, clashes = visual_names()

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rag_colors  # noqa: E402 - a colour measure must match its index's RagColor annotation

colour_changes = rag_colors.build(load(rag_colors.PATH))[1]

folders = Counter(m["props"].get("displayFolder", "(no folder)") for m in analytic)


# ---------- the register ----------
def md_cell(s):
    return str(s).replace("|", "\\|")


def used_on(n):
    if bindings.get(n):
        places = [f"{page} {kind}" for page, kind in bindings[n]]
        return ", ".join(places[:3]) + (f" +{len(places) - 3}" if len(places) > 3 else "")
    users = sorted(u for u in rdeps.get(n, ()) if u in kept)
    if users:
        return f"inside {len(users)} measure{'s' if len(users) > 1 else ''} ({users[0]}{', …' if len(users) > 1 else ''})"
    if n in bound:
        return "a page or report filter"
    if n in kept:
        return "named in the docs"
    return "nothing"


def register_markdown():
    lines = [f"{len(analytic)} analytical measures.", ""]
    by_top = defaultdict(list)
    for m in analytic:
        folder = m["props"].get("displayFolder", "")
        top, _, sub = folder.partition("\\")
        by_top[top or "(no folder)"].append((sub, m))
    for top in sorted(by_top):
        lines += [f"### {top}", "", "| Measure | Folder | Visible | Used on |", "|---|---|---|---|"]
        for sub, m in sorted(by_top[top], key=lambda x: (x[0].lower(), x[1]["name"].lower())):
            visible = "no" if m["props"].get("isHidden") else "yes"
            lines.append(f"| {md_cell(m['name'])} | {md_cell(sub)} | {visible} | {md_cell(used_on(m['name']))} |")
        lines.append("")
    return "\n".join(lines).rstrip("\n")


def baseline_query():
    """One EVALUATE per folder: every kept numeric measure by year. Run before and after a change."""
    out = ["// Baseline: every kept numeric measure by DimDate[Year]. Generated by scripts/dax_audit.py --baseline.",
           "// Run it on the model open in Desktop before and after a DAX change; the results must match."]
    by_folder = defaultdict(list)
    for m in analytic:
        p = m["props"]
        if m["name"] in kept and ("formatString" in p or "formatStringDefinition" in p):
            by_folder[p.get("displayFolder", "")].append(m["name"])  # text measures carry no number
    for f in sorted(by_folder):
        out.append(f"\n// {f}\nEVALUATE\nSUMMARIZECOLUMNS(\n    DimDate[Year],")
        out.append(",\n".join(f'    "{n.replace(chr(34), chr(34) * 2)}", [{n.replace("]", "]]")}]' for n in by_folder[f]))
        out.append(")")
    return "\n".join(out) + "\n"


def compare(before_csv, after_csv, tolerance=1e-12):
    """Same measure, same year: a value may not appear, vanish or change. Numbers may differ in
    the last digits only: the engine's summation order moves the fifteenth digit between runs."""
    import csv
    with open(before_csv, encoding="utf-8") as f:
        a = list(csv.reader(f))
    with open(after_csv, encoding="utf-8") as f:
        b = list(csv.reader(f))
    ia, ib = {h: i for i, h in enumerate(a[0])}, {h: i for i, h in enumerate(b[0])}
    ra, rb = {r[0]: r for r in a[1:]}, {r[0]: r for r in b[1:]}
    problems, same = [], 0
    for col in a[0][1:]:
        if col not in ib:
            problems.append(f"{col}: missing after")
            continue
        for year in sorted(set(ra) | set(rb)):
            x = ra[year][ia[col]] if year in ra else ""
            z = rb[year][ib[col]] if year in rb else ""
            if x == z:
                same += 1
                continue
            try:
                fx, fz = float(x), float(z)
                if abs(fx - fz) <= tolerance * max(abs(fx), abs(fz)):
                    same += 1
                    continue
            except ValueError:
                pass
            problems.append(f"{col} {year}: {x!r} -> {z!r}")
    print(f"compared {same + len(problems)} values; differences: {len(problems)}")
    for p in problems[:50]:
        print("  ", p)
    return not problems


# ---------- output ----------
sys.stdout.reconfigure(encoding="utf-8")
args = sys.argv[1:]
if "--compare" in args:
    i = args.index("--compare")
    sys.exit(0 if compare(args[i + 1], args[i + 2]) else 1)
if "--baseline" in args:
    with open(args[args.index("--baseline") + 1], "w", encoding="utf-8") as f:
        f.write(baseline_query())
if "--register" in args:
    with open(DOC, encoding="utf-8", newline="") as f:
        text = f.read()
    nl = "\r\n" if "\r\n" in text else "\n"
    start, end = "<!-- register:start -->", "<!-- register:end -->"
    a, b = text.index(start) + len(start), text.index(end)
    with open(DOC, "w", encoding="utf-8", newline="") as f:
        f.write(text[:a] + nl + register_markdown().replace("\n", nl) + nl + text[b:])
    print("register written:", len(analytic), "measures")
if "--json" in args:
    with open(args[args.index("--json") + 1], "w", encoding="utf-8") as f:
        json.dump({"unused": unused, "unused_labels": unused_labels, "unused_functions": unused_functions,
                   "documented_not_bound": sorted(doc_kept), "duplicates": duplicates, "shapes": shapes,
                   "quality": quality, "caption_gaps": caption_gaps, "unresolved": unresolved,
                   "typed": typed, "clashes": clashes, "folders": folders,
                   "deps": {k: sorted(v) for k, v in deps.items()},
                   "bindings": bindings}, f, ensure_ascii=False, indent=1)

print(f"measures {len(analytic)} analytic, {len(measures) - len(analytic)} label; functions {len(functions)}; folders {len(folders)}")
print("bound in the report:", sum(1 for m in analytic if m["name"] in bound),
      "| reached through other measures:", sum(1 for m in analytic if m["name"] in used and m["name"] not in bound),
      "| kept because the docs name them:", len(kept - used))
ZERO = {
    "unresolved report references": unresolved,
    "unused measures": unused,
    "unused label measures": unused_labels,
    "unused functions": unused_functions,
    "exact duplicates": duplicates,
    "text typed into visuals": typed,
    "fields sharing one caption in a visual": clashes,
    "colour measures out of date": colour_changes,
}
ZERO.update({k: quality.get(k, []) for k in (
    "measures without a description", "measures without a format", "measures without a folder",
    "variables without the _ prefix", "colours not from RagColor", "IFERROR", "FILTER over a whole table",
    "sales rebuilt inline", "purchases rebuilt inline")})
ZERO.update({f"visible measures without a {c} caption": v for c, v in caption_gaps.items()})
for k, v in ZERO.items():
    print(f"{k}: {len(v)}" + (f"  {v[:3]}" if v else ""))
print(f"shapes shared by three or more measures: {len(shapes)}" + (f"  largest {len(shapes[0])}" if shapes else ""))

if "--strict" in args:
    broken = {k: len(v) for k, v in ZERO.items() if v}
    print()
    print("strict:", "; ".join(f"{k} {n}" for k, n in broken.items()) if broken else "every count that must be zero is zero")
    sys.exit(1 if broken else 0)
