#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""archive_extract.py — 阶段1-1 文献基础归档（摘要级自动抽取 + 可核验）

对当日文献逐篇抽取四栏：科学问题 / 实验设计类型 / 核心结论 / 局限性。
抽取全部基于 PubMed 摘要原文的句子级规则匹配，**不做任何生成式改写**：
  - 命中的句子原样保留（英文原句），供逐条回溯；
  - 未命中即写「摘要未述」，**不推断、不补写**。

用法:
  python3 archive_extract.py --csv 01_文献库/2026-W39/D01/papers.csv \
      --out 01_文献库/2026-W39/D01/归档笔记.md --week 2026-W39 --day 1
"""
import argparse
import csv
import os
import re
from collections import Counter

# --- 句级角色线索（全部为真实学术写作高频线索词） -------------------------
CUES = {
    "question": [
        r"\bwe (?:aimed|aim|sought|set out) to\b", r"\bthis study (?:aims?|aimed|investigat)",
        r"\bthe (?:aim|purpose|objective) of (?:this|the) (?:study|work|analysis)",
        r"\bhere(?:,)? we\b", r"\bwe (?:investigated|examined|explored|assessed|evaluated)\b",
        r"\bhowever,\b", r"\bremains? (?:unclear|unknown|poorly|elusive|to be)",
        r"\bis (?:still )?(?:unclear|unknown|not fully understood)",
        r"\bhas not been (?:elucidated|explored|established|investigated)",
    ],
    "conclusion": [
        r"\b(?:we|our) (?:findings|results|data|study|analyses|work) (?:suggest|indicate|show|demonstrate|reveal|highlight|provide|support)",
        r"\bthese (?:findings|results|data|observations)\b",
        r"\btogether,? (?:these|our)\b", r"\bin conclusion\b",
        r"\bcollectively,\b", r"\boverall,\b",
        r"\bthis study (?:provides|offers|establishes|identifies)\b",
    ],
    "limitation": [
        r"\blimitation", r"\blimited by\b", r"\bshould be interpreted with caution\b",
        r"\bwarrant(?:s|ed)? (?:further|additional)\b", r"\bfurther (?:studies|research|work|experiments) (?:are|is) (?:needed|required|warranted)",
        r"\bremains to be (?:determined|validated|confirmed|elucidated)",
        r"\bcaution is (?:needed|warranted)\b", r"\bfuture studies\b", r"\bnot (?:been )?(?:yet )?validated\b",
        r"\black of\b", r"\bcannot (?:be )?(?:exclude|rule out)", r"\bmay not be generalizable\b",
    ],
}

# --- 实验设计类型判定（真实方法学名称） ------------------------------------
DESIGN = [
    ("单细胞测序", r"single-?cell (?:RNA|ATAC|multi-?omic|transcriptom)"),
    ("空间转录组", r"spatial (?:transcriptom|proteom|omics)"),
    ("孟德尔随机化", r"mendelian randomi[sz]ation"),
    ("机器学习/深度学习", r"(?:machine learning|deep learning|neural network|random forest|XGBoost|LASSO|nomogram|risk model|predictive model)"),
    ("多组学整合", r"(?:multi-?omics|integrative omics|proteogenomic|transcriptome-?metabolome)"),
    ("WGCNA/共表达网络", r"WGCNA|weighted gene co-?expression|co-?expression network"),
    ("差异表达+富集", r"(?:differentially expressed|DEGs?|GO enrichment|KEGG enrichment|gene set enrichment|GSEA)"),
    ("免疫浸润/微环境", r"(?:immune infiltration|tumor microenvironment|CIBERSORT|ESTIMATE|ssGSEA)"),
    ("网络药理学/分子对接", r"(?:network pharmacolog|molecular dock|molecular dynamics simulation)"),
    ("分子动力学", r"molecular dynamics"),
    ("GWAS/遗传关联", r"(?:GWAS|genome-?wide association|polygenic risk|SNP)"),
    ("临床试验/RCT", r"(?:randomi[sz]ed controlled trial|randomi[sz]ed clinical trial|\bRCT\b|phase (?:I|II|III) trial)"),
    ("队列/回顾性研究", r"(?:cohort study|retrospective (?:study|cohort)|prospective cohort|case-?control study)"),
    ("细胞实验", r"(?:in vitro|cell line|cell culture|transfect|knockdown|overexpress)"),
    ("动物实验", r"(?:in vivo|mice|mouse model|rat model|xenograft|zebrafish|organoid)"),
    ("类器官", r"organoid"),
    ("蛋白结构预测", r"(?:AlphaFold|structure prediction|protein-?protein interaction network)"),
    ("宏基因组/微生物组", r"(?:metagenom|microbiome|16S rRNA|shotgun sequencing)"),
    ("甲基化/表观组", r"(?:methylation|epigenom|ATAC-?seq|ChIP-?seq|acetylation)"),
    ("单细胞多组学", r"single-?cell multi-?omics"),
    ("系统评价/Meta", r"(?:systematic review|meta-?analysis)"),
    ("影像组学", r"radiomic"),
]


def split_sentences(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    return [p.strip() for p in parts if len(p.strip()) > 20]


def pick(sents, keys, maxn=2):
    out = []
    for s in sents:
        low = s.lower()
        if any(re.search(k, low) for k in keys):
            out.append(s)
            if len(out) >= maxn:
                break
    return out


def detect_design(text):
    low = (text or "").lower()
    hits = [name for name, pat in DESIGN if re.search(pat.lower(), low)]
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--week", required=True)
    ap.add_argument("--day", type=int, default=1)
    ap.add_argument("--full-abst", action="store_true", help="正文附完整摘要（默认只附命中句）")
    a = ap.parse_args()

    with open(a.csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    stat_design = Counter()
    n_lim = 0

    L = [
        f"# {a.week} D{a.day:02d} 文献基础归档笔记（阶段1-1）",
        "",
        f"- 当日文献：**{len(rows)} 篇**（清单见同目录 `阅读清单.md`）",
        "- 抽取方式：**摘要级句级规则抽取**。命中句原样保留英文原文；未命中写「摘要未述」，不做推断补写。",
        "- 证据边界：**全部为摘要级信息，未核验全文**。正文/图表级细节、真实局限性陈述须在 L2 深读时以全文为准。",
        "",
        "---",
        "",
    ]

    for i, r in enumerate(rows, 1):
        pmid = r.get("pmid", "")
        abst = r.get("abstract", "")
        sents = split_sentences(abst)
        q = pick(sents, CUES["question"], 2)
        c = pick(sents, CUES["conclusion"], 2)
        lim = pick(sents, CUES["limitation"], 2)
        design = detect_design(abst + " " + (r.get("pubtypes") or ""))
        for d in design:
            stat_design[d] += 1
        if lim:
            n_lim += 1

        L += [
            f"### {i}. PMID {pmid} — {(r.get('journal_iso') or '').strip()}（IF {r.get('if_latest','?')}｜{r.get('if_bin','')}｜{r.get('mode','')}｜{r.get('oa','')}）",
            f"**Title**: {r.get('title','').strip()}",
            "",
            f"- **科学问题**：{(' '.join(q)) if q else '（摘要未述 / 未命中线索）'}",
            f"- **设计类型**：{'、'.join(design) if design else '（摘要未命中已知方法学术语）'}",
            f"- **核心结论**：{(' '.join(c)) if c else '（摘要未述 / 未命中线索）'}",
            f"- **局限性（原文）**：{(' '.join(lim)) if lim else '**摘要未述**'}",
            "",
        ]
        if a.full_abst:
            L += [f"<details><summary>完整摘要</summary>", "", abst.strip(), "", "</details>", ""]

    L += [
        "---",
        "",
        "## 当日归档统计",
        "",
        f"- 明确写到局限性的篇数：**{n_lim}/{len(rows)}**（{n_lim/max(len(rows),1)*100:.0f}%）",
        "- 设计类型命中分布（一篇可多标）：",
        "",
        "| 设计类型 | 篇数 |",
        "|---|---|",
    ]
    for k, v in stat_design.most_common():
        L.append(f"| {k} | {v} |")
    L += [
        "",
        "> 统计口径提示：设计类型的命中基于摘要中出现的**方法学术语**，属下限估计；",
        "> 未写进摘要的方法（如实际做了 WB、IHC 但摘要未提）不会被计入。",
        "",
        f"_生成时间：{a.week} D{a.day:02d}｜脚本：archive_extract.py_",
    ]

    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    print(f"[archive_extract] {len(rows)} 篇 → {a.out}")
    print(f"  写明局限性：{n_lim} 篇（{n_lim/max(len(rows),1)*100:.0f}%）")
    print(f"  设计类型命中 Top10：{stat_design.most_common(10)}")


if __name__ == "__main__":
    main()
