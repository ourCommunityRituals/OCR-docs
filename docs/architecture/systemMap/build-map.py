#!/usr/bin/env python3
"""Build infrastructure-map.html from infrastructure-map.json and template.html.

Usage: python3 build-map.py [output.html]
Edit the JSON (nodes, edges, views), run this, then republish the HTML to the same artifact link.
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
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
html = (here / "template.html").read_text().replace("/*__MAP_DATA__*/null", blob)
out = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else here / "infrastructure-map.html"
out.write_text(html)
print(f"wrote {out} ({len(html)//1024} KB)")
