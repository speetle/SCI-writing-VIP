#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_tables.py —— Markdown 表格“断表残片”检测（`-210` 固化工具）

为什么需要它
------------
累积型表格（架构累积、四库清单、账本记录表）是“边写边追加”的：每天往上加行。
一旦把新增行写在 `> 入库说明` 之后、或落到下一个 `## 章节` 之后，这一行在
Markdown 里就**不再是表格**——它前面没有表头行与 `|---|` 分隔行。

结果是本项目最隐蔽的一类错误（`-81` 家族·渲染变体）：
    grep 反查：编号连续、PMID 齐全、条数正确 —— 全绿
    人打开看：38 行里只有 7 行是表格，31 行是纯文本
即“账本比产物好看”，且所有内容层自检都通不过察觉。

判据（唯一正确的那个）
----------------------
一个合法的 Markdown 表格块，**首行的下一行必须是分隔行** `|---|...|`。
按内容判（“编号是否续接”“日期是否连续”）会漏检——首列是日期、版本号、
条目名时全漏。这是 W44 D05 的实测教训：按编号判只查出 1 处，按表头判查出 13 处。

用法
----
    python3 check_tables.py                      # 扫默认扫描域
    python3 check_tables.py a.md b.md dir/       # 扫指定文件/目录（目录取 *.md）
    python3 check_tables.py --root /path/to/proj # 指定项目根
    python3 check_tables.py --json               # 机器可读

退出码
------
    0 = 全部通过（0 残片）
    1 = 发现残片（必须修，不得交付）
    2 = 扫描域为空（口径错误，先查路径，不要当成通过）

扫描域默认值（与 `00_系统/每日自检清单.md` `§B0-W44D05` 第 7 项一致）
------------------------------------------------------------------
    04_IMRAD架构库/*.md
    03_语言范式库/*.md
    06_进化复盘/EVOLUTION_LEDGER.md
"""

import argparse
import glob
import json
import os
import re
import sys

DEFAULT_GLOBS = [
    "04_IMRAD架构库/*.md",
    "03_语言范式库/*.md",
    "06_进化复盘/EVOLUTION_LEDGER.md",
]

# 分隔行：| --- | :---: | ---: | ... 只允许 | - : 空格
SEP_RE = re.compile(r"^\|[\s:\-\|]+\|$")


def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")


def table_blocks(lines):
    """返回连续的以 | 开头的行块，每个块为行索引列表。"""
    blocks, cur = [], []
    for i, line in enumerate(lines):
        if line.startswith("|"):
            cur.append(i)
        else:
            if cur:
                blocks.append(cur)
                cur = []
    if cur:
        blocks.append(cur)
    return blocks


def is_header_block(lines, block):
    """块首行的下一行是否为分隔行。是 → 该块是合法表格；否 → 断表残片。"""
    first = block[0]
    if first + 1 >= len(lines):
        return False
    return bool(SEP_RE.match(lines[first + 1] or ""))


SEQ_HEADER_RE = re.compile(r"^\|\s*(#|序号|编号|No\.?)\s*\|", re.I)


def numbered_rows(lines, block):
    """块内形如 | 12 | ... 的行号序号。

    只在**表头首格是 #／序号／编号／No.** 的块里取——否则会把 PMID（8 位）
    或年份当成序号（W44 D05 实测：按"任意数字首格"取会把 42860426 这类 PMID
    读成缺号，4 件文件全假阳性）。序号另限 ≤999。
    """
    if not block:
        return []
    if not SEQ_HEADER_RE.match(lines[block[0]]):
        return []
    nums = []
    for i in block[1:]:
        m = re.match(r"^\|\s*(\d{1,3})\s*\|", lines[i])
        if m:
            nums.append(int(m.group(1)))
    return nums


def check_file(path):
    lines = read_lines(path)
    blocks = table_blocks(lines)
    frags = []
    for b in blocks:
        if is_header_block(lines, b):
            continue
        prev_end = None
        for p in blocks:
            if p is b:
                break
            prev_end = p[-1]
        gap = []
        if prev_end is not None:
            gap = [x for x in lines[prev_end + 1: b[0]] if x.strip() != ""]
        frags.append({
            "line": b[0] + 1,                 # 1-based
            "rows": len(b),
            "first_cell": (lines[b[0]].split("|")[1].strip() if "|" in lines[b[0]] else "")[:40],
            "gap_kind": "仅空行" if (prev_end is not None and not gap) else (
                "文首" if prev_end is None else "夹有非表格行：" + gap[0][:40]),
        })
    return {
        "path": path,
        "blocks": len(blocks),
        "fragments": frags,
    }


def extra_checks(path, lines):
    """附加断言：编号序列 1..N 无缺号；说明块（> 开头）不得夹在表格块之间。"""
    blocks = table_blocks(lines)
    notes_in_gap = 0
    for k in range(len(blocks) - 1):
        gap = [x for x in lines[blocks[k][-1] + 1: blocks[k + 1][0]] if x.strip() != ""]
        if gap and any(x.startswith(">") for x in gap) and blocks[k + 1][0] == blocks[k][-1] + 1:
            notes_in_gap += 0  # 紧邻则无空行，不构成断裂
    all_nums = []
    for b in blocks:
        all_nums.extend(numbered_rows(lines, b))
    # 缺号只在“观测区间内”判：各周表可能从 13、31 等起始编号，不能按 1..max 判，
    # 否则会把“周内局部编号”误报成缺号（W44 D05 实测假阳性 4 件）。
    missing = []
    if all_nums:
        lo, hi = min(all_nums), max(all_nums)
        have = set(all_nums)
        missing = [n for n in range(lo, hi + 1) if n not in have]
    return {"numbered": len(all_nums), "missing": missing}


def resolve_targets(root, args):
    targets = []
    if args.paths:
        for p in args.paths:
            full = p if os.path.isabs(p) else os.path.join(root, p)
            if os.path.isdir(full):
                targets.extend(sorted(glob.glob(os.path.join(full, "*.md"))))
            elif os.path.isfile(full):
                targets.append(full)
            else:
                targets.extend(sorted(glob.glob(full)))
    else:
        for g in DEFAULT_GLOBS:
            targets.extend(sorted(glob.glob(os.path.join(root, g))))
    # 去重保序
    seen, out = set(), []
    for t in targets:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser(description="检测 Markdown 累积型表格的断表残片（-210）")
    ap.add_argument("paths", nargs="*", help="文件、目录或 glob；省略则扫默认扫描域")
    ap.add_argument("--root", default=os.getcwd(), help="项目根目录（默认当前目录）")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args()

    targets = resolve_targets(args.root, args)
    if not targets:
        print("[FATAL] 扫描域为空——先查路径，不要当成通过（口径错误）", file=sys.stderr)
        return 2

    results, total_frag = [], 0
    for p in targets:
        r = check_file(p)
        r.update(extra_checks(p, read_lines(p)))
        total_frag += len(r["fragments"])
        results.append(r)

    if args.json:
        print(json.dumps({"files": len(targets), "fragments": total_frag,
                          "detail": results}, ensure_ascii=False, indent=2))
    else:
        print(f"# 断表检测（判据：表格块首行的下一行必须是 |---| 分隔行）")
        print(f"# 扫描域文件数 = {len(targets)}")
        for r in results:
            if r["fragments"]:
                print(f"\n{r['path']}：表块 {r['blocks']}，残片 {len(r['fragments'])} 处")
                for f in r["fragments"]:
                    print(f"    行 {f['line']:>5}  行数 {f['rows']:>2}  首格 {f['first_cell']:<24}  {f['gap_kind']}")
            if r["missing"]:
                print(f"    [编号缺号] {r['path']}：缺 {r['missing'][:12]}")
        gaps = sum(len(r["missing"]) for r in results)
        print(f"\n残片合计 = {total_frag} / 区间内缺号 = {gaps}")
        if total_frag == 0 and gaps == 0:
            print("✅ 通过：0 残片，且编号在观测区间内无缺号")
        elif total_frag == 0:
            print("⚠️ 残片 0，但有编号缺号——查是否漏行（缺号即漏行，须补回或登记原因）")
        else:
            print("❌ 未通过：先删块间空行把行并回表尾、或把说明块移到表后，再复跑。不得交付。")

    return 0 if (total_frag == 0 and gaps == 0) else 1



if __name__ == "__main__":
    sys.exit(main())
