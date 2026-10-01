#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
extract_prose.py — 从 Markdown 训练稿/交付稿中抽取**正文散文**，供计数类脚本（count_markers /
count_connectors / extract_language）使用。

为什么需要它（对应 [ERR-2026W40-04]「机检脚本被非正文污染」家族的固定动作）：
`anti_ai_check.py` 已内建「截断 `<!-- APPENDIX -->` + 剔除稿首引用块」的正文范围规则，
但 `count_markers.py` / `count_connectors.py` **只**提供 `--strip-appendix`，不剔标题行、引用块、
表格、列表项、斜体元信息行。直接把这些脚本指向 `.md` 会把「起草前声明」「素材信息清单」
「附录自述」等非正文内容计入分母（实测虚高可达 1.9 倍）。

本脚本把「非正文内容清单」固化为**唯一实现**，五个类别逐项对照：
  ① 稿首标题行（`#` 开头）
  ② 引用块（`>` 开头）
  ③ `<!-- APPENDIX -->` 及其后全部内容
  ④ 表格行（`|` 开头）与表格分隔行
  ⑤ 列表项（`-` / `*` / `+` / `1.` 开头）与斜体元信息行（`_..._` / `*...*` 整行）

输出：每行一句的纯文本（UTF-8），可直接喂给上述三个脚本。

用法：
  python3 extract_prose.py --md <稿件.md> --out <正文.txt>
  python3 extract_prose.py --md <稿件.md>            # 打印到 stdout
"""
import argparse
import re
import sys

APPENDIX_RE = re.compile(r"<!--\s*APPENDIX\s*-->")
LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
ITALIC_RE = re.compile(r"^\s*[_*]{1,2}[^_*].*[_*]{1,2}\s*$")


def extract(md_text: str) -> str:
    """返回正文散文（句子级，每行一句）。"""
    body = APPENDIX_RE.split(md_text, maxsplit=1)[0]
    kept = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):          # ① 标题行
            continue
        if line.startswith(">"):          # ② 引用块（稿首警示块等）
            continue
        if line.startswith("|"):          # ④ 表格行
            continue
        if re.match(r"^[-:\s|]+$", line):  # ④ 表格分隔行
            continue
        if LIST_RE.match(line):           # ⑤ 列表项
            continue
        if ITALIC_RE.match(line):         # ⑤ 斜体元信息行
            continue
        if line.startswith("```"):        # 代码围栏
            continue
        kept.append(line)
    text = " ".join(kept)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return ""
    # 统一分句（与 count_connectors.split_sentences 的粗口径一致，供快速核验）
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(\[])", text)
    return "\n".join(p.strip() for p in parts if p.strip())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True, help="输入 Markdown 稿件")
    ap.add_argument("--out", help="输出正文 txt（缺省打印到 stdout）")
    a = ap.parse_args()

    with open(a.md, encoding="utf-8") as f:
        md_text = f.read()
    prose = extract(md_text)

    if a.out:
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(prose + ("\n" if prose else ""))
        n_sent = len([x for x in prose.splitlines() if x.strip()])
        n_word = len(prose.split())
        sys.stderr.write(
            f"[extract_prose] {a.md} → {a.out}\n"
            f"  正文句数 {n_sent}｜词数（空白切分）{n_word}\n"
            f"  口径：截断 <!-- APPENDIX -->；剔标题行/引用块/表格/列表/斜体元信息行\n"
        )
    else:
        print(prose)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
