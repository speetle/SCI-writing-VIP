#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
imrad_scan.py —— IMRAD 结构扫面（周课 ⑨ 第一步）

职责：从本周文献池按 IF 区间配额抽取 N 篇，逐篇解析**真实全文**的章节组织，
产出可统计的结构数据（章节顺序、段落数、章内句长分布、图注首句、限制节位置）。

深度声明（硬约束）
----------------
- 取到 PMC 全文 → 记为 `full`
- 取不到全文 → 记为 `abstract`，**仅统计摘要结构，不参与方法学细节统计**

用法
----
python3 imrad_scan.py --pool 01_文献库/2026-W39/papers_master.csv \
  --out 04_IMRAD架构库/2026-W39_scan.json --n 50 --seed 20260921
"""
import argparse
import csv
import json
import os
import random
import re
import statistics
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

QUOTA = {">10": 15, "5-10": 20, "3-5": 10, "1-3": 5}

# 章节标题 → 规范角色
ROLE_MAP = [
    (r"introduction|background", "I"),
    (r"material|method|experimental", "M"),
    (r"result|finding", "R"),
    (r"discussion|conclusion|limitation", "D"),
]


def http_get(u, timeout=60, retries=3):
    last = None
    for i in range(retries):
        try:
            return urllib.request.urlopen(
                urllib.request.Request(u, headers={"User-Agent": "SCI-writing-VIP/1.0"}),
                timeout=timeout).read()
        except Exception as e:                                # noqa: BLE001
            last = e
            time.sleep(2 + 2 * i)
    raise last


def fetch_pmc(pmcid):
    u = f"{EUTILS}/efetch.fcgi?db=pmc&retmode=xml&id={pmcid}"
    try:
        xml = http_get(u)
    except Exception:                                          # noqa: BLE001
        return None
    if b"<article" not in xml:
        return None
    try:
        return ET.fromstring(xml)
    except Exception:                                          # noqa: BLE001
        return None


# ---------- 文本工具 ----------

SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


def norm(t):
    return re.sub(r"\s+", " ", t or "").strip()


def sentences(text):
    text = norm(text)
    return [s for s in SENT_SPLIT.split(text) if len(s.split()) >= 4]


def nwords(s):
    return len(re.findall(r"[A-Za-z][A-Za-z'\-]*", s))


# ---------- 解析一篇全文 ----------

def parse_full(root):
    body = root.find(".//body")
    if body is None:
        return None
    secs = []
    for sec in body.findall("./sec"):
        title_el = sec.find("./title")
        title = norm("".join(title_el.itertext())) if title_el is not None else "(untitled)"
        # 注意：必须递归取段。多数期刊把 <p> 放在 <sec> 的**子章节**内
        # （如 Materials and Methods > Statistical analysis > <p>），
        # 只取直接子级 "./p" 会导致 M/R 章统计样本坍塌为 0。
        paras = []
        for p in sec.findall(".//p"):
            if p.findall(".//p"):          # 跳过容器节点，只要叶级段落
                continue
            t = norm("".join(p.itertext()))
            if nwords(t) >= 25:            # 过滤超短行（公式编号等）
                paras.append(t)
        # 子标题
        sub = [norm("".join(s.find("./title").itertext()))
               for s in sec.findall("./sec") if s.find("./title") is not None]
        secs.append({"title": title, "subsections": sub,
                     "n_para": len(paras), "paras": paras})
    figs = []
    for f in root.findall(".//fig"):
        cap = f.find("./caption")
        if cap is not None:
            t = norm("".join(cap.itertext()))
            if t:
                figs.append(t)
    return {"sections": secs, "figs": figs,
            "has_backmatter_limitations": bool(
                re.search(r"limitation", " ".join(
                    norm("".join(x.itertext())) for x in root.findall(".//back//title"))))}


def role_of(title):
    t = title.lower()
    for pat, role in ROLE_MAP:
        if re.search(pat, t):
            return role
    return "?"


def section_stats(secs):
    """每章：段落数、句数、句长均值/SD、短句与长句占比"""
    out = []
    for s in secs:
        sents = [x for p in s["paras"] for x in sentences(p)]
        if not sents:
            out.append({"title": s["title"], "role": role_of(s["title"]),
                        "subsections": s["subsections"], "n_para": s["n_para"],
                        "n_sent": 0, "paragraph_sent_median": None,
                        "sent_words_mean": None, "sent_words_sd": None,
                        "short_pct": None, "long_pct": None})
            continue
        L = [nwords(x) for x in sents]
        psc = [len(sentences(p)) for p in s["paras"] if sentences(p)]
        out.append({
            "title": s["title"], "role": role_of(s["title"]),
            "subsections": s["subsections"], "n_para": s["n_para"],
            "n_sent": len(sents),
            "paragraph_sent_median": statistics.median(psc) if psc else None,
            "sent_words_mean": round(statistics.mean(L), 1),
            "sent_words_sd": round(statistics.pstdev(L), 1) if len(L) > 1 else None,
            "short_pct": round(100 * sum(1 for x in L if x <= 15) / len(L), 1),
            "long_pct": round(100 * sum(1 for x in L if x >= 35) / len(L), 1),
        })
    return out


def abstract_labels(ab):
    labs = []
    for lab in ("BACKGROUND", "OBJECTIVE", "AIM", "METHODS", "RESULTS",
                "CONCLUSION", "INTRODUCTION", "PURPOSE"):
        if re.search(r"(^|\s)" + lab + r"\s*:", ab, re.I):
            labs.append(lab.upper())
    return labs


# ---------- 抽样 ----------

def sample(rows, n, seed):
    rnd = random.Random(seed)
    pure = [r for r in rows if r["mode"] == "纯生信"]
    drywet = [r for r in rows if r["mode"] == "干湿结合"]
    picked, seen = [], set()

    def take(pool, k, why):
        got = 0
        by = defaultdict(list)
        for r in pool:
            by[r["if_bin"]].append(r)
        for b in [">10", "5-10", "3-5", "1-3", "<1", "UNBINNED"]:
            for r in by.get(b, []):
                if got >= k:
                    return
                if r["pmid"] in seen:
                    continue
                seen.add(r["pmid"])
                picked.append(dict(r, _why=why))
                got += 1

    take(pure, 10, "纯生信配额")
    take(drywet, 10, "干湿结合配额")

    by_bin = defaultdict(list)
    for r in rows:
        if r["pmid"] not in seen:
            by_bin[r["if_bin"]].append(r)
    for b, q in QUOTA.items():
        have = sum(1 for x in picked if x["if_bin"] == b)
        need = max(0, q - have)
        cand = sorted(by_bin.get(b, []), key=lambda x: -float(x["score"] or 0))
        if not cand or need == 0:
            continue
        step = max(1, len(cand) // need)
        for r in cand[::step][:need]:
            if r["pmid"] in seen:
                continue
            seen.add(r["pmid"])
            picked.append(dict(r, _why="区间配额"))
    return picked[:n]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pool", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--seed", type=int, default=20260921)
    ap.add_argument("--cache-dir", default="")
    ap.add_argument("--sleep", type=float, default=0.5)
    a = ap.parse_args()

    with open(a.pool, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r.get("pmid")]
    picked = sample(rows, a.n, a.seed)
    print(f"[scan] 抽中 {len(picked)} 篇 "
          f"(纯生信 {sum(1 for x in picked if x['mode']=='纯生信')}, "
          f"干湿结合 {sum(1 for x in picked if x['mode']=='干湿结合')})", file=sys.stderr)

    cache = a.cache_dir or os.path.join(os.path.dirname(os.path.abspath(a.out)), "_pmc_cache")
    os.makedirs(cache, exist_ok=True)

    recs = []
    for i, r in enumerate(picked, 1):
        rec = {"pmid": r["pmid"], "pmcid": r.get("pmcid", ""), "title": r["title"],
               "journal": r["journal_iso"], "if_bin": r["if_bin"],
               "if_latest": r.get("if_latest", ""), "if_metric": r.get("if_metric", ""),
               "mode": r["mode"], "depth": "abstract", "reason": r.get("_why", ""),
               "abstract_labels": abstract_labels(r["abstract"]),
               "n_abs_sent": len(sentences(r["abstract"]))}
        pmcid = (r.get("pmcid") or "").strip()
        if re.match(r"^PMC\d+$", pmcid):
            cf = os.path.join(cache, pmcid + ".xml")
            root = None
            if os.path.exists(cf):
                try:
                    root = ET.fromstring(open(cf, "rb").read())
                except Exception:                              # noqa: BLE001
                    root = None
            if root is None:
                root = fetch_pmc(pmcid)
                if root is not None:
                    open(cf, "wb").write(ET.tostring(root))
                time.sleep(a.sleep)
            if root is not None:
                pf = parse_full(root)
                if pf and pf["sections"]:
                    rec["depth"] = "full"
                    rec["section_order"] = [s["title"] for s in pf["sections"]]
                    rec["section_roles"] = [role_of(s["title"]) for s in pf["sections"]]
                    rec["sections"] = section_stats(pf["sections"])
                    rec["n_sections_body"] = len(pf["sections"])
                    rec["fig_captions"] = len(pf["figs"])
                    rec["fig_first_sent"] = [sentences(x)[0] for x in pf["figs"][:4] if sentences(x)]
                    rec["has_backmatter_limitations"] = pf["has_backmatter_limitations"]
                    rec["limitation_in_discussion"] = any(
                        re.search(r"limitation", s["title"], re.I) or
                        any(re.search(r"limitation", x, re.I) for x in s["subsections"])
                        for s in pf["sections"])
        recs.append(rec)
        print(f"  [{i}/{len(picked)}] {rec['pmid']} {rec['depth']:<8} "
              f"{rec['journal'][:20]:<22} {rec['title'][:52]}", file=sys.stderr)

    full = [r for r in recs if r["depth"] == "full"]
    summary = {
        "generated": time.strftime("%Y-%m-%d %H:%M"),
        "pool": os.path.abspath(a.pool),
        "n_sampled": len(recs),
        "n_full": len(full),
        "n_abstract": len(recs) - len(full),
        "full_text_rate": round(100 * len(full) / len(recs), 1),
        "bin_dist": dict(Counter(r["if_bin"] for r in recs)),
        "mode_dist": dict(Counter(r["mode"] for r in recs)),
        "full_by_bin": dict(Counter(r["if_bin"] for r in full)),
        "full_by_mode": dict(Counter(r["mode"] for r in full)),
    }
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump({"summary": summary, "records": recs}, f, ensure_ascii=False, indent=2)
    print(f"[scan] 全文可得 {len(full)}/{len(recs)} = {summary['full_text_rate']}% -> {a.out}")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
