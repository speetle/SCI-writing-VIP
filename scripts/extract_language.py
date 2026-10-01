#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""extract_language.py — 阶段1-2 语言范式原料提取（样本A：真人原文）

从当日文献摘要中，按**修辞功能角色**把真人句子分类导出，并统计文体指标。
输出的是**原料**（真实句子 + PMID），不是结论——「地道句式清单」须由
模型在原料基础上筛选、归纳后写入 03_语言范式库/，并保留原文引句与 PMID。

角色分类（对应 IMRaD 各段的实际功能）:
  background   背景铺陈      gap          研究缺口
  objective    目的陈述      methods      方法描述
  result       结果陈述      interpretation 结果解读
  limitation   局限陈述      outlook      未来展望
  contrast     文献对比/转折

用法:
  python3 extract_language.py --csv 01_文献库/2026-W39/D01/papers.csv \
      --out 01_文献库/2026-W39/D01/语言范式原料.md \
      --dump-abstracts 01_文献库/2026-W39/D01/_human_corpus.txt
"""
import argparse
import csv
import json
import os
import re
from collections import Counter

ROLE_CUES = {
    "background": [
        r"\bis (?:a )?(?:leading|major|common|significant) cause",
        r"\bremains a (?:major|leading|significant)",
        r"\bhas (?:become|emerged as)\b",
        r"\bin recent years\b",
        r"\baccounts? for\b",
        r"\bis characterized by\b",
        r"\bposes? a (?:major|serious|significant)\b",
        r"\bthe (?:molecular )?mechanisms? underlying\b",
    ],
    "gap": [
        r"\bhowever,\b", r"\bnevertheless,\b", r"\byet,?\b.{0,40}\bunknown\b",
        r"\bremains? (?:unclear|unknown|elusive|poorly understood|controversial|to be)",
        r"\bis (?:still )?(?:unclear|unknown|not fully|poorly)",
        r"\bhas not (?:yet )?been (?:elucidated|clarified|explored|established|investigated|reported)",
        r"\bno (?:effective|reliable|robust) (?:biomarker|predictor|model|therapy)",
        r"\black(?:s|ing)? (?:of )?(?:effective|reliable|robust|comprehensive)",
        r"\bconflicting (?:results|evidence|findings)",
    ],
    "objective": [
        r"\bwe (?:aimed|aim|sought|set out|sought to)\b",
        r"\bthe (?:aim|purpose|objective|goal) of (?:this|the) (?:study|work|analysis|research)",
        r"\bhere(?:,)? (?:we|this study)\b",
        r"\bwe (?:investigated|examined|explored|assessed|evaluated|developed|constructed|integrated)\b",
        r"\bthis study (?:aims?|was designed|was conducted)\b",
        r"\bto (?:identify|explore|investigate|elucidate|develop|construct|evaluate)\b.{0,60}\bwe\b",
    ],
    "methods": [
        r"\bwe (?:performed|conducted|applied|used|employed|collected|downloaded|obtained|analy[sz]ed|integrated)\b",
        r"\b(?:were|was) (?:analy[sz]ed|obtained|downloaded|retrieved|collected|profiled|sequenced|assessed) (?:from|using|by)\b",
        r"\bdata(?:set)?s? (?:were|was) (?:obtained|downloaded|retrieved|collected)\b",
        r"\busing (?:single-?cell|RNA-?seq|scRNA-?seq|WGCNA|LASSO|GSEA|CIBERSORT|the .{0,30} database)\b",
        r"\b(?:differentially expressed genes?|DEGs?|hub genes?|risk score|nomogram) (?:were|was)\b",
        r"\bthe (?:GEO|TCGA|GTEx|UK Biobank|ArrayExpress|DisGeNET|STRING|Metascape) (?:database|dataset|cohort)\b",
    ],
    "result": [
        r"\bwe (?:found|identified|observed|detected|showed|revealed|demonstrated|noted) that\b",
        r"\b(?:a total of|in total),? \d",
        r"\b(?:upregulated|downregulated|overexpressed|underexpressed)\b",
        r"\bwas (?:significantly )?(?:higher|lower|increased|decreased|elevated|reduced) in\b",
        r"\bwere (?:significantly )?(?:enriched|associated|correlated|upregulated|downregulated)\b",
        r"\bsignificant(?:ly)? (?:difference|correlation|association|enrichment)\b",
        r"\bAUC(?:s)? of\b", r"\bhazard ratio\b", r"\b95% (?:confidence interval|CI)\b",
        r"\b(?:expression|levels?) of .{0,40} (?:was|were) (?:higher|lower|increased|elevated)\b",
    ],
    "interpretation": [
        r"\b(?:these|our) (?:findings|results|data) (?:suggest|indicate|imply|highlight|point to)\b",
        r"\bthis (?:suggests|indicates|implies) that\b",
        r"\bmay (?:serve|act|represent|reflect|contribute|be) (?:as )?\b",
        r"\bcould (?:serve|represent|be used|provide)\b",
        r"\bpotentially\b", r"\bpossibly\b", r"\blikely\b", r"\bappears? to\b",
    ],
    "limitation": [
        r"\blimitation", r"\blimited by\b", r"\bshould be interpreted with caution\b",
        r"\bfurther (?:studies|research|work|experiments|validation) (?:are|is) (?:needed|required|warranted|necessary)",
        r"\bwarrant(?:s|ed)? (?:further|additional|experimental)\b",
        r"\bremains? to be (?:determined|validated|confirmed|elucidated)\b",
        r"\bfuture studies (?:should|are needed|may)\b",
        r"\bcannot (?:be )?(?:exclude|rule out)\b", r"\bmay not (?:be )?(?:generaliz|applic|reflect)",
        r"\black of (?:experimental|in vivo|clinical|external) (?:validation|evidence|data)\b",
        r"\bretrospective\b", r"\bsingle-?cent(?:er|re)\b",
    ],
    "outlook": [
        r"\bfuture (?:studies|research|work|investigations) (?:should|will|may|could|need)\b",
        r"\b(?:provide|offers?) (?:new )?(?:insights?|targets?|avenues?|directions?|candidates?)\b",
        r"\bmay (?:guide|inform|facilitate|aid)\b",
        r"\bwarrant(?:s)? (?:clinical|prospective) (?:validation|trials)\b",
        r"\bholds? promise\b", r"\bwarrants? further\b",
        r"\b(?:therapeutic|diagnostic) (?:targets?|strategies|biomarkers?) (?:for|in)\b",
    ],
    "contrast": [
        r"\bin (?:contrast|line) with\b", r"\bby contrast\b", r"\bconsistent with (?:previous|prior|earlier)\b",
        r"\bcontrary to\b", r"\bunlike (?:previous|prior)\b",
        r"\bprevious (?:studies|reports|work) (?:have|has) (?:shown|reported|demonstrated)\b",
        r"\bwhereas\b", r"\bwhile (?:previous|prior|earlier)\b",
        r"\bon the (?:other|contrary) hand\b", r"\bagrees? with\b", r"\bdiffers? from\b",
    ],
}

CONNECTIVES = [
    "however", "moreover", "furthermore", "therefore", "thus", "thereby", "hence",
    "additionally", "in addition", "nevertheless", "nonetheless", "consequently",
    "besides", "meanwhile", "overall", "notably", "importantly", "interestingly",
    "in contrast", "by contrast", "on the other hand", "in particular", "specifically",
    "collectively", "taken together", "respectively", "whereas", "while", "although",
    "though", "despite", "because", "since", "as a result", "for instance", "for example",
    "accordingly", "similarly", "ultimately", "finally", "first", "second", "then",
]

# HEDGES = v1.0「核心口径」（**保持原值不变，历史数值可复现**）
# ⚠️ v2.0（2026-09-26，W39 D06）留痕：v1.0 词表**漏收大量情态/认知限定词**，实测低估约 42%。
#   证据（D06 语料 795 句）：v1.0 命中 165 = 20.8/百句；漏收候选（>0 者）合计 70 = 8.81/百句；
#   两者合并 235 = 29.6/百句。漏收高频项：can 11｜limited 11｜should 7｜unclear 7｜exploratory 7｜
#   often 4｜cannot 3｜estimates 3｜estimated 3｜no significant 3｜did not 2｜preliminary 2。
#   → 直接后果：D03/D04 的「hedge 密度 5.3 / 6.2 未入区间」判据建立在**低估**过的分母上；
#     D05 声称的「rev2 实有 4 处情态、脚本只计 1 处」得到证实。
#   处置：① 保留 v1.0（`HEDGES`）不动，供历史复现；② 新增 v2.0（`HEDGES_V2`）为**新判据口径**；
#     ③ `style_stats` 同时输出两组值，键名后缀区分（无后缀 = v1.0 核心；`_v2` = 扩展）；
#     ④ 依 [ERR-2026W39-26]「修复须同步同类脚本」：`style_compare.py` 直接 `from extract_language import`，
#        本处改动自动生效，无需二次修改（已核）。
#   立 [ERR-2026W39-35]。
HEDGES = [
    "may", "might", "could", "suggest", "suggests", "suggested", "indicate", "indicates",
    "likely", "possibly", "potential", "potentially", "appears", "appear", "seems",
    "approximately", "relatively", "tend", "tends", "putative", "candidate", "presumably",
]

# v2.0 扩展词表：仅收录**认知/情态限定**与**自我设限标记**，不收录纯否定结果标记
# （`no significant` / `did not` / `failed to` 属「阴性结果表述」，单列不计入 hedge，避免混淆两类语义）。
HEDGES_EXTRA = [
    # 情态动词（v1.0 仅收 may/might/could，漏 can/cannot/would/should）
    "can", "cannot", "would", "should",
    # 认知状态词（不确定性直陈）
    "unclear", "uncertain", "unresolved", "unknown",
    # 估计/校准家族
    "estimate", "estimates", "estimated", "expected", "anticipated",
    # 频率/范围缓和词
    "largely", "generally", "mostly", "often", "sometimes", "partly", "roughly",
    # 自我设限标记（C-12 / C-14 家族：把效力上限写进句子）
    "exploratory", "preliminary", "hypothesis-generating", "to our knowledge",
]
HEDGES_V2 = HEDGES + HEDGES_EXTRA

BOOSTERS = [
    "clearly", "obviously", "undoubtedly", "certainly", "definitely", "always", "never",
    "remarkably", "dramatically", "strikingly", "novel", "groundbreaking", "ground-breaking",
    "revolutionary", "unprecedented", "extremely", "crucial", "pivotal", "paramount",
    "invaluable", "game-changing", "breakthrough",
]

AI_TEMPLATES = [
    "plays a crucial role", "plays a pivotal role", "is of great significance",
    "has attracted increasing attention", "hold promise", "holds promise",
    "shed light on", "sheds light on", "provides new insights into", "provide new insights into",
    "opens new avenues", "open new avenues", "has important implications",
    "further research is needed", "in conclusion, our study", "taken together, these findings",
    "it is worth noting that", "delve into", "delves into", "multifaceted", "paradigm shift",
    "underscores the importance", "paves the way", "pave the way", "holistic",
    "leverage", "leveraging", "robust framework", "comprehensive understanding",
    "plays an increasingly important role", "in the realm of", "a growing body of evidence",
    "with the rapid development of", "in recent years, there has been",
]


def split_sentences(text):
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    return [p.strip() for p in parts if len(p.split()) >= 5]


def classify(sent):
    low = sent.lower()
    hits = [role for role, pats in ROLE_CUES.items() if any(re.search(p, low) for p in pats)]
    return hits


def style_stats(sentences):
    lens = [len(s.split()) for s in sentences]
    n = len(lens)
    if not n:
        return {}
    srt = sorted(lens)
    def pct(p):
        return srt[min(n - 1, int(p * n))]
    words = re.findall(r"[a-zA-Z][a-zA-Z-]+", " ".join(sentences).lower())
    low = " ".join(sentences).lower()
    conn = sum(len(re.findall(r"\b" + re.escape(c) + r"\b", low)) for c in CONNECTIVES)
    hedge = sum(len(re.findall(r"\b" + re.escape(c) + r"\b", low)) for c in HEDGES)
    hedge2 = sum(len(re.findall(r"\b" + re.escape(c) + r"\b", low)) for c in HEDGES_V2)
    boost = sum(len(re.findall(r"\b" + re.escape(c) + r"\b", low)) for c in BOOSTERS)
    tmpl = {t: len(re.findall(re.escape(t), low)) for t in AI_TEMPLATES}
    tmpl = {k: v for k, v in tmpl.items() if v}
    return {
        "sentences": n,
        "words": len(words),
        "len_mean": round(sum(lens) / n, 1),
        "len_sd": round((sum((x - sum(lens) / n) ** 2 for x in lens) / n) ** 0.5, 1),
        "len_p10": pct(0.10), "len_p50": pct(0.50), "len_p90": pct(0.90),
        "len_min": min(lens), "len_max": max(lens),
        "share_short_le15": round(sum(1 for x in lens if x <= 15) / n * 100, 1),
        "share_long_ge35": round(sum(1 for x in lens if x >= 35) / n * 100, 1),
        "conn_per_100sent": round(conn / n * 100, 1),
        "conn_types": len({c for c in CONNECTIVES if re.search(r"\b" + re.escape(c) + r"\b", low)}),
        "hedge_per_100sent": round(hedge / n * 100, 1),
        "hedge_per_100sent_v2": round(hedge2 / n * 100, 1),
        "booster_per_100sent": round(boost / n * 100, 1),
        "hedge_booster_ratio": round(hedge / max(boost, 1), 2),
        "hedge_booster_ratio_v2": round(hedge2 / max(boost, 1), 2),
        "ttr": round(len(set(words)) / max(len(words), 1), 3),
        "ai_template_hits": sum(tmpl.values()),
        "ai_template_detail": tmpl,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--per-role", type=int, default=40, help="每个角色最多导出句数")
    ap.add_argument("--dump-abstracts", default="", help="把当日全部摘要写入该文件（作为样本A语料）")
    ap.add_argument("--dump-json", default="", help="文体指标写入 JSON")
    a = ap.parse_args()

    with open(a.csv, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    by_role = {r: [] for r in ROLE_CUES}
    all_sents = []
    for r in rows:
        for s in split_sentences(r.get("abstract", "")):
            all_sents.append(s)
            for role in classify(s):
                by_role[role].append((s, r))

    st = style_stats(all_sents)

    if a.dump_abstracts:
        os.makedirs(os.path.dirname(os.path.abspath(a.dump_abstracts)), exist_ok=True)
        with open(a.dump_abstracts, "w", encoding="utf-8") as f:
            for r in rows:
                f.write((r.get("abstract") or "").strip() + "\n\n")

    L = [
        "# 语言范式原料（样本 A：PubMed 真人原文）",
        "",
        f"- 来源：`{os.path.basename(a.csv)}`，共 **{len(rows)} 篇**摘要",
        f"- 抽取句数：**{len(all_sents)}** 句（仅摘要，未含全文）",
        "- 用途：供归纳「地道高频学术句式清单 / 逻辑衔接范式 / 真人写作习惯特征 / AI 腔黑名单」四份累积文件。",
        "- **证据边界**：本文件只是原料。任何被写入范式库的句子，必须在此文件中可回溯到 PMID。",
        "",
        "---",
        "",
        "## 一、当日真人文本文体指标（样本 A 基线）",
        "",
        "| 指标 | 数值 | 说明 |",
        "|---|---|---|",
        f"| 句子总数 | {st.get('sentences')} | 摘要级语料 |",
        f"| 平均句长（词） | {st.get('len_mean')} | 均值 |",
        f"| 句长标准差 | {st.get('len_sd')} | **越长说明长短句越交错；AI 文本常见偏低** |",
        f"| 句长 P10 / P50 / P90 | {st.get('len_p10')} / {st.get('len_p50')} / {st.get('len_p90')} | 分布形态 |",
        f"| 最短 / 最长句 | {st.get('len_min')} / {st.get('len_max')} | 极差体现节奏 |",
        f"| ≤15 词短句占比 | {st.get('share_short_le15')}% | 真人常用短句下判断 |",
        f"| ≥35 词长句占比 | {st.get('share_long_ge35')}% | 长句比例过高 = 机器味 |",
        f"| 连接词密度（每百句） | {st.get('conn_per_100sent')} | AI 常见 >120 |",
        f"| 连接词种类数 | {st.get('conn_types')} | 种类少而密度高 = 模板堆砌 |",
        f"| 模糊限制语密度（每百句） | {st.get('hedge_per_100sent')} | 审慎语气强度 |",
        f"| 强化词密度（每百句） | {st.get('booster_per_100sent')} | 过度绝对化风险 |",
        f"| hedge / booster 比 | {st.get('hedge_booster_ratio')} | **真人常 >1；AI 稿常 <1** |",
        f"| 类符形符比 TTR | {st.get('ttr')} | 词汇丰富度 |",
        f"| AI 模板短语命中 | {st.get('ai_template_hits')} | 真人语料中本应极低 |",
        "",
    ]
    if st.get("ai_template_detail"):
        L += ["真人语料中命中的模板短语（多为方法学惯用语，需逐条人工判断）：", ""]
        for k, v in sorted(st["ai_template_detail"].items(), key=lambda x: -x[1]):
            L.append(f"- `{k}` × {v}")
        L.append("")

    # ⚠️ 2026-09-28（W40 D01 建池后修复）**IF 口径标注缺失**
    # 原写法 `IF {if_latest} ({if_bin})` **丢掉了 if_year_label / if_metric**，
    # 而 papers.csv 中同列并存两种口径：`JIF_bioxbio`（官方 JIF）与
    # `OA_2yrMCC`（`[代理]OpenAlex-2yrMCC`）。不标注 → 下游难以区分，
    # 直接违反项目红线「官方 JIF 与 OpenAlex 代理值**严禁混称**」。
    # D01 实测：75 篇中 45 篇（60%）为代理值。**改为一律显式标注**。
    def _if_tag(r):
        m = (r.get("if_metric") or "").strip()
        if m == "JIF_bioxbio":
            return "官方 JIF"
        if m == "OA_2yrMCC":
            return "[代理]OpenAlex-2yrMCC"
        return f"口径未标({m or '空'})"

    L += ["---", "", "## 二、按修辞功能分类的真实句子（可直接引用的候选）", ""]
    L += [
        "> **IF 口径声明**：每行 IF 后**必附口径标签**——`官方 JIF` = bioxbio 官方期刊影响因子；"
        "`[代理]OpenAlex-2yrMCC` = OpenAlex 两年平均被引代理值。**两者严禁混称、严禁互相换算**。",
        "",
    ]
    for role, items in by_role.items():
        L += [f"### {role}（命中 {len(items)} 句，展示前 {min(len(items), a.per_role)} 句）", ""]
        for s, r in items[: a.per_role]:
            L.append(
                f"- *{s}*  \n  `PMID {r.get('pmid','')}` ｜ {(r.get('journal_iso') or '').strip()} "
                f"｜ IF {r.get('if_latest','?')} ({r.get('if_bin','')}｜{_if_tag(r)}) ｜ {r.get('mode','')}"
            )
        if not items:
            L.append("- （当日语料未命中该角色线索，可扩大语料或补线索词）")
        L.append("")

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(L))

    if a.dump_json:
        with open(a.dump_json, "w", encoding="utf-8") as f:
            json.dump({"roles": {k: len(v) for k, v in by_role.items()}, "style": st},
                      f, ensure_ascii=False, indent=1)

    print(f"[extract_language] {len(rows)} 篇 / {len(all_sents)} 句 → {a.out}")
    for k, v in by_role.items():
        print(f"  {k:<15} {len(v)}")
    print("  文体指标:", {k: st[k] for k in ("len_mean", "len_sd", "share_short_le15",
                                            "share_long_ge35", "conn_per_100sent",
                                            "hedge_booster_ratio")})


if __name__ == "__main__":
    main()
