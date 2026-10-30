"""Check the model and the report: every reference resolves, and nothing publishable leaks.

Read-only. python scripts/model_check.py
Exit code 1 on any finding. Checks, in order:
  model    every Table[Column], [Measure] and function call in DAX resolves; every sortByColumn
           exists; every relationship joins existing columns of one data type; every table,
           column, measure and function carries a /// description
  report   every field a visual, page or filter binds exists in the model; every internal field
           id (queryRef) names a model object; every page link, tooltip page and image exists
  publish  no e-mail address outside example.com, no IPv4 address, no currency symbol and no
           letter outside the Latin scripts in any tracked text file
"""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL = os.path.join(ROOT, "Purchasing.SemanticModel", "definition")
REPORT = os.path.join(ROOT, "Purchasing.Report")
findings = []

DAX_FUNCTIONS = set("""ABS ADDCOLUMNS ALL ALLEXCEPT AND AVERAGE AVERAGEX BLANK CALCULATE CALCULATETABLE
COALESCE COUNTROWS DATE DATEADD DATEDIFF DISTINCTCOUNT DIVIDE EDATE EXCEPT FALSE FILTER FIRSTNONBLANK
FORMAT HASONEVALUE IF IN ISBLANK ISEMPTY KEEPFILTERS LOOKUPVALUE MAX MIN MINX NATURALINNERJOIN NOT OR
RELATED REMOVEFILTERS ROUND SELECTCOLUMNS SELECTEDMEASURE SELECTEDVALUE SUBSTITUTE SUM SUMMARIZE SUMX
SWITCH TODAY TREATAS TRUE UNICHAR USERPRINCIPALNAME VALUES YEAR""".split())


def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().replace("\r", "")


def name(token):
    return token.strip("'").replace("''", "'")


# --- model -------------------------------------------------------------------------
columns, types, measures = {}, {}, set()
dax = ""
for path in sorted(glob.glob(os.path.join(MODEL, "tables", "*.tmdl"))):
    text = read(path)
    table = name(re.search(r"^table ('(?:[^']|'')+'|\S+)", text, re.M).group(1))
    columns[table] = set()
    for m in re.finditer(r"^\tcolumn ('(?:[^']|'')+'|\S+)\n\t\tdataType: (\w+)", text, re.M):
        columns[table].add(name(m.group(1)))
        types[(table, name(m.group(1)))] = m.group(2)
    for m in re.finditer(r"^\tmeasure ('(?:[^']|'')+'|[^\s=]+)", text, re.M):
        measures.add(name(m.group(1)))
    for m in re.finditer(r"sortByColumn: (\S+)", text):
        if name(m.group(1)) not in columns[table]:
            findings.append(f"model: {table} sorts by missing column {m.group(1)}")
    lines = text.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^(table|\tcolumn|\tmeasure) ('(?:[^']|'')+'|[^\s=]+)", line)
        if m and not (i and lines[i - 1].lstrip("\t").startswith("///")):
            findings.append(f"model: {table}: {m.group(1).strip()} {name(m.group(2))} has no description")
    body = re.sub(r"\tpartition [\s\S]*?(?=\n\tannotation|\Z)", "", text)  # M, not DAX
    dax += "\n".join(l for l in body.split("\n") if not re.match(r"\s*(///|--)", l)) + "\n"

ftext = read(os.path.join(MODEL, "functions.tmdl"))
functions = set(re.findall(r"^function (\w+)", ftext, re.M))
flines = ftext.split("\n")
for i, line in enumerate(flines):
    if line.startswith("function ") and not (i and flines[i - 1].startswith("///")):
        findings.append(f"model: function {line.split()[1]} has no description")
dax += "\n".join(l for l in flines if not re.match(r"\s*(///|--)", l))
dax = re.sub(r'"(?:[^"]|"")*"', '""', dax)  # string literals

for m in re.finditer(r"(?:'((?:[^']|'')+)'|\b([A-Za-z_]\w*))\[([^\]]+)\]", dax):
    table, col = name(m.group(1) or m.group(2)), m.group(3)
    if table in columns and col not in columns[table]:
        findings.append(f"model: {table}[{col}] does not exist")
    elif table not in columns:
        findings.append(f"model: table {table} does not exist ({table}[{col}])")
for m in re.finditer(r"(?<![\w'\]])\[([^\]@]+)\]", dax):
    if m.group(1) not in measures:
        findings.append(f"model: measure [{m.group(1)}] does not exist")
for m in re.finditer(r"\b([A-Za-z]\w*)\s*\(", dax):
    fn = m.group(1)
    if fn not in functions and fn.upper() not in DAX_FUNCTIONS and fn not in ("function", "expr", "val", "anyref"):
        findings.append(f"model: function {fn}( is neither DAX nor defined")

for a, b in re.findall(r"fromColumn: (\S+)\s+toColumn: (\S+)", read(os.path.join(MODEL, "relationships.tmdl"))):
    ends = [tuple(name(p) for p in x.split(".", 1)) for x in (a, b)]
    for t, c in ends:
        if c not in columns.get(t, ()):
            findings.append(f"model: relationship column {t}.{c} does not exist")
    if types.get(ends[0]) != types.get(ends[1]):
        findings.append(f"model: relationship {a} -> {b} joins {types.get(ends[0])} to {types.get(ends[1])}")

# --- report ------------------------------------------------------------------------
objects = {t: columns[t] | set() for t in columns}
for path in glob.glob(os.path.join(MODEL, "tables", "*.tmdl")):
    text = read(path)
    table = name(re.search(r"^table ('(?:[^']|'')+'|\S+)", text, re.M).group(1))
    objects[table] |= {name(x) for x in re.findall(r"^\tmeasure ('(?:[^']|'')+'|[^\s=]+)", text, re.M)}
pages_dir = os.path.join(REPORT, "definition", "pages")
pages = {p for p in os.listdir(pages_dir) if os.path.isdir(os.path.join(pages_dir, p))}
refs = 0


def walk(node, where, aliases):
    global refs
    if isinstance(node, dict):
        if isinstance(node.get("From"), list):
            aliases = {**aliases, **{f["Name"]: f["Entity"] for f in node["From"] if "Name" in f and "Entity" in f}}
        expr = node.get("Expression")
        if "Property" in node and isinstance(expr, dict) and isinstance(expr.get("SourceRef"), dict):
            refs += 1
            entity = expr["SourceRef"].get("Entity") or aliases.get(expr["SourceRef"].get("Source"))
            if node["Property"] not in objects.get(entity, ()):
                findings.append(f"report: {where} binds {entity}[{node['Property']}], which does not exist")
        for key, value in node.items():
            if isinstance(value, str) and key in ("queryRef", "metadata", "queryName"):
                m = re.match(r"^(?:\w+\()?([^.()]+)\.(.+?)\)?$", value)
                if not m or m.group(2) not in objects.get(m.group(1), ()):
                    findings.append(f"report: {where} field id {value!r} names no model object")
            else:
                walk(value, where, aliases)
    elif isinstance(node, list):
        for item in node:
            walk(item, where, aliases)


for path in glob.glob(os.path.join(REPORT, "definition", "**", "*.json"), recursive=True):
    where = os.path.relpath(path, ROOT)
    with open(path, encoding="utf-8-sig") as f:
        data = json.load(f)
    walk(data, where, {})
    text = json.dumps(data)
    for pid in re.findall(r'"navigationSection": \{"expr": \{"Literal": \{"Value": "\'(\w+)\'"', text):
        if pid not in pages:
            findings.append(f"report: {where} links to missing page {pid}")
    for pid in re.findall(r'"visualTooltip".{0,300}?"section": \{"expr": \{"Literal": \{"Value": "\'(\w+)\'"', text):
        if pid not in pages:
            findings.append(f"report: {where} uses missing tooltip page {pid}")
    for image in re.findall(r"'([\w-]+\.(?:png|jpg|svg))'", text):
        if not os.path.exists(os.path.join(REPORT, "StaticResources", "RegisteredResources", image)):
            findings.append(f"report: {where} shows missing image {image}")

# --- publish -----------------------------------------------------------------------
TEXT = (".tmdl", ".json", ".md", ".py", ".yml", ".pbip", ".pbir", ".pbism", ".gitignore", ".gitattributes")
# the author's contact, allowed in the licence notice only
CONTACT = {"README.md": "fuaddi.g@gmail.com", "LICENSE": "fuaddi.g@gmail.com"}
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d not in (".git", "__pycache__")]
    for f in filenames:
        if not f.endswith(TEXT) and f != "LICENSE":
            continue
        path = os.path.join(dirpath, f)
        if os.path.abspath(path) == os.path.abspath(__file__):
            continue
        for i, line in enumerate(read(path).split("\n"), 1):
            where = f"{os.path.relpath(path, ROOT)}:{i}"
            for mail in re.findall(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+", line):
                if not mail.endswith("@example.com") and CONTACT.get(os.path.relpath(path, ROOT)) != mail:
                    findings.append(f"publish: {where} holds an e-mail address")
            if re.search(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", line):
                findings.append(f"publish: {where} holds an IP address")
            if re.search(r"[^\x00-\u024F\u2000-\u2BFF]", line):
                findings.append(f"publish: {where} holds a letter outside the Latin scripts")
            if re.search(r"[\u00A2-\u00A5\u20A0-\u20C0]", line):
                findings.append(f"publish: {where} holds a currency")

print("\n".join(sorted(set(findings))))
print(f"{len(measures)} measures, {len(functions)} functions, {sum(map(len, columns.values()))} columns, "
      f"{len(columns)} tables; {refs} report field references; {len(set(findings))} findings")
sys.exit(1 if findings else 0)
