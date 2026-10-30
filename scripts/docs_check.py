"""Check the documents: links, anchors, citations, and the names they put in backticks.

Read-only. python scripts/docs_check.py
Exit code 1 on any finding. Reads README.md, CLAUDE.md and docs/*.md:
  links      every relative link reaches a file, and its #anchor a heading in that file
  citations  every [[name]](sources.md#name) has an entry `### name` in docs/sources.md, the
             label matches the anchor, and every entry is cited at least once
  names      every `Table[Column]` exists; every other name in backticks that looks like a model
             or project name - an identifier, or words joined by spaces - names a table, column,
             measure, function, page, query group, file, or a word of the model's source code
Fenced code blocks are skipped.
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS = [os.path.join(ROOT, "README.md"), os.path.join(ROOT, "CLAUDE.md")] + \
    sorted(glob.glob(os.path.join(ROOT, "docs", "*.md")))
findings = []
# Names that exist outside the repository: the default branch, and files Power BI Desktop
# writes or documents (git-ignored, or not in this project).
OUTSIDE = {"main", "cache.abf", "diagramLayout.json", "mobileState.json", "unappliedChanges.json",
           "semanticModelDiagramLayout.json",
           # font names the phone standard rules out: by design used nowhere
           "Segoe UI Bold", "Segoe UI Light"}


def read(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().replace("\r", "")


def slug(heading):
    """GitHub's heading anchor: lowercase, punctuation dropped, spaces to hyphens."""
    s = re.sub(r"[`*_]", "", heading.strip().lower())
    s = re.sub(r"[^\w\- ]", "", s)
    return s.replace(" ", "-")


def prose(text):
    """The document without fenced code blocks."""
    return re.sub(r"^```.*?^```", "", text, flags=re.S | re.M)


# --- what exists -------------------------------------------------------------------
model = os.path.join(ROOT, "Purchasing.SemanticModel", "definition")
tables, columns, names = set(), {}, set()
corpus_words = set()
for path in glob.glob(os.path.join(model, "**", "*.tmdl"), recursive=True):
    text = read(path)
    corpus_words |= set(re.findall(r"[A-Za-z_]\w*", text)) | set(re.findall(r"[A-Za-z_][\w.]*\w", text))
    names |= set(re.findall(r"^\t+caption: (.+)$", text, re.M))
    names |= set(re.findall(r"^cultureInfo (\S+)", text, re.M))
    t = re.search(r"^table ('(?:[^']|'')+'|\S+)", text, re.M)
    if t:
        table = t.group(1).strip("'")
        tables.add(table)
        columns[table] = {c.strip("'") for c in re.findall(r"^\tcolumn ('(?:[^']|'')+'|\S+)", text, re.M)}
        names |= columns[table]
        names |= {m.strip("'") for m in re.findall(r"^\tmeasure ('(?:[^']|'')+'|[^\s=]+)", text, re.M)}
    names |= set(re.findall(r"^function (\w+)", text, re.M))
    names |= set(re.findall(r"^queryGroup (\w+)", text, re.M))
    names |= set(re.findall(r"^expression (\w+)", text, re.M))
# the report's property names and values, and the scripts' own words (check classes)
phrases = ""
for path in glob.glob(os.path.join(ROOT, "Purchasing.Report", "**", "*.json"), recursive=True) + \
        glob.glob(os.path.join(ROOT, "scripts", "*.py")):
    text = read(path)
    phrases += "\n" + text
    corpus_words |= set(re.findall(r"[A-Za-z_]\w*", text)) | set(re.findall(r"[A-Za-z_][\w.]*\w", text))
for path in glob.glob(os.path.join(ROOT, "Purchasing.Report", "definition", "pages", "*", "page.json")):
    names |= set(re.findall(r'"displayName": "([^"]+)"', read(path)))
names |= tables
files = set()
for dirpath, dirnames, filenames in os.walk(ROOT):
    dirnames[:] = [d for d in dirnames if d != ".git"]
    for f in filenames:
        rel = os.path.relpath(os.path.join(dirpath, f), ROOT).replace(os.sep, "/")
        files |= {rel, f}
    files |= {os.path.relpath(dirpath, ROOT).replace(os.sep, "/"), os.path.basename(dirpath)}

# --- per document ------------------------------------------------------------------
sources_path = os.path.join(ROOT, "docs", "sources.md")
entries = set(re.findall(r"^### ([\w-]+)$", read(sources_path), re.M))
cited = set()
headings = {p: {slug(h) for h in re.findall(r"^#{1,6} (.+)$", prose(read(p)), re.M)} for p in DOCS}

for path in DOCS:
    rel = os.path.relpath(path, ROOT)
    text = prose(read(path))
    for label, target in re.findall(r"\[((?:\[[^\]]*\]|[^\]])*)\]\(([^)\s]+)\)", text):
        if re.match(r"https?://|mailto:", target):
            continue
        file_part, _, anchor = target.partition("#")
        dest = os.path.normpath(os.path.join(os.path.dirname(path), file_part)) if file_part else path
        if not os.path.exists(dest):
            findings.append(f"{rel}: link to missing {target}")
            continue
        if anchor:
            if dest.endswith(".md"):
                known = headings.get(dest) or {slug(h) for h in re.findall(r"^#{1,6} (.+)$", prose(read(dest)), re.M)}
                if anchor not in known:
                    findings.append(f"{rel}: anchor #{anchor} not in {os.path.relpath(dest, ROOT)}")
        if os.path.abspath(dest) == os.path.abspath(sources_path) and label.startswith("[") and path != sources_path:
            name = label.strip("[]")
            cited.add(anchor)
            if name != anchor:
                findings.append(f"{rel}: citation [[{name}]] links to #{anchor}")
            if anchor not in entries:
                findings.append(f"{rel}: citation {anchor} has no entry in docs/sources.md")
    for code in re.findall(r"`([^`\n]+)`", text):
        m = re.fullmatch(r"'?([\w ]+?)'?\[([^\]]+)\]", code)
        if m:
            table, col = m.groups()
            if table in columns and col not in columns[table]:
                findings.append(f"{rel}: `{code}` - no column {col} in {table}")
            elif table not in columns:
                findings.append(f"{rel}: `{code}` - no table {table}")
            continue
        if re.search(r"[(){}=<>…\\|,:;#\"'+*]|^\d|\.\.|^-", code):
            continue  # an expression, a path pattern or a fragment, not a name
        bare = code.rstrip("/")
        if bare in names or bare in files or bare in corpus_words or bare in OUTSIDE \
                or any(f.endswith("/" + bare) for f in files) \
                or (" " in bare and re.search(r"(?<!\w)" + re.escape(bare) + r"(?!\w)", phrases)):
            continue
        if re.fullmatch(r"[A-Za-z_][\w./-]*", code) or re.fullmatch(r"[A-Z][\w/%-]*(?: [\w/%-]+)+", code):
            findings.append(f"{rel}: `{code}` names nothing in the model, the report or the repository")

for entry in sorted(entries - cited):
    findings.append(f"docs/sources.md: entry {entry} is cited nowhere")

print("\n".join(findings))
print(f"{len(DOCS)} files, {len(entries)} sources, {len(findings)} findings")
sys.exit(1 if findings else 0)
