"""在乾淨環境生成多稿。用法：send.py <書資料夾> <chNNNN> [稿數] [--model 模型]

已有的稿不會被覆蓋，編號接下去。送出前比對 prompt 和 cards/hidden/，只回報，不阻擋。
"""
import argparse
import concurrent.futures as cf
import json
import pathlib
import re
import subprocess
import sys
import tempfile

SYSTEM = "你是一位小說作者。"
MIN_MATCH = 8


def sentences(text):
    parts = re.split(r"[。！？\n]+", text)
    return [p.strip(" 　，、「」『』…-") for p in parts if len(p.strip(" 　，、「」『』…-")) >= MIN_MATCH]


def hidden_hits(book, prompt):
    hits = []
    for card in sorted((book / "cards" / "hidden").glob("*.md")):
        for s in sentences(card.read_text(encoding="utf-8")):
            if s in prompt:
                hits.append(f"{card.name}：{s}")
    return hits


def generate(prompt, out, model, cwd):
    cmd = ["claude", "-p", "--setting-sources", "", "--system-prompt", SYSTEM, "--tools", "",
           "--model", model, "--effort", "high", "--output-format", "json",
           "--no-session-persistence", "--strict-mcp-config", "--disable-slash-commands"]
    r = subprocess.run(cmd, input=prompt.encode("utf-8"), capture_output=True, cwd=cwd, timeout=1500)
    try:
        d = json.loads(r.stdout.decode("utf-8"))
    except ValueError:
        return f"{out.name} 失敗：{r.stderr.decode('utf-8', 'replace')[:300]}"
    if d.get("is_error"):
        return f"{out.name} 失敗：{d.get('result')}"
    out.write_text(d["result"], encoding="utf-8")
    return f"{out.name} 完成，{len(d['result'])} 字"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("book", type=pathlib.Path)
    ap.add_argument("chapter")
    ap.add_argument("n", type=int, nargs="?", default=3)
    ap.add_argument("--model", default="opus")
    a = ap.parse_args()

    folder = a.book / "drafts" / a.chapter
    prompt_file = folder / "prompt.md"
    if not prompt_file.exists():
        sys.exit(f"找不到 {prompt_file}")
    prompt = prompt_file.read_text(encoding="utf-8")

    hits = hidden_hits(a.book, prompt)
    print("水下比對：" + ("沒有命中" if not hits else "有命中"))
    for h in hits:
        print("  " + h)

    used = [int(m.group(1)) for f in folder.glob("稿*.md") if (m := re.fullmatch(r"稿(\d+)\.md", f.name))]
    start = max(used, default=0) + 1
    outs = [folder / f"稿{i}.md" for i in range(start, start + a.n)]
    with tempfile.TemporaryDirectory() as cwd, cf.ThreadPoolExecutor(a.n) as ex:
        results = list(ex.map(lambda o: generate(prompt, o, a.model, cwd), outs))
    for line in results:
        print(line)
    if any("失敗" in line for line in results):
        sys.exit(1)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
