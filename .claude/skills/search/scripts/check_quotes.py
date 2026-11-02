"""核對引文是否逐字存在。用法：check_quotes.py <書資料夾> <來源> <引文> [<來源> <引文> ...]

來源是章號（ch0012）或書資料夾內的相對路徑（outline/總綱.md）。
比對時忽略空白和換行。章節開頭的摘要和 POV 不算原文。
全部找到時回傳 0，有任何一句找不到時回傳 1。
"""
import pathlib
import re
import sys


def normalize(text):
    return re.sub(r"\s+", "", text)


def body(path):
    text = path.read_text(encoding="utf-8")
    return re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)


def source_path(book, source):
    if re.fullmatch(r"ch\d{4}", source):
        return book / "chapters" / f"{source}.md"
    return book / source


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    if len(args) < 3 or len(args) % 2 == 0:
        sys.exit(__doc__)
    book = pathlib.Path(args[0])
    missing = 0
    for source, quote in zip(args[1::2], args[2::2]):
        path = source_path(book, source)
        wanted = normalize(quote)
        if not wanted:
            print(f"空白 {source}")
            missing += 1
        elif not path.is_file():
            print(f"沒有這個檔 {source}：{quote}")
            missing += 1
        elif wanted in normalize(body(path)):
            print(f"OK {source}：{quote}")
        else:
            others = [
                p.stem
                for p in sorted((book / "chapters").glob("ch*.md"))
                if wanted in normalize(body(p))
            ]
            hint = f"（在 {'、'.join(others)}）" if others else ""
            print(f"找不到 {source}{hint}：{quote}")
            missing += 1
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
