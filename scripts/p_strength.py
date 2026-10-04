#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P1–P4「问题表述强度」量化脚本（W40 D05 建，服务 daily-sop §5-0）

口径四项声明
  · 词表范围：见下 ASSERTIVE / WEAKCAUSAL / SPECULATIVE 三张表（本脚本内硬编码）
  · 分句口径：按 [.!?] 切分 + 去空白；剔除 <6 词的残片
  · 过滤条件：仅取传入文本的正文；本脚本不读附录
  · 脚本名：p_strength.py（自建，非 skill 内既有脚本）

P4 断言强度评分规则（0–3，自建指数，非文献定论）

  ⚠️ 与 daily-sop §5-0 表格文字的关系（须同时声明，防"口径随值走"）：
     SOP 原文字面为「3=强因果+量化／2=直接因果／1=弱化因果／0=纯推测」。
     本脚本把「3」由"强因果动词 + 量化"放宽为「**报告性/因果性动词 + 句内量化**」——
     理由：本语料（生物医学摘要 / Results）的量化断言绝大多数写成 `was associated with (OR…, 95% CI…, p…)`，
     若"3"必须同时满足"强因果动词"，则该档在本语料中将近乎不存在（实测 ≤1%），
     失去"真人是否敢把话说到位"的区分力。**该放宽已在本文件顶部声明，属显式口径变更，不属静默改判。**

  打分分支（互斥，自上而下取首个命中）
     0 = 纯推测：命中 SPECULATIVE 且**不含任何报告性动词**（ASSERTIVE / WEAKCAUSAL 均无）
     3 = 量化断言：句内含 QUANT（% / OR / CI / p / n = / β / 倍数 / AUC 值），且至少一个报告性动词
     2 = 定性因果断言：命中 ASSERTIVE，句内无 QUANT
     1 = 定性关联断言：命中 WEAKCAUSAL，句内无 QUANT
"""
import csv
import json
import re
import statistics
import sys

ASSERTIVE = r"""\b(drives?|driven|shapes?|shaped|determines?|determined|confers?|conferred|governs?|governed|
establishes?|established|reveals?|revealed|demonstrates?|demonstrated|identif(?:y|ies|ied|ying)|
confirms?|confirmed|shows?|showed|shown|abolish(?:es|ed)?|restrict(?:s|ed|ing)?|localiz(?:es|ed)|localis(?:es|ed)|
produces?|produced|recapitulat(?:es|ed)|eliminat(?:es|ed)|causes?|caused|mediate[sd]?|mediating|
define[sd]?|defining|require[sd]?|requiring|enables?|enabled|promotes?|promoted|suppress(?:es|ed)|
increas(?:es|ed|ing)|decreas(?:es|ed|ing)|reduc(?:es|ed|ing)|impair(?:s|ed)|enhanc(?:es|ed)|block(?:s|ed)|inhibit(?:s|ed))\b"""
WEAKCAUSAL = r"""\b(associat(?:es|ed)|correlat(?:es|ed)|link(?:s|ed)|relat(?:es|ed)|contribut(?:es|ed)|
observed|found|detected|indicat(?:es|ed|ing)|suggest(?:s|ed)|trend(?:s|ed)|appeared)\b"""
SPECULATIVE = r"""\b(may|might|could|possibly|potentially|apparently|perhaps|likely|unlikely|candidate|
potential|presumably|seem(?:s|ed)?|appear(?:s|ed)?)\b"""
QUANT = r"(\d+(?:\.\d+)?\s?%|\bn\s?=\s?\d|\b\d+(?:\.\d+)?-fold|\bp\s?[<=]\s?[\d.]|95%\s?(?:CI|confidence interval)|\bOR\s?=|\bAUC\s?[=><]|\bβ\s?=|q\s?=\s?[\d.])"
DISCLAIM_CHAIN = r"(does not|do not|did not|cannot|is not|are not|not constitute|should not be (?:interpreted|taken|considered)|rather than (?:a|an|an?\s+\w+\s+)?(?:causal|independent|direct))"


def sentences(text):
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?])\s+", text)
    out = []
    for p in parts:
        p = p.strip()
        if len(p.split()) >= 6:
            out.append(p)
    return out


def score(s):
    a = bool(re.search(ASSERTIVE, s, re.I))
    w = bool(re.search(WEAKCAUSAL, s, re.I))
    sp = bool(re.search(SPECULATIVE, s, re.I))
    q = bool(re.search(QUANT, s, re.I))
    if (a or w) and q:
        return 3
    if a:
        return 2
    if sp and not a and not w:
        return 0
    if w:
        return 1
    return 1


def report(name, sents):
    sc = [score(s) for s in sents]
    di = sum(1 for s in sents if re.search(DISCLAIM_CHAIN, s, re.I))
    a = sum(1 for s in sents if re.search(ASSERTIVE, s, re.I))
    sp = sum(1 for s in sents if re.search(SPECULATIVE, s, re.I))
    n = len(sents)
    d = {
        "name": name,
        "n_sent": n,
        "P4_mean": round(statistics.mean(sc), 2) if n else None,
        "P4_sd": round(statistics.pstdev(sc), 2) if n else None,
        "P4_dist": {k: sc.count(k) for k in (0, 1, 2, 3)},
        "P4_share_ge2": round(100 * sum(1 for x in sc if x >= 2) / n, 1) if n else None,
        "P2_assertive_per100": round(100 * a / n, 1) if n else None,
        "P2_speculative_per100": round(100 * sp / n, 1) if n else None,
        "P2_ratio_assert_over_spec": round(a / sp, 2) if sp else None,
        "disclaimer_sent_per100": round(100 * di / n, 1) if n else None,
    }
    return d


def main():
    toppool = sys.argv[1]
    mine = sys.argv[2]
    out = sys.argv[3]

    res = []

    # ---- 顶刊池 2024–2026 摘要（近两年层，P1–P4 首选样本）
    sel = []
    with open(toppool, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("year") in ("2024", "2025", "2026") and (r.get("abstract") or "").strip():
                sel.append(r)
    corpus = []
    for r in sel:
        corpus.extend(sentences(r["abstract"]))
    res.append(report("顶刊池 2024–2026 摘要（n_journals=%d）" % len({r["journal_iso"] for r in sel}), corpus))

    # ---- 顶刊池 2016–2023（历史层，供年代对照）
    hist = []
    with open(toppool, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            if r.get("year") in tuple(str(y) for y in range(2016, 2024)) and (r.get("abstract") or "").strip():
                hist.append(r)
    hc = []
    for r in hist:
        hc.extend(sentences(r["abstract"]))
    res.append(report("顶刊池 2016–2023 摘要（历史层）", hc))

    # ---- 我的初稿（正文区：剔除 # 标题行 / > 引用块 / <!-- APPENDIX --> 之后）
    body = []
    with open(mine, encoding="utf-8") as f:
        raw = f.read()
    raw = re.split(r"<!--\s*APPENDIX\s*-->", raw, maxsplit=1)[0]
    for line in raw.splitlines():
        s = line.strip()
        if not s or s.startswith("#") or s.startswith(">"):
            continue
        if re.match(r"^[-*|]", s) or s.startswith("**") and s.endswith("**"):
            continue
        body.append(s)
    res.append(report("我的初稿（Results 段·正文区）", sentences(" ".join(body))))

    with open(out, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
