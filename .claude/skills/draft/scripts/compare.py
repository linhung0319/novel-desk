"""把各稿排成並排的 HTML。用法：compare.py <書資料夾> <chNNNN> [--mark 片段 片段 ...]"""
import argparse
import html
import pathlib
import re
import sys

PAGE = """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><title>{title}</title>
<style>
:root {{ color-scheme: light dark; --bg: #fbfaf7; --fg: #24221e; --line: #d9d5cb; --mark: #f4dc8f; --markfg: #24221e; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg: #1d1c1a; --fg: #e6e2d8; --line: #45423b; --mark: #6b5a1e; --markfg: #f4eed8; }} }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--bg); color: var(--fg); font-family: "Noto Serif TC", "Microsoft JhengHei", serif; }}
main {{ display: grid; grid-template-columns: repeat({n}, minmax(24em, 1fr)); height: 100vh; overflow-x: auto; }}
section {{ overflow-y: auto; padding: 0 1.2em 3em; border-right: 1px solid var(--line); }}
h2 {{ position: sticky; top: 0; margin: 0; padding: .7em 0; background: var(--bg); font-size: 1em; }}
p {{ line-height: 1.8; margin: 0 0 .9em; }}
mark {{ background: var(--mark); color: var(--markfg); }}
</style></head><body><main>{columns}</main></body></html>
"""


def render(text, pattern):
    out = []
    for para in filter(None, (p.strip() for p in text.split("\n"))):
        body = html.escape(para, quote=False)
        if pattern:
            body = re.sub(pattern, lambda x: f"<mark>{x.group(0)}</mark>", body)
        out.append(f"<p>{body}</p>")
    return "\n".join(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book", type=pathlib.Path)
    ap.add_argument("chapter")
    ap.add_argument("--mark", nargs="*", default=[])
    a = ap.parse_args()

    folder = a.book / "drafts" / a.chapter
    found = [(int(m.group(1)), f) for f in folder.glob("稿*.md") if (m := re.fullmatch(r"稿(\d+)\.md", f.name))]
    if not found:
        sys.exit(f"{folder} 裡沒有稿件")
    marks = sorted({html.escape(m, quote=False) for m in a.mark if m}, key=len, reverse=True)
    pattern = "|".join(map(re.escape, marks))
    columns = []
    missing = set(marks)
    for i, f in sorted(found):
        text = f.read_text(encoding="utf-8")
        escaped = html.escape(text, quote=False)
        missing -= {m for m in marks if m in escaped}
        columns.append(f"<section><h2>稿{i}</h2>\n{render(text, pattern)}</section>")
    out = folder / "並排.html"
    out.write_text(PAGE.format(title=f"{a.chapter} 並排", n=len(found), columns="\n".join(columns)), encoding="utf-8")
    print(out)
    for m in sorted(missing):
        print("沒找到：" + html.unescape(m))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
