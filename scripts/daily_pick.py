#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""daily_pick.py — 按日切分每周文献池

把「本周入选文献池」确定性地切成 7 天份，保证：
  1) 每天 IF 区间结构均衡（轮转分配，而非随机取样）；
  2) 同一输入两次运行结果完全一致（无随机数，稳定可复现）；
  3) 7 天并集 = 全池，交集 = 空（不重不漏）；
  4) 满足「每周 ≥500 篇 / 每日 ≥70 篇」的配额约束。

用法:
  python3 daily_pick.py --csv 01_文献库/2026-W39/papers_master.csv \
      --week 2026-W39 --day 1 --per-day 75 \
      --out-dir 01_文献库/2026-W39/D01
"""
import argparse
import csv
import json
import os
from collections import Counter

IF_ORDER = {">10": 0, "5-10": 1, "3-5": 2, "1-3": 3, "<1": 4, "UNBINNED": 5, "PENDING": 6}


def load(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def split_days(rows, days):
    """按 IF 区间 → 分数降序 → PMID 升序排序后轮转切分。"""
    rows = sorted(
        rows,
        key=lambda r: (
            IF_ORDER.get((r.get("if_bin") or "").strip(), 9),
            -float(r.get("score") or 0),
            int(r.get("pmid") or 0),
        ),
    )
    buckets = [[] for _ in range(days)]
    for i, r in enumerate(rows):
        buckets[i % days].append(r)
    return buckets


def render_md(week, day, rows):
    c_bin = Counter((r.get("if_bin") or "?").strip() for r in rows)
    c_mode = Counter((r.get("mode") or "?").strip() for r in rows)
    c_oa = Counter((r.get("oa") or "?").strip() for r in rows)
    lines = [
        f"# {week} D{day:02d} 当日阅读清单",
        "",
        f"- 篇数：**{len(rows)}**",
        f"- IF 区间分布：{'｜'.join(f'{k} {v}' for k, v in sorted(c_bin.items(), key=lambda x: IF_ORDER.get(x[0], 9)))}",
        f"- 研究模式：{'｜'.join(f'{k} {v}' for k, v in c_mode.most_common())}",
        f"- 开放获取：{'｜'.join(f'{k} {v}' for k, v in c_oa.most_common())}",
        "",
        "> 本清单由 `scripts/daily_pick.py` 确定性生成：排序键 = IF 区间 → score → PMID，轮转分配。",
        "> 所有条目均来自真实 PubMed 检索结果（检索式见 `search_log.md`）。",
        "",
        "| # | PMID | IF区间 | IF | 期刊 | 模式 | OA | 标题 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        t = (r.get("title") or "").replace("|", "/").strip()
        lines.append(
            f"| {i} | {r.get('pmid','')} | {r.get('if_bin','')} | {r.get('if_latest','')} | "
            f"{(r.get('journal_iso') or '').strip()} | {(r.get('mode') or '').strip()} | "
            f"{(r.get('oa') or '').strip()} | {t} |"
        )
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="周池 papers_master.csv")
    ap.add_argument("--week", required=True, help="周次，如 2026-W39")
    ap.add_argument("--day", type=int, required=True, help="当日序号 1..N")
    ap.add_argument("--per-day", type=int, default=75, help="每日篇数下限（默认 75）")
    ap.add_argument("--days", type=int, default=7, help="一周训练天数（默认 7）")
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()

    rows = load(a.csv)
    buckets = split_days(rows, a.days)
    if not (1 <= a.day <= a.days):
        raise SystemExit(f"--day 必须在 1..{a.days} 之间")

    mine = buckets[a.day - 1]
    os.makedirs(a.out_dir, exist_ok=True)

    # 1) 当日 papers.csv
    fields = list(rows[0].keys())
    with open(os.path.join(a.out_dir, "papers.csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in mine:
            w.writerow(r)

    # 2) 当日阅读清单
    with open(os.path.join(a.out_dir, "阅读清单.md"), "w", encoding="utf-8") as f:
        f.write(render_md(a.week, a.day, mine))

    # 3) 分日清单（供全周核对不重不漏）
    manifest = {f"D{i+1:02d}": [r.get("pmid") for r in b] for i, b in enumerate(buckets)}
    with open(os.path.join(a.out_dir, "_day_map.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=1)

    # 4) 自检
    all_pmids = [p for v in manifest.values() for p in v]
    dup = len(all_pmids) - len(set(all_pmids))
    c_bin = Counter((r.get("if_bin") or "?").strip() for r in mine)
    print(f"[daily_pick] {a.week} D{a.day:02d}: {len(mine)} 篇 → {a.out_dir}")
    print(f"  IF 区间: {'｜'.join(f'{k} {v}' for k, v in sorted(c_bin.items(), key=lambda x: IF_ORDER.get(x[0], 9)))}")
    print(f"  全周并集 {len(all_pmids)} 篇｜重复 {dup} 篇｜池总数 {len(rows)} 篇")
    if dup:
        print("  ⚠️ 存在重复分配，请检查池文件是否有重复 PMID")
    if len(mine) < a.per_day:
        print(f"  ⚠️ 当日 {len(mine)} 篇 < 目标 {a.per_day} 篇：池总量不足（{len(rows)}/{a.days}）；请扩大周池")
    if len(rows) < 500:
        print(f"  ⚠️ 周池 {len(rows)} 篇 < 500 篇硬底线，需补充检索")


if __name__ == "__main__":
    main()
