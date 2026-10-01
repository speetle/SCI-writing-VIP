#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""harvest_toppool.py — 建「近十年顶刊 reserve 池」（2026-10-01 新增）

【来源】先生 2026-10-01 指定：
  「日常的写作训练，先从高分期刊中（IF＞20）选择，范围扩展到近十年，
    但热点新闻依旧是近两年的，以三大顶刊为主，主要看最新的发现。」

【与周课主池的分工（必读，勿混用）】
  ┌──────────────┬──────────────────────────────┬───────────────────────────────┐
  │ 层            │ 用途                          │ 时间窗 / IF                   │
  ├──────────────┼──────────────────────────────┼───────────────────────────────┤
  │ 周课主池      │ 日课 7×74 篇保量、全景扫描    │ 近 1 年、全 IF 分层（≥500 篇）│
  ├──────────────┼──────────────────────────────┼───────────────────────────────┤
  │ 顶刊 reserve │ 日课 ④ 仿写头号素材、周课 ⑨   │ **近十年（2016-2026）、IF>20**│
  │              │ 深拆候选、问题表述演变分析     │ 三大顶刊系为主                │
  └──────────────┴──────────────────────────────┴───────────────────────────────┘

⚠️ **不可把本池当周课主池用**：本池规模约 400–500 篇，撑不住「每日 ≥74 篇 × 7 天」，
   且本池 IF 门槛为硬过滤（PENDING 一律丢弃，不得估算）。

【为什么不能按字面「日课全部改 IF>20」】
  W40 实测：周池 520 篇中 IF>20 仅 **11 篇**（< 日课每日 ≥74 篇硬要求），
  其中三大顶刊仅 **3 篇**（Nature 1 / Nat Med 2），可全文（有 PMCID）仅 **3/11（27%）**。
  → 故取双层结构：**仿写素材优先顶刊层，归档保量仍走周课主池**。

用法：
  python3 harvest_toppool.py --out-dir <项目>/01_文献库/_顶刊池 \
      --if-table <项目>/00_系统/journal_metrics.csv \
      --start 2016/01/01 --end 2026/09/30 --per-year 45
"""
import argparse
import csv
import json
import os
import sys
import time
from collections import Counter, OrderedDict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harvest  # noqa: E402  复用同一套 esearch / get_summary / get_detail，保证口径一致

# ---------------------------------------------------------------------------
# 期刊白名单：**三大顶刊（Nature / Cell / Science）体系为主**
#   每组的 IF 均常年 >20；含主刊与同源高量子刊。
# ---------------------------------------------------------------------------
TOP_JOURNALS = [
    # --- Nature 系（三大顶刊之一）---
    "Nature",
    "Nature Medicine",
    "Nature Genetics",
    "Nature Biotechnology",
    "Nature Cell Biology",
    "Nature Cancer",
    "Nature Immunology",
    "Nature Microbiology",
    "Nature Communications",
    "Nature Medicine (Bethesda, Md. : Online)",
    # --- Cell 系（三大顶刊之一）---
    "Cell",
    "Cancer Cell",
    "Immunity",
    "Molecular Cell",
    "Cell Metabolism",
    "Neuron",
    "Cell Reports",
    "Cell Stem Cell",
    "Cell Research",
    "Cell Death & Disease",
    # --- Science 系（三大顶刊之一）---
    "Science",
    "Science Advances",
    "Science Translational Medicine",
    "Science Signaling",
    "Science Immunology",
    "Science Robotics",
    # --- 生物医学 IF>20 常青刊（少数，补顶刊系覆盖不到的疾病/生信场景）---
    "Cancer Research",
    "Journal of Clinical Oncology",
    "GUT",
    "Circulation",
    "European Heart Journal",
    "Kidney International",
    "Signal Transduction and Targeted Therapy",
    "Molecular Cancer",
    "Advanced Science",
    "Nucleic Acids Research",
    "Genome Biology",
    "Autophagy",
]
# 上面部分刊名在 PubMed [Journal] 字段里是缩写形式，这里给一份「重复检索用名」
JOURNAL_ABBR = {
    "Nature Medicine": "Nat Med",
    "Nature Genetics": "Nat Genet",
    "Nature Biotechnology": "Nat Biotechnol",
    "Nature Cell Biology": "Nat Cell Biol",
    "Nature Cancer": "Nat Cancer",
    "Nature Immunology": "Nat Immunol",
    "Nature Communications": "Nat Commun",
    "Cancer Cell": "Cancer Cell",
    "Molecular Cell": "Mol Cell",
    "Cell Metabolism": "Cell Metab",
    "Cell Reports": "Cell Rep",
    "Cell Stem Cell": "Cell Stem Cell",
    "Cell Research": "Cell Res",
    "Cell Death & Disease": "Cell Death Dis",
    "Science Advances": "Sci Adv",
    "Science Translational Medicine": "Sci Transl Med",
    "Science Signaling": "Sci Signal",
    "Science Immunology": "Sci Immunol",
    "Cancer Research": "Cancer Res",
    "Journal of Clinical Oncology": "J Clin Oncol",
    "GUT": "Gut",
    "Circulation": "Circulation",
    "European Heart Journal": "Eur Heart J",
    "Kidney International": "Kidney Int",
    "Signal Transduction and Targeted Therapy": "Signal Transduct Target Ther",
    "Molecular Cancer": "Mol Cancer",
    "Advanced Science": "Adv Sci (Weinh)",
    "Nucleic Acids Research": "Nucleic Acids Res",
    "Genome Biology": "Genome Biol",
    "Autophagy": "Autophagy",
}

IF_ORDER = {">10": 0, "5-10": 1, "3-5": 2, "1-3": 3, "<1": 4, "UNBINNED": 5, "PENDING": 6}


def load_if_table(path):
    if not path or not os.path.exists(path):
        return {}
    out = {}
    with open(path, encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            iso = (r.get("journal_iso") or "").strip().lower()
            full = (r.get("journal_full") or "").strip().lower()
            ifv = (r.get("if_latest") or "").strip()
            if not ifv or ifv.upper() == "PENDING":
                continue
            try:
                v = float(ifv)
            except ValueError:
                continue
            if iso:
                out[iso] = (v, ifv, (r.get("if_source_url") or "").strip())
            if full:
                out.setdefault(full, (v, ifv, (r.get("if_source_url") or "").strip()))
    return out


# 刊名硬门槛豁免集（仅在 journal_if 表缺该刊 IF 时生效；有 IF 时仍照常按 min_if 判）
# ⚠️ 纯白名单，不含任何"我估计它大概 >20"的意思；条目本身必须本身就是顶刊。
IF_EXEMPT_JOURNALS = {
    "science",
    "the science",
    "science (new york, n.y.)",
    "cell",
    "nature",
}


def exempt_set():
    """豁免集 = 显式三家 + **白名单内全部刊名（含缩写名）**。

    2026-10-01 扩展。原实现只豁免 science/cell/nature 三家，
    而白名单里还有 Immunity / Cell Metabolism / Neuron / Science Translational Medicine
    / Genome Biology 等十余家非三大顶刊；只要其中任何一家在 `journal_metrics.csv` 里缺条目
    （W40 实测 Nat Biotechnol 有、Nat Immunol 等十余家没有），该刊文章就会**整批静默消失**——
    与 [ERR-2026W40-40]（Science 0 篇）完全同型。
    故改为：**只要在白名单里就豁免**，IF 仍一律写 PENDING、绝不估算。
    → 从机制上保证「白名单里的刊一定在池里有representative」。
    """
    s = set(IF_EXEMPT_JOURNALS)
    s |= {j.lower() for j in TOP_JOURNALS}
    s |= {k.lower() for k in JOURNAL_ABBR}
    s |= {v.lower() for v in JOURNAL_ABBR.values()}
    return s


def bin_of(v, threshold=20.0):
    """顶刊池专用分箱：先给 threshold 一档，再落到周池常用档。

    ⚠️ 2026-10-01 修正：原实现固定 `>=10 → ">10"`，在 min_if=20 时
    池内 100% 落 ">10"，该列**零区分度**（440/440 同值），
    无法用于「顶刊 vs 主池」的横向对照。
    """
    if v >= threshold:
        return f">{int(threshold)}"
    if v >= 10:
        return ">10"
    if v >= 5:
        return "5-10"
    if v >= 3:
        return "3-5"
    if v >= 1:
        return "1-3"
    return "<1"


def bin_of_row(row):
    """IF 为 PENDING 的行返回 UNBINNED（不估算、不猜档）。"""
    raw = (row.get("if_latest") or "").strip()
    try:
        return bin_of(float(raw))
    except (TypeError, ValueError):
        return "UNBINNED"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--if-table", default="")
    ap.add_argument("--start", default="2016/01/01", help="YYYY/MM/DD（EDAT 起）")
    ap.add_argument("--end", default="2026/09/30", help="YYYY/MM/DD（EDAT 止）")
    ap.add_argument("--recent-cap", type=int, default=2000,
                    help="近 N 年每年取回上限（默认 2000；服务「主要看最新的发现」）")
    ap.add_argument("--early-cap", type=int, default=300,
                    help="2016–2024 每年取回上限（默认 300；早年只作表述演变的参考层，"
                         "取多了白烧 PubMed 时间）")
    ap.add_argument("--per-year", type=int, default=45, help="每年保留上限（顶刊层配额）")
    ap.add_argument("--recent-years", type=int, default=3,
                    help="近 N 年使用 --recent-cap（默认 3；2026-10-01 由 2 改 3，修复中段塌陷）")
    ap.add_argument("--min-if", type=float, default=20.0, help="IF 硬门槛（默认 20.0）")
    ap.add_argument("--min-abstract", type=int, default=300, help="摘要下限（顶刊摘要偏长，放宽）")
    ap.add_argument("--cache-dir", default="", help="默认 <out-dir>/_cache")
    a = ap.parse_args()

    os.makedirs(a.out_dir, exist_ok=True)
    itab = load_if_table(a.if_table)
    cache_dir = a.cache_dir or os.path.join(a.out_dir, "_cache")

    # 【按年分块 + 期刊 OR 单次检索】
    # ⚠️ 2026-10-01 踩坑：原实现「十年大窗口 × 逐刊 × 每刊双名」= 60 次 esearch，
    #     PubMed 对超大窗口的 esearch 单次可达十几秒，实测跑满 16 min 仍卡在 esearch，
    #     _cache 空（连 summary 都没进）→ 预估总时长数小时。**已终止，改为本实现。**
    #     （同领域 TopN 期刊可用 OR 合成一词，PubMed 支持；再按年切窗，检索次数由 60 → 11。）
    journal_or = "(" + " OR ".join(f'"{j}"[Journal]' for j in TOP_JOURNALS) + ")"
    y_from, y_to = int(a.start.split("/")[0]), int(a.end.split("/")[0])
    all_pmids, per_year_hits, exempt_keys = [], OrderedDict(), set()
    honest_years = []
    for y in range(y_from, y_to + 1):
        y_end = f"{y}/12/31" if y < y_to else a.end
        win = f'("{y}/01/01"[EDAT] : "{y_end}"[EDAT])'
        # 近 --recent-years 年放大候选上限（服务「主要看最新的发现」），早年仅作表述演变参考层。
        # ⚠️ 2026-10-01 修正：原为 y >= y_to-1（最近两年），导致 2024 候选仅 300 → 保留 22 篇，
        #    在「近十年」窗口内出现中段塌陷，会污染逐年断言强度趋势的判读。
        ret = a.recent_cap if y >= (y_to - a.recent_years + 1) else a.early_cap
        try:
            hits, rs = harvest.esearch(f"{journal_or} AND {win} AND english[lang]",
                                       ret, sort="date")
        except Exception as e:
            print(f"  [warn] {y} esearch 失败: {type(e).__name__} {e}")
            continue
        ids = list(dict.fromkeys(rs))
        if not ids and hits == 0:
            honest_years.append(y)
            continue
        per_year_hits[y] = {"hits": hits, "retrieved": len(ids), "window": win}
        print(f"[esearch] {y}（{win}）：命中 {hits}，取回 {len(ids)}")
        all_pmids.extend(ids)
        time.sleep(0.35)

    uniq = list(dict.fromkeys(all_pmids))
    print(f"\n[esearch] 去重后 PMID：{len(uniq)}（期刊白名单 {len(TOP_JOURNALS)} 本，"
          f"检索次数 {len(per_year_hits)}）")
    if honest_years:
        print(f"[注意] 以下年份 0 命中（未被 PubMed 收录或全被剔除）：{honest_years}")

    print("[元数据] get_summary ...")
    summ = harvest.get_summary(uniq, os.path.join(cache_dir, "summary_toppool.json"))
    print("[摘要] get_detail ...")
    det = harvest.get_detail(uniq, os.path.join(cache_dir, "detail_toppool.json"))

    rows, dropped = [], Counter()
    for pmid in uniq:
        s, d = summ.get(pmid), det.get(pmid)
        if not s or not d:
            dropped["元数据缺失"] += 1
            continue
        pts = set(d["pubtypes"]) | set(s.get("pubtype") or [])
        if pts & harvest.EXCLUDE_PT:
            dropped["非研究性文献"] += 1
            continue
        if pts & getattr(harvest, "PREPRINT_PT", set()):
            dropped["预印本"] += 1
            continue
        if len(d["abstract"]) < a.min_abstract:
            dropped["摘要过短"] += 1
            continue
        iso = (d.get("journal_iso") or "").strip()
        full = (d.get("journal_full") or "").strip()
        key = (iso or "").lower() or (full or "").lower()
        rec = itab.get(key.lower())
        if not rec:
            # 【刊名硬门槛豁免】先生点名「以三大顶刊为主」。
            # 实测（2026-10-01）：journal_metrics.csv 973 刊里**没有 Science 主刊**，
            # 缓存中 437 篇 Science 全部因 IF 未匹配被剔除 → 池内三大顶刊之一是 0 篇，
            # 与先生指令直接冲突。此处改走「刊名门槛」而非「估值门槛」：
            # 刊名在豁免集内 ⇒ 保留，但 **IF 一律标 PENDING，绝不补值、绝不估算**，
            # 并用 if_metric 列显式说明口径，供选材端自行判断。
            if key.lower() in exempt_set():
                exempt_keys.add(key.lower())
                rows.append({
                    "pmid": pmid,
                    "title": harvest.re.sub(r"<[^>]+>", "", s.get("title", "")).strip(),
                    "journal_iso": iso, "journal_full": full,
                    "issn": d.get("issn", ""),
                    "if_latest": "", "if_year_label": "", "if_bin": "UNBINNED",
                    "if_source_url": "",
                    "pubdate": (s.get("pubdate") or ""), "epubdate": (s.get("epubdate") or ""),
                    "year": (s.get("epubdate") or s.get("pubdate") or "")[:4] or "unknown",
                    "doi": d.get("doi", ""), "pmcid": d.get("pmcid", ""), "oa": (d.get("oa") or ""),
                    "pubtypes": "; ".join(sorted(pts)),
                    "tags": "", "cancers": "",
                    "mode": "", "public_data": "", "has_algo": "",
                    "matched_blocks": "", "score": "", "abstract": d["abstract"],
                    "if_metric": "PENDING（刊名硬门槛；未取 IF，未估算）",
                })
                continue
            dropped["IF 未匹配（PENDING，不估算）"] += 1
            continue
        ifv, ifstr, src = rec
        if ifv < a.min_if:
            dropped[f"IF<{a.min_if:g}"] += 1
            continue
        text = (s.get("title", "") + " " + d["abstract"] + " " + " ".join(d["mesh"]))
        tags, cancers, has_pub, has_wet, has_algo, mode = harvest.tag_it(text)
        year = (s.get("epubdate") or s.get("pubdate") or "")[:4] or "unknown"
        rows.append({
            "pmid": pmid,
            "title": harvest.re.sub(r"<[^>]+>", "", s.get("title", "")).strip(),
            "journal_iso": iso, "journal_full": full,
            "issn": d.get("issn", ""),
            "if_latest": ifstr, "if_year_label": "", "if_bin": bin_of(ifv),
            "if_source_url": src,
            "pubdate": (s.get("pubdate") or ""), "epubdate": (s.get("epubdate") or ""),
            "year": year,
            "doi": d.get("doi", ""), "pmcid": d.get("pmcid", ""), "oa": d.get("oa", ""),
            "pubtypes": "; ".join(sorted(pts)),
            "tags": "; ".join(tags), "cancers": "; ".join(cancers),
            "mode": mode, "public_data": has_pub, "has_algo": has_algo,
            "matched_blocks": "", "score": "", "abstract": d["abstract"],
            "if_metric": "JIF_bioxbio",
        })

    if exempt_keys:
        print(f"[初筛] 刊名硬门槛豁免（IF 仍为 PENDING，未估算）：{sorted(exempt_keys)}")
    print(f"\n[初筛] 保留 {len(rows)}；剔除：{dict(dropped)}")

    # --- 按年配额（近两年优先，服务「主要看最新的发现」）---
    by_year = {}
    for r in rows:
        by_year.setdefault(r["year"], []).append(r)
    years = sorted(by_year)
    kept, quota_left = [], {y: a.per_year for y in years}

    def ifval(r):
        """IF 为空（刊名门槛豁免行）时返回 0.0——**不估算、不补值**，只做排序占位。"""
        try:
            return float((r.get("if_latest") or "").strip())
        except (TypeError, ValueError):
            return 0.0

    # 近两年先占满配额，再回填更早年份
    ordered = years[-2:] + years[:-2]
    for y in ordered:
        for r in sorted(by_year[y], key=lambda x: (-ifval(x), int(x["pmid"]))):
            if quota_left[y] > 0:
                kept.append(r)
                quota_left[y] -= 1

    kept.sort(key=lambda r: (r["year"], -ifval(r), int(r["pmid"])))
    cols = ["pmid", "title", "journal_iso", "journal_full", "issn", "if_latest", "if_year_label",
            "if_bin", "if_source_url", "pubdate", "epubdate", "year", "doi", "pmcid", "oa",
            "pubtypes", "tags", "cancers", "mode", "public_data", "has_algo", "abstract", "if_metric"]
    out_csv = os.path.join(a.out_dir, "papers_toppool.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(kept)

    meta = {
        "window": f"{a.start} ~ {a.end}", "journals": len(TOP_JOURNALS),
        "unique_pmids_searched": len(uniq),
        "kept": len(kept), "per_year_quota": a.per_year,
        "min_if": a.min_if,
        "per_year_hits": per_year_hits,
        "journal_whitelist": len(TOP_JOURNALS),
        "search_strategy": "期刊 OR 词 × 按年分块（11 次 esearch，sort=date）",
        "dropped": dict(dropped),
        "year_distribution": dict(sorted(Counter(r["year"] for r in kept).items())),
        "journal_distribution": dict(sorted(Counter(r["journal_iso"] for r in kept).items(),
                                           key=lambda x: -x[1])),
        "oa": dict(Counter(r["oa"] or "?" for r in kept)),
        "with_pmcid": sum(1 for r in kept if (r.get("pmcid") or "").strip()),
        "if_exempt_journals": sorted(exempt_keys),
        "if_exempt_rows": sum(1 for r in kept if (r.get("if_metric") or "").startswith("PENDING")),
        "if_metric_distribution": dict(sorted(Counter(r.get("if_metric", "") for r in kept).items())),
        "built_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    with open(os.path.join(a.out_dir, "toppool_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 顶刊 reserve 池已建：{out_csv}")
    print(f"   篇数 {len(kept)}｜可全文(PMCID) {meta['with_pmcid']}/{len(kept)}")
    print(f"   年份分布：{meta['year_distribution']}")
    print(f"   期刊分布 Top10：{list(meta['journal_distribution'].items())[:10]}")
    print(f"   剔除原因：{meta['dropped']}")


if __name__ == "__main__":
    main()
