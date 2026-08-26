#!/usr/bin/env python3
"""Regenerate topics.json from https://github.com/ASSERT-KTH/topics (current/).

Usage: python3 dashboard/update-topics.py   (needs `gh` authenticated, or set GITHUB_TOKEN)
"""
import base64
import json
import re
import subprocess
from pathlib import Path

OUT = Path(__file__).parent / "topics.json"


def gh_api(path):
    return json.loads(subprocess.check_output(["gh", "api", path]))


def latex_to_text(s):
    s = re.sub(r"(?m)^\s*%.*$", "", s)                      # comment lines
    s = re.sub(r"(?<!\\)%.*", "", s)                        # trailing comments
    s = re.sub(r"\\href\{[^}]*\}\{([^}]*)\}", r"\1", s)     # \href{url}{text} -> text
    s = re.sub(r"\\url\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\emph\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\textbf\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\*?(\[[^\]]*\])?(\{[^}]*\})?", "", s)  # other commands
    s = s.replace("~", " ").replace("\\&", "&").replace("\\%", "%").replace("\\_", "_")
    return re.sub(r"\s+", " ", s).strip()


def parse_topic(tex):
    cat = re.search(r"%\s*category:\s*(.+)", tex)
    title = re.search(r"\\subsubsection\{([^}]*)\}", tex)
    if not title:
        return None
    body = tex[title.end():]
    # description: text up to the reference list / hidden task comment
    for stop in (r"\begin{enumerate}", r"\begin{comment}", r"\begin{itemize}"):
        idx = body.find(stop)
        if idx != -1:
            body = body[:idx]
    desc = latex_to_text(body)
    desc = re.sub(r"^Description:\s*", "", desc)
    return {
        "category": latex_to_text(cat.group(1)) if cat else "Other",
        "title": latex_to_text(title.group(1)),
        "description": desc,
    }


def main():
    files = gh_api("repos/ASSERT-KTH/topics/contents/current")
    topics = []
    for f in files:
        if not f["name"].endswith(".tex") or f["name"].startswith("_"):
            continue
        blob = gh_api(f"repos/ASSERT-KTH/topics/contents/current/{f['name']}")
        topic = parse_topic(base64.b64decode(blob["content"]).decode("utf-8"))
        if topic:
            topics.append(topic)
            print(f"  {topic['category']}: {topic['title']}")

    # group by category, preserving file order
    categories = []
    by_cat = {}
    for t in topics:
        if t["category"] not in by_cat:
            by_cat[t["category"]] = []
            categories.append(t["category"])
        by_cat[t["category"]].append({"title": t["title"], "description": t["description"]})

    OUT.write_text(json.dumps(
        {
            "source": "https://github.com/ASSERT-KTH/topics",
            "categories": [{"name": c, "topics": by_cat[c]} for c in categories],
        },
        indent=2, ensure_ascii=False) + "\n")
    print(f"wrote {OUT} ({len(topics)} topics, {len(categories)} categories)")


if __name__ == "__main__":
    main()
