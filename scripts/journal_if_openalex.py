#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""journal_if_openalex.py — 用 OpenAlex 代理指标补齐 JIF 缺失（不改变入选集）

背景：bioxbio 只覆盖部分期刊，W39 实测 632 刊中仅约 292 刊可溯源，
导致文献池有 53% 落在 UNBINNED，IF 分层训练无法进行。

本脚本用 OpenAlex（开放 API，可溯源）的 `2yr_mean_citedness`
（2 年篇均被引数）作为**代理指标**补齐缺口。

⚠️ 严格口径（不可混用）：
  - bioxbio 行 = **官方 JIF**，`if_year_label` = 年份，`if_source_url` = bioxbio 页。
  - OpenAlex 行 = **代理指标**，`if_year_label` 强制带 `[代理]OpenAlex-2yrMCC` 前缀，
    `if_source_url` = OpenAlex API URL，`if_metric` = `OA_2yrMCC`。
  - 代理值**不得**在报告中被称作"影响因子"，只能称"2 年篇均被引数（代理分层）"。
  - 命中不了（无 ISSN / API 无条目）仍写 PENDING，绝不估算。

用法：
  python3 journal_if_openalex.py \
      --pool 01_文献库/2026-W39/papers_master.csv \
      --out  00_系统/journal_metrics_openalex.csv \
      --patch-pool            # 原地补齐：只填 if 列与 if_bin，不改变入选文献
"""
import argparse
import csv
import json
import os
import shutil
import sys
import time
import urllib.parse
import urllib.request

BIN = lambda v: (">10" if v >= 10 else "5-10" if v >= 5 else "3-5" if v >= 3
                 else "1-3" if v >= 1 else "<1")
UA = {"User-Agent": "SCI-writing-VIP/2.0 (mailto:research@example.org)"}
API = "https://api.openalex.org/sources"


def fetch(issns, mailto):
    flt = "issn:" + "|".join(issns)
    url = f"{API}?filter={urllib.parse.quote(flt, safe=':|')}&per-page=50&mailto={mailto}"
    req = urllib.request.Request(url, headers=UA)
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8")), url
        except Exception as e:
            if attempt == 2:
                print(f"  ! 请求失败：{e}")
                return {"results": []}, url
            time.sleep(2 * (attempt + 1))
    return {"results": []}, url


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True, help="需要补齐的文献池 csv")
    ap.add_argument("--out", required=True, help="代理指标表输出路径")
    ap.add_argument("--patch-pool", action="store_true",
                    help="原地补齐文献池的 if 列与 if_bin（不改变入选文献本身）")
    ap.add_argument("--mailto", default="research@example.org")
    ap.add_argument("--batch", type=int, default=50, help="每次请求 ISSN 数（上限 50）")
    a = ap.parse_args()

    with open(a.pool, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    fields = list(rows[0].keys())

    # 1) 找出需要补齐的期刊（按 ISSN 去重）
    need = {}
    for r in rows:
        if (r.get("if_latest") or "").strip():
            continue
        issn = (r.get("issn") or "").strip().split()[0] if (r.get("issn") or "").strip() else ""
        if not issn:
            continue
        need.setdefault(issn, set()).add(r.get("journal_iso", "").strip())

    print(f"[openalex] 待补齐期刊 {len(need)} 个（按 ISSN 去重）")
    issns = list(need.keys())
    hit = {}
    for i in range(0, len(issns), a.batch):
        chunk = issns[i:i + a.batch]
        data, url = fetch(chunk, a.mailto)
        for s in data.get("results", []):
            v = (s.get("summary_stats") or {}).get("2yr_mean_citedness")
            if v is None:
                continue
            for iss in ([s.get("issn_l")] + (s.get("issn") or [])):
                if iss and iss in need:
                    hit[iss] = {
                        "journal_name": s.get("display_name", ""),
                        "value": float(v),
                        "api_url": f"{API}/{s.get('id','').split('/')[-1]}",
                        "query_url": url,
                    }
        print(f"  批 {i // a.batch + 1}: 请求 {len(chunk)}，累计命中 {len(hit)}")
        time.sleep(0.4)

    # 2) 写代理指标表
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    today = time.strftime("%Y-%m-%d")
    with open(a.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["issn", "journal_iso", "openalex_name", "oa_2yr_mean_citedness",
                    "derived_if_bin", "metric_type", "source_url", "fetch_date"])
        for issn, h in sorted(hit.items()):
            for jname in sorted(need.get(issn, {""})):
                w.writerow([issn, jname, h["journal_name"], round(h["value"], 3),
                            BIN(h["value"]), "OA_2yrMCC", h["api_url"], today])

    # ⚠️ 2026-09-28 W40 修复：原写法 `(r.get("issn") or "").strip().split()[0]`
    # 在 issn 为空字符串时抛 IndexError（`"".strip().split()` → `[]`），
    # 使整个脚本在**写完代理指标表之后、原地补齐文献池之前**崩溃，
    # 表现为「表已生成、池未补齐」的半成品状态。改用与 L75/L132 一致的守卫写法。
    def _issn0(r):
        s = (r.get("issn") or "").strip()
        return s.split()[0] if s else ""

    covered = sum(1 for r in rows if not (r.get("if_latest") or "").strip()
                  and _issn0(r) in hit)
    print(f"[openalex] 命中期刊 {len(hit)}/{len(need)}；可补齐文献 {covered} 篇")
    print(f"  → {a.out}")

    # 3) 原地补齐文献池
    if a.patch_pool:
        bak = os.path.join(os.path.dirname(os.path.abspath(a.pool)), "_verify",
                           os.path.basename(a.pool).replace(".csv", "_pre_openalex.csv"))
        os.makedirs(os.path.dirname(bak), exist_ok=True)
        shutil.copy2(a.pool, bak)
        if "if_metric" not in fields:
            fields = fields + ["if_metric"]
        n_patch = 0
        for r in rows:
            r.setdefault("if_metric", "")
            if (r.get("if_latest") or "").strip():
                r["if_metric"] = "JIF_bioxbio"
                continue
            issn = (r.get("issn") or "").strip().split()[0] if (r.get("issn") or "").strip() else ""
            h = hit.get(issn)
            if not h:
                r["if_bin"] = "PENDING"
                r["if_metric"] = ""
                continue
            r["if_latest"] = f"{h['value']:.3f}"
            r["if_year_label"] = "[代理]OpenAlex-2yrMCC"
            r["if_source_url"] = h["api_url"]
            r["if_bin"] = BIN(h["value"])
            r["if_metric"] = "OA_2yrMCC"
            n_patch += 1
        with open(a.pool, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for r in rows:
                w.writerow({k: r.get(k, "") for k in fields})
        from collections import Counter
        c = Counter(r["if_bin"] for r in rows)
        m = Counter(r.get("if_metric", "") for r in rows)
        print(f"[openalex] 已原地补齐 {n_patch} 篇（原文件备份于 {bak}）")
        print(f"  新 IF 区间分布: {c.most_common()}")
        print(f"  指标来源构成: {m.most_common()}")


if __name__ == "__main__":
    main()
