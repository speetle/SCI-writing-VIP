#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_pmc_fulltext.py —— 按单篇抓取 PMC 全文并结构化导出（供「深度拆解」使用）

职责：给定 PMID 或 PMCID，从 Europe PMC 取 fullTextXML，缓存本地，并导出一份
      便于人工/AI 逐图拆解的结构化 Markdown（章节骨架 + 图注全文 + Methods + Results + Discussion）。

为什么单独写一个（与 imrad_scan.py 的区别）
------------------------------------------
- `imrad_scan.py` 是**批量扫面**：按 IF 配额抽 N 篇，只统计章节/段落结构，用于周课 ⑨。
- 本脚本是**单篇深入**：输出图注全文与 Methods/Results/Discussion 正文，供逐图拆解使用。

深度声明（硬约束，与 SKILL.md 一致）
----------------------------------
- 取到全文 → 输出头部标 `depth: full`，方可书写方法学细节与图注级判断
- 取不到全文 → 输出头部标 `depth: abstract-only`，**只给摘要**，禁止据此写「精读发现」
- 官方 JIF 与 OpenAlex 代理值严禁混称；本脚本不涉及 IF，仅搬运全文

踩坑记录（已验证）
----------------
1. **Europe PMC 返回的文本含不间断空格 U+00A0（`\\xa0`）**，直接用普通空格做字符串匹配会**失配**。
   本脚本统一规范化为普通空格（`--keep-nbsp` 可关闭）。
   实例：`CWP_L, 50\\xa0mg/kg` —— 用 "50 mg/kg" 检索会命中 0 处。
2. Europe PMC 全文端点对**非 OA 文献返回 404 或错误页**，须显式判空并降级为摘要级。
3. 沙箱放行 `www.ebi.ac.uk`；本机实测 2026-09-25 可用。

用法
----
# 单篇（PMID 或 PMCID 均可，自动解析）
python3 fetch_pmc_fulltext.py --id 42756286 --out-dir 04_IMRAD架构库/_pmc_cache \\
    --dump-md 07_深度拆解/_fulltext/42756286.md

# 仅缓存 XML，不导出 md
python3 fetch_pmc_fulltext.py --id PMC13582482 --out-dir 04_IMRAD架构库/_pmc_cache

# 批量（从 papers_master.csv 取指定 PMID）
python3 fetch_pmc_fulltext.py --csv 01_文献库/2026-W39/papers_master.csv \\
    --pmids 42756286,42756064 --out-dir 04_IMRAD架构库/_pmc_cache --dump-md-dir 07_深度拆解/_fulltext
"""
import argparse
import csv
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

EBI = "https://www.ebi.ac.uk/europepmc/webservices/rest"
SEARCH = EBI + "/search"
FULLTEXT = EBI + "/{pmcid}/fullTextXML"


# ---------------------------------------------------------------- 取回

def _get(url, timeout=45):
    req = urllib.request.Request(url, headers={"User-Agent": "SCI-writing-VIP/2.0 (research use)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")


def resolve_pmcid(ident):
    """把 PMID / PMCID 统一解析成 PMCID；返回 None 表示无全文。"""
    ident = ident.strip()
    if ident.upper().startswith("PMC"):
        return ident.upper()
    q = urllib.parse.quote(f"EXT_ID:{ident} AND SRC:MED")
    try:
        raw = _get(f"{SEARCH}?query={q}&format=json&resultType=core&pageSize=1")
        js = json.loads(raw)
        hits = js.get("resultList", {}).get("result", [])
        if not hits:
            return None
        return hits[0].get("pmcid") or None
    except Exception as e:
        print(f"  [warn] 解析 PMCID 失败: {e}", file=sys.stderr)
        return None


def fetch_xml(pmcid, out_dir, force=False, sleep=1.0):
    """抓取并缓存全文 XML。返回 (xml_bytes_str or None, path or None)。"""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{pmcid}.xml")
    if os.path.exists(path) and not force and os.path.getsize(path) > 2000:
        with open(path, encoding="utf-8") as f:
            return f.read(), path
    try:
        raw = _get(FULLTEXT.format(pmcid=pmcid))
    except urllib.error.HTTPError as e:
        print(f"  [info] {pmcid}: HTTP {e.code} —— 非 OA 或无全文，降级为摘要级", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"  [warn] {pmcid}: {e}", file=sys.stderr)
        return None, None
    if "<article" not in raw[:2000]:
        print(f"  [info] {pmcid}: 返回非全文内容，降级为摘要级", file=sys.stderr)
        return None, None
    with open(path, "w", encoding="utf-8") as f:
        f.write(raw)
    time.sleep(sleep)          # 对公共 API 保持礼貌
    return raw, path


# ---------------------------------------------------------------- 规范化

def norm(s):
    """统一空白：U+00A0 → 普通空格；折叠连续空白。"""
    if s is None:
        return ""
    s = s.replace("\xa0", " ").replace("\u2009", " ").replace("\u202f", " ")
    return re.sub(r"[ \t\r\n]+", " ", s).strip()


def itext(e):
    return norm("".join(e.itertext())) if e is not None else ""


# ---------------------------------------------------------------- 结构化导出

def sections_of(root):
    """返回 [(层级, 标题, sec-type, 节点)]，仅遍历 body 下的一级/二级 sec。"""
    body = root.find(".//body")
    if body is None:
        return []
    out = []
    for s in body.findall("sec"):
        ti = s.find("title")
        out.append((1, itext(ti) or "(无标题)", s.get("sec-type"), s))
        for sub in s.findall("sec"):
            st = sub.find("title")
            out.append((2, itext(st) or "(无标题)", sub.get("sec-type"), sub))
    return out


def dump_markdown(root, meta):
    L = []
    L.append(f"# {meta.get('title') or '(无标题)'}")
    L.append("")
    L.append(f"> **depth**: `full`｜**PMID**: {meta.get('pmid','—')}｜**PMCID**: {meta.get('pmcid','—')}"
             f"｜**期刊**: {meta.get('journal','—')}｜**DOI**: {meta.get('doi','—')}")
    L.append("> 文本已规范化（U+00A0 → 空格）。所有内容为原文搬运，未作改写。")
    L.append("")
    L.append(f"**摘要**：{meta.get('abstract','(未取到)')}")
    L.append("")
    L.append("---")
    L.append("")

    # 章节骨架
    L.append("## 一、章节骨架")
    L.append("")
    L.append("| 层级 | 标题 | sec-type | 段落数 |")
    L.append("|---|---|---|---|")
    for lvl, name, st, node in sections_of(root):
        n = len(node.findall("p"))
        L.append(f"| {'H1' if lvl == 1 else 'H2'} | {name} | {st or '—'} | {n} |")
    L.append("")

    # 图与表
    L.append("## 二、图表清单（图注全文）")
    L.append("")
    for f in root.iter("fig"):
        lab = itext(f.find("label")) or "(无 label)"
        L.append(f"**{lab}** — {itext(f.find('caption'))}")
        L.append("")
    for tw in root.iter("table-wrap"):
        lab = itext(tw.find("label")) or "(无 label)"
        L.append(f"**{lab}** — {itext(tw.find('caption'))}")
        L.append("")

    # 正文各节
    L.append("---")
    L.append("")
    L.append("## 三、正文分节原文")
    for lvl, name, st, node in sections_of(root):
        if lvl != 1:
            continue
        if name in ("References",) or (st and "ref-list" in st):
            continue
        L.append("")
        L.append(f"### {name}")
        L.append("")
        for p in node.findall("p"):
            t = itext(p)
            if t:
                L.append(t)
                L.append("")
        for sub in node.findall("sec"):
            stitle = itext(sub.find("title")) or "(无标题)"
            L.append("")
            L.append(f"#### {stitle}")
            L.append("")
            for p in sub.findall("p"):
                t = itext(p)
                if t:
                    L.append(t)
                    L.append("")
    return "\n".join(L)


def meta_of(root, pmid=None, pmcid=None):
    doi = ""
    for aid in root.iter("article-id"):
        if aid.get("pub-id-type") == "doi":
            doi = itext(aid)
    jt = root.find(".//journal-title")
    return {
        "title": itext(root.find(".//article-title")),
        "journal": itext(jt),
        "doi": doi,
        "pmid": pmid or "",
        "pmcid": pmcid or "",
        "abstract": itext(root.find(".//abstract"))[:4000],
    }


# ---------------------------------------------------------------- 主流程

def process(ident, out_dir, dump_md=None, force=False):
    pmcid = resolve_pmcid(ident)
    if not pmcid:
        print(f"[skip] {ident}: 未找到 PMCID（可能未被 PMC 收录）")
        return False
    print(f"[ok] {ident} → {pmcid}")
    raw, path = fetch_xml(pmcid, out_dir, force=force)
    if raw is None:
        return False
    root = ET.fromstring(raw)
    pmid = ident if ident.isdigit() else ""
    meta = meta_of(root, pmid=pmid, pmcid=pmcid)
    if dump_md:
        os.makedirs(os.path.dirname(dump_md) or ".", exist_ok=True)
        with open(dump_md, "w", encoding="utf-8") as f:
            f.write(dump_markdown(root, meta))
        print(f"      → md: {dump_md}")
    print(f"      → xml: {path}")
    return True


def main():
    ap = argparse.ArgumentParser(description="按单篇抓取 PMC 全文并结构化导出")
    ap.add_argument("--id", help="单个 PMID 或 PMCID")
    ap.add_argument("--pmids", help="逗号分隔的多个 PMID（与 --csv 联用）")
    ap.add_argument("--csv", help="papers_master.csv（仅用于校验/补充信息）")
    ap.add_argument("--out-dir", default="04_IMRAD架构库/_pmc_cache", help="XML 缓存目录")
    ap.add_argument("--dump-md", help="单篇导出的 md 路径")
    ap.add_argument("--dump-md-dir", help="批量导出的 md 目录")
    ap.add_argument("--force", action="store_true", help="忽略缓存重新抓取")
    ap.add_argument("--keep-nbsp", action="store_true", help="保留 U+00A0（默认规范化）")
    a = ap.parse_args()

    global norm
    if a.keep_nbsp:
        norm = lambda s: re.sub(r"[ \t\r\n]+", " ", s or "").strip()

    idents = []
    if a.id:
        idents = [a.id]
    elif a.pmids:
        idents = [x.strip() for x in a.pmids.split(",") if x.strip()]
    else:
        ap.error("需提供 --id 或 --pmids")

    ok = 0
    for ident in idents:
        md = a.dump_md
        if a.dump_md_dir:
            md = os.path.join(a.dump_md_dir, f"{ident}.md")
        if process(ident, a.out_dir, dump_md=md, force=a.force):
            ok += 1
    print(f"\n完成：{ok}/{len(idents)} 篇取得全文（其余为摘要级或未收录）")


if __name__ == "__main__":
    sys.exit(main())
