#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
select_for_reading.py — 按阅读深度分层抽样，生成 L1/L2 阅读清单

为什么需要它：500+ 篇不可能逐字读，必须**按规则**而不是按手感选精读对象，
否则会系统性地偏向自己熟悉的主题（确认偏误），也会让「热点」判断失真。

用法
  # L1 速读清单（60–120 篇）：按 IF 区间分层配额 + 纯生信优先
  python3 select_for_reading.py --csv papers_master.csv --level L1 --n 80

  # L2 深读清单（10–20 篇）：仅取 [OA] + 高 IF + 纯生信，供技法解构
  python3 select_for_reading.py --csv papers_master.csv --level L2 --n 15

  # 极简模式：只输出 PMID 列表（便于喂给 pubmed-search / 精读技能）
  python3 select_for_reading.py --csv papers_master.csv --level L2 --n 15 --pmids-only
"""
import argparse
import csv
import json
import os
import sys
from collections import Counter, OrderedDict

BIN_ORDER = [">10", "5-10", "3-5", "1-3", "<1", "UNBINNED"]


def load(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def bin_quota(n, level):
    """IF 区间配额：高分区权重更高，但不独占（避免只读顶刊而错过领域主流）。"""
    if level == "L2":
        w = {">10": 5, "5-10": 4, "3-5": 1, "1-3": 0, "<1": 0, "UNBINNED": 0}
    else:  # L1
        w = {">10": 3, "5-10": 4, "3-5": 3, "1-3": 2, "<1": 1, "UNBINNED": 2}
    tot = sum(w.values())
    q = OrderedDict()
    left = n
    keys = list(w)
    for i, k in enumerate(keys):
        if i == len(keys) - 1:
            q[k] = left
        else:
            q[k] = int(round(n * w[k] / tot))
            left -= q[k]
    return q


def pick(rows, level, n):
    """同区间内：纯生信 → 含算法信号 → score 降序。"""
    q = bin_quota(n, level)
    out = []
    for b in BIN_ORDER:
        pool = [r for r in rows if r.get("if_bin") == b]
        if level == "L2":
            pool = [r for r in pool if r.get("oa") == "OA"]
        pool.sort(key=lambda r: (r.get("mode") != "纯生信", r.get("has_algo") != "Y",
                                 -float(r.get("score") or 0)))
        out += pool[:q.get(b, 0)]
    # 配额未填满时用全局高分补齐（仍保持分层均衡）
    if len(out) < n:
        have = {r["pmid"] for r in out}
        rest = sorted([r for r in rows if r["pmid"] not in have],
                      key=lambda r: -float(r.get("score") or 0))
        out += rest[: n - len(out)]
    return out[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--level", choices=["L1", "L2"], default="L1")
    ap.add_argument("--n", type=int, default=80)
    ap.add_argument("--pmids-only", action="store_true")
    ap.add_argument("--full-abstract", action="store_true", help="打印完整摘要（默认截断 900 字）")
    ap.add_argument("--out", default="")
    a = ap.parse_args()

    rows = load(a.csv)
    sel = pick(rows, a.level, a.n)

    if a.pmids_only:
        print("\n".join(r["pmid"] for r in sel))
        return

    lines = []
    lines.append(f"# {a.level} 阅读清单（{len(sel)} 篇，源 {os.path.basename(a.csv)}，"
                 f"全库 {len(rows)} 篇）\n")
    dist = Counter(r["if_bin"] for r in sel)
    lines.append("配额兑现：" + " | ".join(f"{b}={dist.get(b,0)}" for b in BIN_ORDER) + "\n")
    lines.append(f"模式构成：{dict(Counter(r['mode'] for r in sel))}\n")
    for i, r in enumerate(sel, 1):
        ab = r["abstract"] if a.full_abstract else (r["abstract"][:900] + " …")
        lines.append(f"\n---\n### {i}. [PMID:{r['pmid']}] [{r['oa']}] IF={r.get('if_latest') or '?'} "
                     f"({r.get('if_bin')}) | {r['mode']}\n"
                     f"**{r['title']}**\n\n*{r['journal_full'] or r['journal_iso']}* · {r.get('pubdate','')}\n\n"
                     f"标签：{r['tags']}｜疾病：{r['cancers'] or '—'}｜匹配块：{r['matched_blocks']}\n\n"
                     f"{ab}\n")
    text = "\n".join(lines)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(text)
        print(f"[select_for_reading] 已写入 {a.out}（{len(sel)} 篇）")
    else:
        print(text)


if __name__ == "__main__":
    sys.exit(main())
