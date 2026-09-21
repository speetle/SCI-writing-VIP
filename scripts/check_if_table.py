#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
check_if_table.py — journal_metrics.csv 归属一致性校验（红线自检）

背景（2026-09-21 W39 复核发现，见 ERROR_DO_NOT_REPEAT [ERR-2026W39-05]）：
旧版 journal_if.py 在 slug 抓取失败后会回退到站内搜索，而该站搜索页由前端 JS 渲染，
服务端返回的是一份**静态热门期刊列表**（首条恒为 PLOS-ONE）。于是 341/632 行
被写入 PLOS ONE 的 IF（2.8）与 URL，`status` 仍记 `OK`，污染了 290/520 篇入选文献的
IF 分层，而 `if_source_url` 反而成了「错误已被追溯」的假证据。

因此引入本校验：**IF 表的每一行，其 if_source_url 的 slug 必须等于
journal_iso 的规范 slug**。URL 与期刊名不一致 ⇒ 该值不可溯源 ⇒ 视为污染。

用法
  python3 check_if_table.py --table 00_系统/journal_metrics.csv
  python3 check_if_table.py --table m.csv --strict      # 发现违规即退出码 1
"""
import argparse
import csv
import re
import sys
from collections import Counter

PLOS_FALLBACK = "PLOS-ONE"      # 历史缺陷特征值


def slugify(s):
    return re.sub(r"-+", "-", re.sub(r"[^0-9A-Za-z]+", "-", (s or "").strip())).strip("-").upper()


def check(path):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    bad, plos, ok = [], [], 0
    for r in rows:
        iso = (r.get("journal_iso") or "").strip()
        url = (r.get("if_source_url") or "").strip()
        val = (r.get("if_latest") or "").strip()
        if not url:                                  # PENDING 行：允许无 URL
            continue
        seg = url.rstrip("/").split("/")[-1].upper()
        if seg.endswith(PLOS_FALLBACK) and slugify(iso) != PLOS_FALLBACK:
            plos.append((iso, val, url))
        elif seg != slugify(iso):
            bad.append((iso, val, url, slugify(iso)))
        else:
            ok += 1
    pend = sum(1 for r in rows if (r.get("status") or "").strip().upper() == "PENDING")
    return rows, ok, bad, plos, pend


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--table", required=True)
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--show", type=int, default=10)
    a = ap.parse_args()

    rows, ok, bad, plos, pend = check(a.table)
    print(f"表：{a.table}")
    print(f"总行数 {len(rows)}｜URL 与期刊一致 {ok}｜PENDING {pend}｜"
          f"疑似 PLOS 兜底污染 {len(plos)}｜其他 slug 不符 {len(bad)}")
    if plos:
        print(f"\n[红线] PLOS 兜底污染（示例 {min(a.show, len(plos))} 条）：")
        for iso, v, u in plos[:a.show]:
            print(f"   {iso:<32} 记录IF={v:<6} url={u}")
    if bad:
        print(f"\n[警告] slug 不符（示例 {min(a.show, len(bad))} 条）：")
        for iso, v, u, exp in bad[:a.show]:
            print(f"   {iso:<32} 记录IF={v:<6} 期望slug={exp:<28} 实际={u.rsplit('/',1)[-1]}")
    if not plos and not bad:
        print("\n✅ 通过：所有带 URL 的行，其来源 slug 与期刊名一致。")
    return 1 if (a.strict and (plos or bad)) else 0


if __name__ == "__main__":
    sys.exit(main())
