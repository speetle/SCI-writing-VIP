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
        # --- D03 扩充（原表未覆盖的高频真实表述，均可在 abstracts 中回溯）---
        r"\b(?:this|the present|our) (?:study|work|research|analysis|paper|investigation|review|report)\s"
        r"(?:explored|investigated|examined|assessed|evaluated|aimed|sought|was designed|was conducted|"
        r"reports?|presents?|describes?|provides?|proposes?|develops?|introduces?|focuses|analyzed|analysed|"
        r"characterized|characterised|compared|integrated|quantified|maps?|aims?)\b",
        r"\bwe (?:developed|constructed|built|proposed|designed|integrated|analyzed|analysed|performed|"
        r"conducted|used|applied|collected|identified|generated|compared|screened|combined|established|"
        r"derived|compiled|mapped|quantified|tested|profiled|characterized|characterised|report|present|"
        r"describe|propose|introduce|hypothesized|hypothesised|addressed|leveraged|evaluated|assessed)\b",
        r"\b(?:to|in order to) (?:investigate|explore|examine|assess|evaluate|determine|identify|clarify|"
        r"elucidate|characterize|characterise|define|develop|construct|test|quantify)\b",
        r"\b(?:objective|aim|purpose|goal)s? (?:of|was|were|is|are)\b",
        r"\b(?:purpose|objective|aim)s?:\s",
        r"\bwe (?:therefore|here|thus)?\s*(?:aim|sought)\b",
        r"\bto (?:this end|address this|fill this gap|better understand)\b",
    ],
    "conclusion": [
        r"\b(?:we|our) (?:findings|results|data|study|analyses|work) (?:suggest|indicate|show|demonstrate|reveal|highlight|provide|support)",
        r"\bthese (?:findings|results|data|observations)\b",
        r"\btogether,? (?:these|our)\b", r"\bin conclusion\b",
        r"\bcollectively,\b", r"\boverall,\b",
        r"\bthis study (?:provides|offers|establishes|identifies)\b",
        # --- D03 扩充 ---
        r"\bwe (?:found|observed|identified|detected|demonstrated|showed|revealed|confirmed|noted|concluded|"
        r"report that|show that|estimate)\b",
        r"\b(?:conclusion|conclusions|results|findings|key findings|key points):",
        r"\bthese (?:results|data|analyses|observations|studies)\b",
        r"\b(?:the|our) (?:model|nomogram|signature|score|classifier|framework|index) "
        r"(?:achieved|reached|yielded|demonstrated|showed|attained|predicted)\b",
        r"\bthe (?:combined|proposed|final) model\b",
        r"\bwas (?:significantly )?(?:associated with|correlated with|enriched in|upregulated|downregulated)\b",
        r"\bwere (?:significantly )?(?:associated with|correlated with|enriched in|upregulated|downregulated|"
        r"identified|observed|detected)\b",
        r"\bfurthermore,?\s+(?:we|these)\b",
    ],
    # ⚠️ D05（2026-09-25）拆表：原 limitation 表混装了两类互不相干的线索——
    #   ①「真·局限指针」(`limitation` / `limited by` / `caution` / `lack of` / `cannot rule out`)
    #   ②「展望/设限指针」(`future studies` / `warrant(s) further` / `further studies are needed`)
    #   后者是 **outlook**，不是 limitation。混装使「写明局限性」的篇数被系统性高估
    #   （D05 实测：10 篇「明写局限」中，2 篇实为展望句）。→ 已拆入 CUES["outlook"]。
    "limitation": [
        r"\blimitation", r"\blimited by\b", r"\bshould be interpreted with caution\b",
        r"\bremains to be (?:determined|validated|confirmed|elucidated)",
        r"\bcaution is (?:needed|warranted)\b", r"\bnot (?:been )?(?:yet )?validated\b",
        r"\black of\b", r"\bcannot (?:be )?(?:exclude|rule out)", r"\bmay not be generalizable\b",
    ],
    "outlook": [
        r"\bwarrant(?:s|ed)? (?:further|additional)\b",
        r"\bfurther (?:studies|research|work|experiments) (?:are|is) (?:needed|required|warranted)",
        r"\bfuture (?:studies|research|work|investigations|efforts)\b",
    ],
}

# --- 局限句「指代对象」判定（D05 新增，配合 A-42 / D-16 的发现） ----------------
# 背景：`limitation` / `limited by` 在真实摘要中至少四类指代——
#   ① 本研究缺陷（自陈）② 现行药物/疗法的局限 ③ 现行方法/数据源的局限 ④ 领域知识缺口。
#   仅 ① 属「作者自陈局限」，其余三类混入会使统计失真。
#   ⚠️ 本判定**只做标签，不删句、不改写**（红线：不推断）。判不出自陈的，一律标「需人工判定」。
LIMIT_SELF = re.compile(
    r"(?:\b(?:our|this|the present|the current)\s+(?:study|work|analysis|review|report|cohort|model|"
    r"investigation|framework)\b[^.]{0,160}\blimit"
    r"|\blimit\w*\b[^.]{0,160}\b(?:our|this|the present|the current)\s+(?:study|work|analysis|review|"
    r"report|cohort|model|investigation|framework)\b"
    r"|\bwe\s+(?:acknowledge|cannot|did not|were unable|have not)\b"
    r"|\b(?:exploratory|hypothesis-generating|preliminary)\b"
    r"|\bshould be interpreted with caution\b)", re.I)


def split_limitation(sents):
    """返回 (自陈局限句, 非自陈局限句)。非自陈 = 指代工具/药物/领域，须人工判定。"""
    self_hits, other_hits = [], []
    for s in sents:
        (self_hits if LIMIT_SELF.search(s) else other_hits).append(s)
    return self_hits[:2], other_hits[:2]

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


# --- 位置兜底（线索未命中时使用，仍为「原文逐字引用」，不做任何推断） ---------
# 背景：D03 实测线索覆盖率仅约 44%——摘要中确实存在研究目的句与结论句，
# 但其表述（`This study explored ...` / `We developed ...` / `We found ...`）
# 不在原线索表内。修复分两步：① 扩充线索词；② 仍不命中时启用**位置兜底**，
# 并在归档中显式标注「位置兜底」，保证可审计（不推断、不补写、不改写）。
def positional_fallback(sents, role):
    """按位置取兜底句：question → 首个含第一人称/研究主语的句子；conclusion → 末句。"""
    if not sents:
        return []
    if role == "question":
        for s in sents:
            if re.search(r"\b(?:we|this study|this work|the present study|the aim|the objective)\b",
                         s, re.IGNORECASE):
                return [s]
        return [sents[0]]
    # conclusion
    return sents[-2:] if len(sents) >= 2 else [sents[-1]]


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
    n_lim_other = n_lim_none = n_outl = 0
    n_q = n_c = n_q_fb = n_c_fb = 0

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
        lim_raw = pick(sents, CUES["limitation"], 4)
        lim, lim_other = split_limitation(lim_raw)
        outl = pick(sents, CUES["outlook"], 1)
        # 位置兜底：线索未命中时启用（标注来源，绝不推断）
        q_src = "" if q else "（线索未命中→位置兜底句）"
        c_src = "" if c else "（线索未命中→位置兜底句）"
        if not q:
            q = positional_fallback(sents, "question")
        if not c:
            c = positional_fallback(sents, "conclusion")
        design = detect_design(abst + " " + (r.get("pubtypes") or ""))
        for d in design:
            stat_design[d] += 1
        if lim:
            n_lim += 1
        elif lim_other:
            n_lim_other += 1
        else:
            n_lim_none += 1
        if outl:
            n_outl += 1
        if q:
            n_q += 1
            if q_src:
                n_q_fb += 1
        if c:
            n_c += 1
            if c_src:
                n_c_fb += 1

        L += [
            f"### {i}. PMID {pmid} — {(r.get('journal_iso') or '').strip()}（IF {r.get('if_latest','?')}｜{r.get('if_bin','')}｜{r.get('mode','')}｜{r.get('oa','')}）",
            f"**Title**: {r.get('title','').strip()}",
            "",
            f"- **科学问题**：{(' '.join(q)) if q else '（摘要未述 / 未命中线索）'}{q_src}",
            f"- **设计类型**：{'、'.join(design) if design else '（摘要未命中已知方法学术语）'}",
            f"- **核心结论**：{(' '.join(c)) if c else '（摘要未述 / 未命中线索）'}{c_src}",
            f"- **局限性（原文·自陈）**：{(' '.join(lim)) if lim else '**摘要未述**'}"
            + (f"\n- **局限性（原文·非自陈，指代现行药物/疗法/方法或领域缺口；须人工判定，勿计作作者自陈）**：{' '.join(lim_other)}" if lim_other and not lim else "")
            + (f"\n- **展望/设限（原文）**：{' '.join(outl)}" if outl else ""),
            "",
        ]
        if a.full_abst:
            L += [f"<details><summary>完整摘要</summary>", "", abst.strip(), "", "</details>", ""]

    L += [
        "---",
        "",
        "## 当日归档统计",
        "",
        f"- 作者**自陈局限**的篇数：**{n_lim}/{len(rows)}**（{n_lim/max(len(rows),1)*100:.0f}%）",
        f"- `limitation` 类词命中但**指代对象非本研究**（现行药物/疗法/方法或领域缺口）的篇数：**{n_lim_other}**（须人工判定，**不计入自陈局限**）",
        f"- 局限栏为「摘要未述」的篇数：**{n_lim_none}**",
        f"- 展望/设限句命中篇数（原属 limitation 表，D05 已拆分独立）：**{n_outl}**",
        f"- 科学问题栏有内容：**{n_q}/{len(rows)}**（其中位置兜底 {n_q_fb} 篇，已在栏内标注）",
        f"- 核心结论栏有内容：**{n_c}/{len(rows)}**（其中位置兜底 {n_c_fb} 篇，已在栏内标注）",
        "- ⚠️ 位置兜底说明：线索未命中时按位置取句（question→首个含研究主语的句子；"
        "conclusion→末 1–2 句），**仍为原文逐字引用**，已在栏内标「线索未命中→位置兜底句」，可逐条回溯核验。",
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
    print(f"  作者自陈局限：{n_lim} 篇（{n_lim/max(len(rows),1)*100:.0f}%）")
    print(f"  局限类词但非自陈（指代工具/药物/领域，须人工判定）：{n_lim_other} 篇")
    print(f"  局限栏摘要未述：{n_lim_none} 篇")
    print(f"  展望/设限句命中：{n_outl} 篇")
    print(f"  设计类型命中 Top10：{stat_design.most_common(10)}")


if __name__ == "__main__":
    main()
