#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
repair_ids.py —— 修复文献池中 doi / pmcid / oa 三列的错位问题

背景（2026-09-21 发现）
--------------------
harvest.py 早期版本用 `art.findall(".//ArticleIdList/ArticleId")` 抓 DOI/PMCID。
该 XPath 会递归进入 `ReferenceList/Reference/ArticleIdList`，命中**参考文献自己的**
DOI/PMCID，且循环赋值使「最后一个匹配胜出」。结果：doi / pmcid 列记的是别篇文献的
标识，由 pmcid 派生的 oa 标记随之失真。

影响面：doi、pmcid、oa 三列。**不影响** pmid / title / journal / abstract / IF / if_bin。

本脚本以 PMID 为准重新解析 `PubmedData/ArticleIdList`，就地修复三列，
并输出核对报告（含新旧值对照抽样）。

用法
----
python3 repair_ids.py --pool 01_文献库/2026-W39/papers_master.csv \
                      --report 01_文献库/2026-W39/_verify/id_repair_report.md
"""
import argparse
import csv
import json
import os
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"


def http_get(u, timeout=60, retries=3):
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(u, headers={"User-Agent": "SCI-writing-VIP/1.0"})
            return urllib.request.urlopen(req, timeout=timeout).read()
        except Exception as e:                                # noqa: BLE001
            last = e
            time.sleep(2 + 2 * i)
    raise last


def fetch_ids(pmids, batch=150, sleep=0.5):
    """按 PMID 取本篇自身的 DOI / PMCID（仅 PubmedData 层）。"""
    out = {}
    for i in range(0, len(pmids), batch):
        chunk = pmids[i:i + batch]
        u = f"{EUTILS}/efetch.fcgi?db=pubmed&retmode=xml&rettype=abstract&id={','.join(chunk)}"
        try:
            root = ET.fromstring(http_get(u))
        except Exception as e:                                # noqa: BLE001
            print(f"  [warn] batch {i//batch} failed: {e}", file=sys.stderr)
            continue
        for art in root.findall(".//PubmedArticle"):
            cit = art.find("MedlineCitation")
            if cit is None:
                continue
            pmid = (cit.findtext("PMID") or "").strip()
            doi = pmcid = ""
            for aid in art.findall("./PubmedData/ArticleIdList/ArticleId"):
                t = (aid.get("IdType") or "").lower()
                if t == "doi" and not doi:
                    doi = (aid.text or "").strip()
                elif t == "pmc" and not pmcid:
                    pmcid = (aid.text or "").strip()
            out[pmid] = {"doi": doi, "pmcid": pmcid}
        print(f"  [efetch] {min(i+batch, len(pmids))}/{len(pmids)}", file=sys.stderr)
        time.sleep(sleep)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True, help="papers_master.csv")
    ap.add_argument("--report", default="", help="核对报告输出路径（可选）")
    ap.add_argument("--sleep", type=float, default=0.5)
    a = ap.parse_args()

    with open(a.pool, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit("池为空")
    fields = list(rows[0].keys())

    pmids = [r["pmid"] for r in rows if r.get("pmid")]
    print(f"[repair] 待核 PMID {len(pmids)} 条", file=sys.stderr)
    real = fetch_ids(pmids, sleep=a.sleep)

    # 对照统计
    ex_doi = ex_pmc = 0
    old_oa = sum(1 for r in rows if r.get("oa") == "OA")
    changed = []
    for r in rows:
        rid = real.get(r["pmid"], {})
        d, p = rid.get("doi", ""), rid.get("pmcid", "")
        if d and d != r.get("doi", ""):
            ex_doi += 1
        if p != r.get("pmcid", ""):
            ex_pmc += 1
        if len(changed) < 12:
            changed.append((r["pmid"], r.get("doi", ""), d, r.get("pmcid", ""), p,
                            r.get("oa", ""), "OA" if p else "非OA"))
        r["doi"] = d
        r["pmcid"] = p
        r["oa"] = "OA" if p else "非OA"

    with open(a.pool, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})

    new_oa = sum(1 for r in rows if r["oa"] == "OA")
    msg = [
        "# DOI / PMCID / OA 修复核对报告",
        "",
        f"- 处理文件：`{os.path.abspath(a.pool)}`",
        f"- 处理时间：{time.strftime('%Y-%m-%d %H:%M')}",
        f"- 记录数：{len(rows)}",
        "",
        "## 修复口径",
        "",
        "仅取 `PubmedData/ArticleIdList/ArticleId`（本篇自身标识）。",
        "旧实现用 `.//ArticleIdList/ArticleId` 递归命中 `ReferenceList/*/ArticleIdList`，",
        "且循环覆盖使最后一条胜出，导致 ID 与外源文献错位。",
        "",
        "## 结果",
        "",
        "| 项 | 修复前 | 修复后 |",
        "|---|---|---|",
        f"| DOI 与真实值不一致 | — | 已纠正 {ex_doi} 条 |",
        f"| PMCID 与真实值不一致 | — | 已纠正 {ex_pmc} 条 |",
        f"| 标记为 OA 的篇数 | {old_oa} | {new_oa} |",
        f"| 真实可得 PMC 全文的篇数 | — | {new_oa} |",
        "",
        "## 新旧值对照（前 12 条）",
        "",
        "| PMID | 旧 DOI | 新 DOI | 旧 PMCID | 新 PMCID | 旧 OA | 新 OA |",
        "|---|---|---|---|---|---|---|",
    ]
    for pmid, od, nd, op, np_, oo, no in changed:
        msg.append(f"| {pmid} | {od[:38]} | {nd[:38]} | {op} | {np_} | {oo} | {no} |")
    msg += [
        "",
        "## 影响声明",
        "",
        "- **受影响列**：`doi`、`pmcid`、`oa`。",
        "- **未受影响**：`pmid`、`title`、`journal_iso`、`abstract`、`if_latest`、`if_bin`、",
        "  `mode`、`tags` —— 故基于这些列的报告统计（IF 分布、热点聚类、模式构成）不受影响。",
        "- **需回改的表述**：一切引用「OA 篇数」「[OA]/[非OA] 标记」的结论，须按修复后数值重述。",
        "",
    ]
    out = "\n".join(msg)
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        with open(a.report, "w", encoding="utf-8") as f:
            f.write(out)
        print(f"[repair] 报告 -> {a.report}", file=sys.stderr)
    print(f"[repair] DOI 纠正 {ex_doi}，PMCID 纠正 {ex_pmc}，OA {old_oa} -> {new_oa}")


if __name__ == "__main__":
    main()
