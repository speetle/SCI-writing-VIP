#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
journal_if.py — 期刊影响因子本地指标表构建 / 增量更新工具

数据来源（可溯源）：
  bioxbio.com  (https://www.bioxbio.com/journal/<SLUG>)
  SLUG 规则：PubMed 的 ISO 期刊缩写 → 全部大写、非字母数字替换为 "-"
      例: "Brief Bioinform" → BRIEF-BIOINFORM ; "Nucleic Acids Res" → NUCLEIC-ACIDS-RES
  抓取策略：ISO 缩写 slug → 全称 slug，逐个尝试；**每个候选页都必须通过「页面归属校验」
  （<title> 中的期刊名须与请求期刊一致）才允许写入**。

  ⚠️ 历史缺陷（2026-09-21 发现并修复）：旧版用
  `https://www.bioxbio.com/search?q=<full name>` 取首个 /journal/ 链接作兜底。
  该站搜索页由前端 JS/Google CSE 渲染，服务端返回的是**静态热门列表**（首条恒为 PLOS-ONE）。
  于是所有 slug 抓取失败的期刊都被静默写入 PLOS ONE 的 IF（2.8）与 PLOS ONE 的 URL，
  且 status 仍为 OK——共污染 340/632 行、影响 290/520 篇入选文献的 IF 分层。
  修复要点：(1) 删除该兜底；(2) 加入重试（站点 SSL 抖动频繁）；
  (3) 强制页面归属校验，校验不过一律 PENDING，绝不写入任何数值。

输出：journal_metrics.csv
  journal_iso,journal_full,if_latest,if_year_label,if_source_url,fetch_date,status

设计原则（红线）：
  - 只写入实际抓取到的数值；抓不到就写 status=PENDING，绝不猜、绝不填默认值。
  - 每次更新都记录 fetch_date 与来源 URL，保证任何一处 IF 都可回溯。

用法：
  python3 journal_if.py --journals "Nat Commun,SCI REP,PLoS One" --out metrics.csv
  python3 journal_if.py --from-csv papers_master.csv --col journal_iso --out metrics.csv
  python3 journal_if.py --from-csv papers_master.csv --out metrics.csv --refresh
"""
import argparse
import csv
import html
import os
import re
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import date

UA = {"User-Agent": ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                     "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36")}
BASE = "https://www.bioxbio.com"
FIELDS = ["journal_iso", "journal_full", "if_latest", "if_year_label",
          "if_source_url", "fetch_date", "status"]


def http_get(url, timeout=25, retries=3, backoff=1.5):
    """带重试的 GET，失败抛异常。

    bioxbio 抖动明显（实测 SSL handshake timeout），单次失败不足以判定
    「期刊不在库中」，须重试后再标 PENDING。
    但 **HTTP 404 是确定性结果**（该 slug 不在库中），重试无意义、纯浪费时间，
    直接抛出交由上层尝试下一个候选 slug。
    """
    last = None
    for i in range(retries):
        try:
            req = urllib.request.Request(url, headers=UA)
            return urllib.request.urlopen(req, timeout=timeout).read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:          # noqa: PERF203
            if e.code == 404:                        # 确定性缺失，不重试
                raise
            last = e
        except Exception as e:                       # noqa: BLE001
            last = e
        if i < retries - 1:
            time.sleep(backoff * (i + 1))
    raise last


def slugify(iso_abbrev):
    s = re.sub(r"[^0-9A-Za-z]+", "-", iso_abbrev.strip()).strip("-")
    return s.upper()


def parse_latest_if(html_text):
    """返回 (year_label, if_value)；解析失败返回 None。取表中最新年份行。"""
    for row in re.findall(r"<tr>(.*?)</tr>", html_text, flags=re.S):
        cells = [html.unescape(re.sub("<[^>]+>", "", c)).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, flags=re.S)]
        if len(cells) >= 2 and re.match(r"^\d{4}", cells[0]) and re.match(r"^[\d.]+$", cells[1]):
            return cells[0], cells[1]
    return None


def _norm_tokens(s):
    """标准化为比较用词元（去括号内容、去标点、转小写）。"""
    s = re.sub(r"\([^)]*\)", " ", s or "")
    s = re.sub(r"[^0-9A-Za-z]+", " ", s).strip().lower()
    return [t for t in s.split() if t]


def page_journal_name(html_text):
    """从 <title> 提取期刊名（截掉 'Impact Factor IF ...' 之后的部分）。"""
    m = re.search(r"<title>(.*?)</title>", html_text, flags=re.S)
    if not m:
        return ""
    return re.split(r"\s+Impact\s+Factor", html.unescape(m.group(1)).strip(),
                    flags=re.I)[0].strip()


def title_matches(iso, full_name, page_name):
    """校验页面确属所请求的期刊。

    判据：首词前缀一致 且 ISO 词元多数能在页面标题中找到词首匹配。
    用于拦截历史缺陷（兜底页恒为 PLOS ONE ⇒ 首词 plos ≠ front/target/...）。
    """
    pt = _norm_tokens(page_name)
    if not pt:
        return False
    for cand in (iso, full_name):
        ct = _norm_tokens(cand)
        if not ct or ct[0][:4] != pt[0][:4]:
            continue
        hit = sum(1 for c in ct if any(p.startswith(c[:4]) for p in pt))
        if hit / len(ct) >= 0.6:
            return True
    return False


def candidate_slugs(iso, full_name):
    """候选 slug 序列（逐个尝试，全部经页面归属校验）。

    1) ISO 缩写          "Nucleic Acids Res"  → NUCLEIC-ACIDS-RES
    2) ISO 去括号        "Medicine (Baltimore)" → MEDICINE
    3) 全称              "Frontiers in Immunology" → FRONTIERS-IN-IMMUNOLOGY
    4) 全称去括号

    已删除旧版「站内搜索兜底」——该站搜索页服务端返回静态热门列表，
    取首条链接会把无关期刊的 IF 静默写入（红线：不编造数据）。
    """
    out = []
    for raw in (iso, full_name):
        if not raw:
            continue
        for variant in (raw, re.sub(r"\([^)]*\)", " ", raw)):
            s = slugify(variant)
            if s and s not in out:
                out.append(s)
    return out


def fetch_one(iso, full_name="", verbose=True):
    """返回 dict（一行 journal_metrics）。

    抓不到、或抓到但**页面归属校验不通过**，一律 status=PENDING、if_latest 留空。
    绝不写入任何未经确证的数值。
    """
    today = date.today().isoformat()
    rec = {"journal_iso": iso, "journal_full": full_name or iso, "if_latest": "",
           "if_year_label": "", "if_source_url": "", "fetch_date": today, "status": "PENDING"}
    for slug in candidate_slugs(iso, full_name):
        url = f"{BASE}/journal/{urllib.parse.quote(slug)}"
        try:
            text = http_get(url)
        except Exception:
            continue
        parsed = parse_latest_if(text)
        if not parsed:
            continue
        if not title_matches(iso, full_name, page_journal_name(text)):
            if verbose:
                print(f"  [MISM] {iso:<28} 页面归属不符"
                      f"（{page_journal_name(text)[:30]}）→ 拒绝写入")
            continue
        rec["if_year_label"], rec["if_latest"] = parsed
        rec["if_source_url"] = url
        rec["status"] = "OK"
        break
    if verbose:
        print(f"  [{'OK ' if rec['status']=='OK' else 'PEND'}] {iso:<28} "
              f"IF={rec['if_latest'] or '-'} ({rec['if_year_label'] or '-'})")
    return rec


def if_bin(v):
    """IF 区间分箱（用户指定口径）。空值返回 UNBINNED。"""
    if v in (None, "", "-"):
        return "UNBINNED"
    try:
        x = float(v)
    except ValueError:
        return "UNBINNED"
    if x < 1:
        return "<1"
    if x < 3:
        return "1-3"
    if x < 5:
        return "3-5"
    if x < 10:
        return "5-10"
    return ">10"


def load_existing(path):
    if not os.path.exists(path):
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        return {(r.get("journal_iso") or "").strip(): r for r in csv.DictReader(f)}


def save(path, rows):
    rows = sorted(rows.values(), key=lambda r: (r["status"] != "OK", r["journal_iso"].lower()))
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in FIELDS})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--journals", default="", help="逗号分隔的 ISO 缩写")
    ap.add_argument("--from-csv", default="", help="从已有 CSV 抽取期刊缩写")
    ap.add_argument("--col", default="journal_iso")
    ap.add_argument("--full-col", default="journal_full", help="同 CSV 中的全称列（用于兜底搜索）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--refresh", action="store_true", help="忽略缓存，全部重抓")
    ap.add_argument("--delay", type=float, default=0.6, help="每次请求间隔秒（礼貌抓取）")
    a = ap.parse_args()

    names, fulls = [], {}
    if a.journals:
        names += [x.strip() for x in a.journals.split(",") if x.strip()]
    if a.from_csv:
        with open(a.from_csv, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                n = (r.get(a.col) or "").strip()
                if n:
                    names.append(n)
                    if r.get(a.full_col):
                        fulls.setdefault(n, r[a.full_col].strip())

    seen, ordered = set(), []
    for n in names:
        if n.lower() not in seen:
            seen.add(n.lower())
            ordered.append(n)

    cache = {} if a.refresh else load_existing(a.out)
    todo = [n for n in ordered if n.lower() not in {k.lower() for k in cache}]
    print(f"[journal_if] 期刊总数 {len(ordered)}，已缓存 {len(ordered)-len(todo)}，待抓 {len(todo)}")

    for i, n in enumerate(todo, 1):
        print(f"({i}/{len(todo)})", end=" ")
        rec = fetch_one(n, fulls.get(n, ""))
        cache[rec["journal_iso"]] = rec
        if i % 25 == 0:
            save(a.out, cache)
        time.sleep(a.delay)
    save(a.out, cache)

    ok = [r for r in cache.values() if r["status"] == "OK"]
    dist = {}
    for r in cache.values():
        b = if_bin(r["if_latest"])
        dist[b] = dist.get(b, 0) + 1
    print(f"[journal_if] 完成：{len(ok)}/{len(cache)} 命中；区间分布 {dict(sorted(dist.items()))}")
    print(f"[journal_if] 已写入 {a.out}")


if __name__ == "__main__":
    sys.exit(main())
