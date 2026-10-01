#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
count_markers.py — 「句首标记词 / 让步对比结构 / 黑名单字面计数」统一口径测量器

为什么需要这个脚本（2026-09-28 / W40 D01 立）
------------------------------------------------
W39 的「句首标记词句占比」基线（真人五日合并 8.85%）由一个**一次性的 /tmp 脚本**产出，
其**词表、分句口径、过滤条件、脚本名四项口径中，只有脚本名被记录**，其余三项丢失。
后果：任何新稿都无法用同一把尺子复测——基线不可复现，属 [ERR-2026W39-18]/[ERR-2026W39-23] 同族风险。

本脚本把该指标固化为**可复用、带完整四项口径声明**的工具，其输出可直接进入范式库与账本。

口径四项（本脚本输出的每一个数字都受此约束）
------------------------------------------------
  ① 词表     = 见下方 INITIAL_MARKERS / CONCESSIVE / 以及 --literal 传入的字面串
  ② 分句口径 = count_connectors.split_sentences()（与连接词密度同源，保证可比）
  ③ 过滤条件 = 无（正文标题行请自行剔除后再传入；本脚本对 `#` 开头行会提示但不过滤）
  ④ 脚本     = count_markers.py

输出三类指标
------------------------------------------------
  A. 句首标记词句占比  —— 句子的首个实词 token 属 INITIAL_MARKERS 即计入
  B. 让步/对比结构密度 —— although / whereas / despite / while / though（全句字面计数）
  C. 任意字面串计数     —— --literal "a|b|c"（用于黑名单逐词复核；计数为**字面出现次数**）

用法
------------------------------------------------
  python3 count_markers.py --corpus corpus.txt
  python3 count_markers.py --corpus corpus.txt --json out.json \
      --literal "is of great significance|clearly demonstrate|It should be noted"
  python3 count_markers.py --corpus mine.md --strip-appendix      # 剔除 <!-- APPENDIX --> 之后内容
"""
import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from count_connectors import split_sentences  # noqa: E402  分句口径唯一真源

# ① 词表：句首"话语标记词"（段间/句间推进外包的典型载体）
INITIAL_MARKERS = [
    # 追加-递进
    "however", "moreover", "furthermore", "additionally", "in addition",
    "besides", "also", "similarly", "likewise", "conversely",
    # 转折-对比
    "in contrast", "by contrast", "instead", "alternatively", "conversely",
    "nonetheless", "nevertheless", "still", "yet", "that said",
    # 因果-推论
    "thus", "therefore", "consequently", "accordingly", "hence", "as such",
    # 汇总-收束
    "overall", "collectively", "taken together", "in summary", "in conclusion",
    # 序列-强调
    "finally", "notably", "importantly", "specifically", "in particular",
    "meanwhile", "subsequently", "indeed",
]
# 去重但保序
_seen = set()
INITIAL_MARKERS = [m for m in INITIAL_MARKERS if not (m in _seen or _seen.add(m))]

# ② 让步/对比结构（C-25 判据）
CONCESSIVE = ["although", "whereas", "despite", "while", "though"]

# ⚠️ 2026-09-28 口径复原说明（**必读**）
# W39 的「句首标记词句占比 8.85%」由一次性 `/tmp/headconn_file.py` 产出，词表未记录。
# W40 D01 用上表 38 项复算 W39 七日语料，得 **7.27%**（低于旧报 ≈1.6pp）。
# 逐项反解后确认差异**完全来自词表**：旧表额外包含 `further` 与让步连词（`although` /
# `whereas` / `despite` / `while` / `though`）。
# 复原检验（脚本实测，分母均为 5 889 句）：
#     38 项              → 428/5889 = 7.27%
#     +further           → 452/5889 = 7.68%
#     +further+让步 5 词  → 526/5889 = 8.93%  ← 对应旧报 8.85%（差 0.08pp，D06 单日 68/795 对旧报 69/795）
# 处置：**不废旧带**。定义双口径，两者均由本脚本一次输出、严禁混称：
#   口径 A（**判据口径**，延续 W39 的 7%–11% 带）= 38 项 + `further` + 让步连词
#   口径 B（窄口径，纯话语标记词，用于分析"推进外包"）= 38 项
WIDE_EXTRA = ["further"] + CONCESSIVE

_MARKER_RE = re.compile(
    r"^(?:" + "|".join(re.escape(m) for m in sorted(INITIAL_MARKERS, key=len, reverse=True)) + r")\b",
    re.I)


def count_markers(corpus_text):
    sents = split_sentences(corpus_text)
    n = len(sents)
    if n == 0:
        return None
    initial_hits = []
    for s in sents:
        s2 = s.strip().lstrip("([\"'").strip()
        if _MARKER_RE.match(s2):
            initial_hits.append(s2[:60])

    conc = {}
    for w in CONCESSIVE:
        conc[w] = len(re.findall(r"\b" + w + r"\b", corpus_text, re.I))
    conc_total = sum(conc.values())

    # 口径 A（判据口径）＝ 窄口径 + WIDE_EXTRA
    wide_markers = INITIAL_MARKERS + WIDE_EXTRA
    _re_wide = re.compile(
        r"^(?:" + "|".join(re.escape(m) for m in sorted(wide_markers, key=len, reverse=True)) + r")\b", re.I)
    wide_hits = [s for s in sents
                 if _re_wide.match(s.strip().lstrip("([\"'").strip())]

    return {
        "sentences": n,
        "initial_marker_sentences": len(initial_hits),
        "initial_marker_share_pct": round(100.0 * len(initial_hits) / n, 2),
        "initial_marker_sentences_WIDE": len(wide_hits),
        "initial_marker_share_pct_WIDE": round(100.0 * len(wide_hits) / n, 2),
        "concessive": conc,
        "concessive_total": conc_total,
        "concessive_per_100sent": round(100.0 * conc_total / n, 2),
        "initial_examples": initial_hits[:12],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="语料文本（每行一句；脚本内再统一分句）")
    ap.add_argument("--json", default="", help="可选：写出 json")
    ap.add_argument("--literal", default="",
                    help="可选：`|` 分隔的字面串，逐项统计**字面出现次数**（黑名单复核用）")
    ap.add_argument("--strip-appendix", action="store_true",
                    help="剔除 `<!-- APPENDIX -->` 及其后全部内容（稿件机检用）")
    a = ap.parse_args()

    text = open(a.corpus, encoding="utf-8").read()
    if a.strip_appendix and "<!-- APPENDIX -->" in text:
        text = text.split("<!-- APPENDIX -->", 1)[0]

    r = count_markers(text)
    if r is None:
        print("[count_markers] 语料为空")
        return

    print("=" * 66)
    print(f"[count_markers] 语料 {a.corpus}")
    print(f"  口径四项：① 词表=INITIAL_MARKERS({len(INITIAL_MARKERS)} 项)/CONCESSIVE(5 项)/--literal "
          f"｜② 分句=count_connectors.split_sentences() ｜③ 过滤={'剔除 APPENDIX' if a.strip_appendix else '无'} "
          f"｜④ 脚本=count_markers.py")
    print(f"  句数 {r['sentences']}")
    print("-" * 66)
    print(f"  【A】句首标记词句占比（**双口径，严禁混称**）")
    print(f"       口径 A（**判据口径**，含 further + 让步连词；延续 W39 的 7%–11% 带）："
          f"{r['initial_marker_sentences_WIDE']} / {r['sentences']} = {r['initial_marker_share_pct_WIDE']:.2f}%")
    print(f"       口径 B（窄口径，纯话语标记词，仅用于分析「推进外包」）："
          f"{r['initial_marker_sentences']} / {r['sentences']} = {r['initial_marker_share_pct']:.2f}%")
    print(f"       示例句首（窄口径）：")
    for e in r["initial_examples"]:
        print(f"         · {e}")
    print(f"  【B】让步/对比结构 合计 {r['concessive_total']} = {r['concessive_per_100sent']:.2f} / 百句")
    print("       " + "｜".join(f"{k} {v}" for k, v in r["concessive"].items()))
    if a.literal:
        print(f"  【C】字面串计数（口径：字面出现次数，非词元）：")
        for k in a.literal.split("|"):
            k = k.strip()
            if not k:
                continue
            c = len(re.findall(re.escape(k), text, re.I))
            d = round(100.0 * c / r["sentences"], 2)
            print(f"       {k:<34} {c:>4} 次  ({d:.2f} / 百句)")
        r["literal"] = {k.strip(): len(re.findall(re.escape(k.strip()), text, re.I))
                        for k in a.literal.split("|") if k.strip()}
    print("=" * 66)

    if a.json:
        json.dump(r, open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"[count_markers] JSON → {a.json}")


if __name__ == "__main__":
    main()
