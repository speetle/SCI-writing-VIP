#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ref_verify.py — 引用存在性与支撑度核查（AI 痕迹三步法第三步机检）

做三件事：
  1. 抽取稿件中的 PMID / DOI
  2. 用 PubMed E-utilities 核查是否真实存在，回填题名/期刊/年份
  3. 用引用句与原文（题名+摘要）的实词重叠度给一个**提示值**，标出需人工复核者

不做的事：不判定“原文是否支持该结论”。H2 类幻觉只能人工读原文，见
references/ai-trace-remediation.md 第三步。

用法：
  python3 ref_verify.py --manuscript 稿.md --out 引用核验.md
  python3 ref_verify.py --manuscript 稿.md --json --no-abstract   # 只查存在性
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

EUTILS = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
UA = "SCI-writing-VIP-ref-verify/1.0 (mailto:drmilo@gkd.edu.cn)"

PMID_RE = re.compile(r"PMID[:\s]*([0-9]{6,9})", re.I)
DOI_RE = re.compile(r"\b(10\.\d{4,9}/[^\s\)\]\}>;,、，。；\"]+)")

STOP = set("""
a an the and or but if then than that this these those of in on at to for from by with without
as is are was were be been being has have had do does did not no nor so such it its we our they their
here there however therefore moreover furthermore thus although whereas while because since
we found show shown suggests suggest indicate indicates may might could can would should
which who whom whose what when where why how all any both each few more most other some only
also than into over under between during after before above below up down out off again
study studies result results data group groups patient patients cell cells model models
""".split())


def norm_words(s):
    return [w for w in re.findall(r"[a-z][a-z0-9\-]{3,}", s.lower()) if w not in STOP]


def http_get(url, tries=3, timeout=30):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
            last = exc
            time.sleep(1.0 + i)
    raise RuntimeError("请求失败：%s" % last)


def esummary(pmids):
    url = "%s/esummary.fcgi?db=pubmed&retmode=json&id=%s" % (EUTILS, ",".join(pmids))
    raw = http_get(url)
    data = json.loads(raw.decode("utf-8", "replace"))
    out = {}
    for pid in pmids:
        rec = (data.get("result") or {}).get(pid)
        if not rec or rec.get("error"):
            out[pid] = None
            continue
        authors = [a.get("name", "") for a in (rec.get("authors") or [])][:3]
        out[pid] = {
            "title": (rec.get("title") or "").strip(),
            "journal": rec.get("source") or "",
            "year": (rec.get("pubdate") or "").split(" ")[0],
            "authors": authors,
            "pubtype": ", ".join(rec.get("pubtype") or []),
        }
    return out


def efetch_abstracts(pmids):
    """返回 {pmid: abstract_text}"""
    url = "%s/efetch.fcgi?db=pubmed&retmode=xml&id=%s" % (EUTILS, ",".join(pmids))
    raw = http_get(url, timeout=60)
    root = ET.fromstring(raw)
    out = {}
    for art in root.findall(".//PubmedArticle"):
        pid = art.findtext(".//MedlineCitation/PMID")
        if not pid:
            continue
        parts = []
        for ab in art.findall(".//Article/Abstract/AbstractText"):
            label = ab.get("Label")
            txt = "".join(ab.itertext()).strip()
            parts.append(("%s: " % label if label else "") + txt)
        out[pid] = " ".join(parts)
    return out


def crossref_title(doi):
    try:
        url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="") + "?mailto=drmilo@gkd.edu.cn"
        raw = http_get(url, tries=1, timeout=20)
        d = json.loads(raw.decode("utf-8", "replace"))["message"]
        return (d.get("title") or [""])[0]
    except Exception:
        return ""


def extract_citations(text):
    """返回 [(kind, id, 引用句, 行号)]；同一 id 只保留首次出现的句子。"""
    lines = text.splitlines()
    seen = set()
    out = []
    for i, line in enumerate(lines, 1):
        for m in PMID_RE.finditer(line):
            pid = m.group(1)
            if ("pmid", pid) in seen:
                continue
            seen.add(("pmid", pid))
            out.append(("PMID", pid, sentence_around(line, m.start(), m.end()), i))
        for m in DOI_RE.finditer(line):
            doi = m.group(1).rstrip(".")
            if ("doi", doi.lower()) in seen:
                continue
            seen.add(("doi", doi.lower()))
            out.append(("DOI", doi, sentence_around(line, m.start(), m.end()), i))
    return out


def sentence_around(line, start, end):
    bounds = [0] + [m.end() for m in re.finditer(r"[.。!?；;]\s", line)] + [len(line)]
    lo = max([b for b in bounds if b <= start] or [0])
    hi = min([b for b in bounds if b >= end] or [len(line)])
    return line[lo:hi].strip()


def overlap(sent, ref_text):
    sw = norm_words(sent)
    if not sw:
        return 0.0, []
    rw = set(norm_words(ref_text))
    hit = [w for w in set(sw) if w in rw]
    return len(hit) / float(len(set(sw))), hit


def build_report(rows, src, missing_only=False):
    L = []
    add = L.append
    add("# 引用核验报告")
    add("")
    add("- 源文件：`%s`" % src)
    add("- 口径：存在性由 PubMed E-utilities 核；**支撑度重叠值只是提示，不是判定**（H2 必须人工读原文）")
    add("")
    n_ok = sum(1 for r in rows if r["exists"])
    n_bad = len(rows) - n_ok
    low = [r for r in rows if r["exists"] and r["overlap"] is not None and r["overlap"] < 0.15]
    add("| 指标 | 数 |")
    add("|---|---|")
    add("| 引用条目 | %d |" % len(rows))
    add("| 存在性通过 | %d |" % n_ok)
    add("| **查无此文** | **%d** |" % n_bad)
    add("| 重叠 <0.15（须人工核） | %d |" % len(low))
    add("")
    add("## 逐条")
    add("")
    add("| # | 类型 | 标识 | 存在 | 题名（截断） / 期刊·年 | 引用句 | 重叠 | 判定位 |")
    add("|---|---|---|---|---|---|---|---|")
    for i, r in enumerate(rows, 1):
        if missing_only and r["exists"]:
            continue
        title = (r["title"] or "—")
        if len(title) > 90:
            title = title[:87] + "..."
        meta = "%s · %s" % (r["journal"], r["year"]) if r["journal"] else ""
        sent = r["sentence"].replace("|", "/")
        if len(sent) > 110:
            sent = sent[:107] + "..."
        ov = "—" if r["overlap"] is None else "%.2f" % r["overlap"]
        verdict = "⬜ 待人工判" if r["exists"] else "❌ 删除或替换"
        add("| %d | %s | `%s` | %s | %s %s | %s | %s | %s |" % (
            i, r["kind"], r["id"], "✅" if r["exists"] else "**否**", title, meta, sent, ov, verdict))
    add("")
    add("## 人工判定须知")
    add("")
    add("| 重叠值 | 含义 | 动作 |")
    add("|---|---|---|")
    add("| ≥0.35 | 引用句与原文用词高度一致 | 仍须读摘要确认方向一致 |")
    add("| 0.15–0.35 | 一般 | 读摘要确认对象与条件 |")
    add("| <0.15 | 可能是转述、跨文献综合，或张冠李戴 | **必读原文**，判为不支持则删改 |")
    add("")
    add("判定四值：支持 / 部分支持 / 不支持 / 反向支持。反向支持改写成对比句即为加分项。")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="引用存在性与支撑度核查")
    ap.add_argument("--manuscript", required=True)
    ap.add_argument("--out")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-abstract", action="store_true", help="只查存在性，不算重叠")
    ap.add_argument("--missing-only", action="store_true", help="报告只列查无此文的条目")
    args = ap.parse_args()

    with open(args.manuscript, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()

    cits = extract_citations(text)
    if not cits:
        print("未在稿件中找到 PMID/DOI。若引用以作者-年份格式书写，请先补 PMID/DOI。")
        return 0

    pmids = [c[1] for c in cits if c[0] == "PMID"]
    meta = {}
    abstracts = {}
    if pmids:
        uniq = list(dict.fromkeys(pmids))
        for i in range(0, len(uniq), 100):
            meta.update(esummary(uniq[i:i + 100]))
            time.sleep(0.4)
        if not args.no_abstract:
            for i in range(0, len(uniq), 40):
                abstracts.update(efetch_abstracts(uniq[i:i + 40]))
                time.sleep(0.4)

    rows = []
    for kind, cid, sent, line in cits:
        if kind == "PMID":
            rec = meta.get(cid)
            if rec:
                ref_text = rec["title"] + " " + abstracts.get(cid, "")
                ov = None if args.no_abstract else overlap(sent, ref_text)[0]
                rows.append({"kind": kind, "id": cid, "exists": True, "title": rec["title"],
                             "journal": rec["journal"], "year": rec["year"], "sentence": sent,
                             "overlap": ov, "line": line})
            else:
                rows.append({"kind": kind, "id": cid, "exists": False, "title": "", "journal": "",
                             "year": "", "sentence": sent, "overlap": None, "line": line})
        else:
            title = "" if args.no_abstract else crossref_title(cid)
            rows.append({"kind": kind, "id": cid, "exists": bool(title), "title": title,
                         "journal": "Crossref", "year": "", "sentence": sent,
                         "overlap": None, "line": line})

    if args.json:
        print(json.dumps({"source": args.manuscript, "citations": rows}, ensure_ascii=False, indent=2))
        return 0

    report = build_report(rows, args.manuscript, args.missing_only)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        bad = sum(1 for r in rows if not r["exists"])
        print("WROTE %s | citations=%d | not_found=%d" % (args.out, len(rows), bad))
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
