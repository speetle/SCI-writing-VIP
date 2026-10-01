#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
results_boundary_scan.py —— Results 段末边界句统计（周课 ⑨ 的 R 章专项）

背景
----
W39 周课 ⑨ 从 **1 篇**深拆（PMID 42737438，14 段中 13 段）得出「Results 每小节末尾
至少 1 句边界句」的四类模板，并在框架模板 §4 列为 `[待校验]`：
**W40 须扩至 ≥20 篇全文统计；命中率 <50% 则降级为"个人风格"而非通用规则。**

本脚本即用于关闭该待校验项。它复用 `imrad_scan.py` 的 PMC 缓存，
对抽中的全文逐段取 **段末句**，按四类边界句模板做正则+特征判定。

四类边界句（框架模板 §2.3）
--------------------------
- 外推边界：`further <prospective/independent> evaluation is required before …`
- 设计边界：`Because <design limit>, <result> cannot <inference>`
- 证据等级边界：`should be regarded as complementary evidence rather than …`
- 统计边界：`describe model-level <property> and do not establish <claim>`

用法
----
python3 results_boundary_scan.py \
  --scan 04_IMRAD架构库/2026-W40_scan.json \
  --cache-dir 04_IMRAD架构库/_pmc_cache \
  --out 04_IMRAD架构库/2026-W40_boundary.json

硬约束
------
- 只用 `depth=full` 的记录；摘要级记录不参与（R4）。
- 剔除 PMC 把图注放进 `<body><p>` 造成的假段落（首词 Fig./Figure/Table/Supplementary + 短段）。
- 只统计 **Results 章（role=R）**；Discussion 的局限段不计入。
"""
import argparse
import json
import os
import re
import statistics
import xml.etree.ElementTree as ET
from collections import Counter

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")

ROLE_MAP = [
    (r"introduction|background", "I"),
    (r"material|method|experimental", "M"),
    (r"result|finding", "R"),
    (r"discussion|conclusion|limitation", "D"),
]

CAPTION_HEAD = re.compile(
    r"^(fig(ure)?s?|table|supplementary|extended\s+data|movie|video)\b", re.I)

# ---- 四类边界句特征 ----
BOUNDARY_PATTERNS = [
    ("外推边界", re.compile(
        r"(further|additional|future|prospective|independent)\s+"
        r"[a-z\-]*\s*(evaluation|validation|studies|study|work|analysis|cohorts?|trials?)"
        r"[^.]{0,60}?\b(is|are|will be|would be|remains?)\b[^.]{0,30}?"
        r"(required|needed|warranted|necessary)|"
        r"(require|need)s?\s+(further|additional|prospective|independent)\s+"
        r"(evaluation|validation|studies|work|analysis)|"
        r"(remains?|is)\s+to\s+be\s+(validated|tested|determined|confirmed)", re.I)),
    ("设计边界", re.compile(
        r"\b(because|given|owing to|due to)\b[^.]{0,120}?"
        r"\b(cannot|can not|should not|may not|do(es)? not allow|preclude[sd]?|"
        r"is not possible|were not possible|was not possible)\b|"
        r"\b(limited|restricted)\s+(to|by)\b[^.]{0,60}?", re.I)),
    ("证据等级边界", re.compile(
        r"(regarded|considered|interpreted|viewed)\s+as\s+"
        r"(complementary|exploratory|hypothesis[- ]generating|preliminary|descriptive|"
        r"nominal|associative)|"
        r"(not|rather than)\s+(independent|functional)\s+"
        r"(evidence|validation|confirmation)|"
        r"(complementary\s+(evidence|to)|hypothesis[- ]generating|exploratory\s+(in\s+nature|only))", re.I)),
    ("统计边界", re.compile(
        r"(do(es)? not|did not|cannot|can not)\s+"
        r"(establish|demonstrate|prove|imply|indicate|support|reflect|represent)\b|"
        r"(reflect|describe|represent|capture)s?\s+"
        r"(model[- ]level|predictive|associative|correlative|statistical)\b|"
        r"(association|correlation|predictive)\s+rather\s+than\s+"
        r"(causation|causality|mechanism|biological)", re.I)),
]

# 通用"限定/降级"词（不进四类，但计入"含边界意味"）
SOFT_BOUNDARY = re.compile(
    r"\b(however|nevertheless|nonetheless|should be (interpreted|cautious|treated)|"
    r"caution|warrant(s|ed)?|preliminary|exploratory|caveat|"
    r"not\s+(statistically\s+)?significant|"
    r"limited\s+(power|sample|cohort|resolution|generalizab)|"
    r"cannot\s+be\s+(excluded|ruled out|generalized)|"
    r"may\s+(not|reflect|be\s+confounded)|"
    r"no\s+(significant|evidence of)|"
    r"failed?\s+to|did\s+not\s+(reach|achieve|survive|remain))\b", re.I)


def norm(t):
    return re.sub(r"\s+", " ", t or "").strip()


def sentences(text):
    text = norm(text)
    return [s for s in SENT_SPLIT.split(text) if len(s.split()) >= 4]


def nwords(s):
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", s))


def role_of(title):
    t = (title or "").lower()
    for pat, role in ROLE_MAP:
        if re.search(pat, t):
            return role
    return "?"


def classify(sent):
    for name, pat in BOUNDARY_PATTERNS:
        if pat.search(sent):
            return name
    if SOFT_BOUNDARY.search(sent):
        return "软限定（非四类）"
    return None


def parse_results_paragraphs(xml_path):
    """返回 [(results_unit_title, paragraph_text), ...]

    unit = Results 章的**最细小节**（有子章节用子章节标题，否则用章标题），
    以便按「每个小节末尾」的口径检验边界句规则。
    """
    try:
        root = ET.fromstring(open(xml_path, "rb").read())
    except Exception:                                            # noqa: BLE001
        return []
    body = root.find(".//body")
    if body is None:
        return []
    out = []
    for sec in body.findall("./sec"):
        title_el = sec.find("./title")
        title = norm("".join(title_el.itertext())) if title_el is not None else "(untitled)"
        if role_of(title) != "R":
            continue
        units = []
        subs = [s for s in sec.findall("./sec") if s.find("./title") is not None]
        if subs:
            for s in subs:
                units.append((norm("".join(s.find("./title").itertext())), s))
        else:
            units.append((title, sec))
        for utitle, node in units:
            for p in node.findall(".//p"):
                if p.findall(".//p"):        # 跳过容器节点
                    continue
                t = norm("".join(p.itertext()))
                if nwords(t) < 25:
                    continue
                if CAPTION_HEAD.match(t) and nwords(t) <= 90:   # 图注误入 <body><p>
                    continue
                out.append((utitle, t))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scan", required=True)
    ap.add_argument("--cache-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    data = json.load(open(a.scan, encoding="utf-8"))
    recs = data["records"]
    rows = []
    para_types = Counter()
    n_para_total = 0
    n_para_with = 0
    per_paper = []

    for r in recs:
        if r.get("depth") != "full":
            continue
        pmcid = (r.get("pmcid") or "").strip()
        xml_path = os.path.join(a.cache_dir, pmcid + ".xml")
        if not pmcid or not os.path.exists(xml_path):
            continue
        paras = parse_results_paragraphs(xml_path)
        if not paras:
            continue
        # 逐段取段末句
        last_types = []
        for _, t in paras:
            ss = sentences(t)
            if not ss:
                continue
            last = ss[-1]
            if nwords(last) < 5:
                last = " ".join(ss[-2:]) if len(ss) >= 2 else last
            c = classify(last)
            last_types.append((c, last, nwords(last)))
            n_para_total += 1
            if c:
                n_para_with += 1
                para_types[c] += 1
        # 每篇：末段末句是否边界句（"每小节末尾至少 1 句"的可核验代理）
        n_sect_strict = 0     # 最后一段的末句是边界句
        n_sect_loose = 0      # 最后两段的末句任一为边界句
        sect_titles = sorted({tt for tt, _ in paras})
        for st in sect_titles:
            sp = [t for tt, t in paras if tt == st]
            if not sp:
                continue
            tails = []
            for pp in (sp[-1], sp[-2] if len(sp) >= 2 else None):
                if not pp:
                    continue
                ss = sentences(pp)
                if ss:
                    tails.append(classify(ss[-1]))
            if tails and tails[0]:
                n_sect_strict += 1
            if any(tails):
                n_sect_loose += 1
        per_paper.append({
            "pmid": r["pmid"], "journal": r["journal"], "if_bin": r["if_bin"],
            "mode": r["mode"], "n_para": len(paras),
            "n_para_with_boundary": sum(1 for c, _, _ in last_types if c),
            "para_hit_rate": round(100 * sum(1 for c, _, _ in last_types if c) / len(last_types), 1),
            "n_results_sections": len(sect_titles),
            "n_sections_strict": n_sect_strict,
            "n_sections_loose": n_sect_loose,
            "last_sent_len_median": round(statistics.median([l for _, _, l in last_types]), 1),
            "examples": [{"type": c, "sent": s} for c, s, _ in last_types if c][:3],
        })

    n_paper = len(per_paper)
    papers_with_any = sum(1 for p in per_paper if p["n_para_with_boundary"] > 0)
    med_rate = round(statistics.median([p["para_hit_rate"] for p in per_paper]), 1) if n_paper else None
    sect_total = sum(p["n_results_sections"] for p in per_paper)
    sect_strict = sum(p["n_sections_strict"] for p in per_paper)
    sect_loose = sum(p["n_sections_loose"] for p in per_paper)

    # 章节顺序统计
    by_bin = Counter()
    for r in recs:
        if r.get("depth") != "full":
            continue
        roles = r.get("section_roles") or []
        try:
            by_bin[(r["if_bin"], "M_before_D" if roles.index("M") < roles.index("D") else "M_after_D")] += 1
        except ValueError:
            continue

    summary = {
        "n_papers_full_in_scan": sum(1 for r in recs if r.get("depth") == "full"),
        "n_papers_with_results_parsed": n_paper,
        "n_results_paragraphs": n_para_total,
        "n_para_with_boundary": n_para_with,
        "para_hit_rate_pct": round(100 * n_para_with / n_para_total, 1) if n_para_total else None,
        "per_paper_median_para_hit_rate_pct": med_rate,
        "papers_with_at_least_one_boundary": papers_with_any,
        "papers_with_at_least_one_boundary_pct": round(100 * papers_with_any / n_paper, 1) if n_paper else None,
        "results_units_total": sect_total,
        "results_units_strict_hit": sect_strict,
        "results_unit_strict_hit_rate_pct": round(100 * sect_strict / sect_total, 1) if sect_total else None,
        "results_units_loose_hit": sect_loose,
        "results_unit_loose_hit_rate_pct": round(100 * sect_loose / sect_total, 1) if sect_total else None,
        "boundary_type_distribution": dict(para_types),
        "methods_vs_discussion_order": {f"{k[0]}|{k[1]}": v for k, v in by_bin.items()},
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump({"summary": summary, "papers": per_paper}, open(a.out, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"-> {a.out}")


if __name__ == "__main__":
    main()
