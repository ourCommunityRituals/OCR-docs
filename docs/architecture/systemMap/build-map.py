#!/usr/bin/env python3
"""Check infrastructure-map.json, and build the page when template.html is present.

Usage: python3 build-map.py [output.html]
In OCR-docs this only checks the JSON: the page template carries its own colours,
so it lives with the owner's project files and artifact, not in this repo
(the design-system check keeps OCR-docs free of its own styles).
Where template.html sits next to this script, it also writes the page.
"""
import json, sys, pathlib
here = pathlib.Path(__file__).parent
data = json.loads((here / "infrastructure-map.json").read_text())
# Basic checks so a typo fails here, not on the page.
for e in data["edges"]:
    for n in [e["from"], *(e["to"] if isinstance(e["to"], list) else [e["to"]])]:
        assert n in data["nodes"], f"edge {e['id']} names unknown node {n}"
for v in data["views"]:
    for n in v["place"]:
        assert n in data["nodes"], f"view {v['id']} places unknown node {n}"
    ids = {e["id"] for e in data["edges"]}
    for eid in v["edges"]:
        assert eid in ids, f"view {v['id']} lists unknown edge {eid}"
for k, n in data["nodes"].items():
    assert n["status"] in data["statuses"], f"node {k} has unknown status {n['status']}"
tpl = here / "template.html"
if not tpl.exists():
    print(f"checked {len(data['nodes'])} nodes, {len(data['edges'])} edges, {len(data['views'])} views: OK (no template.html here, so no page built)")
    sys.exit(0)
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
html = tpl.read_text().replace("/*__MAP_DATA__*/null", blob)
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here / "infrastructure-map.html"
out.write_text(html)
print(f"wrote {out} ({len(html)//1024} KB)")
