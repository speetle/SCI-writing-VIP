#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
count_connectors.py — 连接词 / 衔接手段「字面字符串」实测计数器。

背景（红线）：[ERR-2026W39-18] 手写归纳把 `moreover` / `in addition` 误记为 0 次，
并把「低频合法词」升级为「绝对禁词」，导致修订反向失真。
本脚本为该类计数提供**唯一可信来源**：一律对语料做字面字符串统计（不依赖分词，无口径歧义）。

用法:
  python3 count_connectors.py --corpus <语料.txt> [--json <out.json>] [--min-ratio 0.5]
  python3 count_connectors.py --corpus mine.md --strip-appendix   # 交付类稿件必用

语料格式：`extract_language.py --dump-abstracts` 的输出（**一行一摘要**，行间有空行）。
计数口径：大小写不敏感的词边界匹配（\\b）；**句数按分句后计**，分句正则与
`style_compare.py::split_sentences` 保持一致（否则与机检指标的分母不可比）。

⚠️ 分母口径提示：本脚本的分句含「≥5 词」过滤，与 `extract_language.py` 报告的句数
（其口径为全量切分）**不同**，两者分母不可混用；跨文件引用时须注明是哪个口径。
"""
import argparse
import json
import re
import sys
from collections import OrderedDict

# 连接词表（与 03_语言范式库/B、D 两份文件保持同步）
CONNECTORS = OrderedDict([
    # 段首/句首型标记
    ("however", r"\bhowever\b"),
    ("moreover", r"\bmoreover\b"),
    ("furthermore", r"\bfurthermore\b"),
    ("in addition", r"\bin\s+addition\b"),
    ("additionally", r"\badditionally\b"),
    ("besides", r"\bbesides\b"),
    ("therefore", r"\btherefore\b"),
    ("thus", r"\bthus\b"),
    ("collectively", r"\bcollectively\b"),
    ("taken together", r"\btaken\s+together\b"),
    ("overall", r"\boverall\b"),
    ("subsequently", r"\bsubsequently\b"),
    ("notably", r"\bnotably\b"),
    # 句内对比型（本系统实测为真人的绝对主力）
    ("while", r"\bwhile\b"),
    ("whereas", r"\bwhereas\b"),
    ("but", r"\bbut\b"),
    ("yet", r"\byet\b"),
    ("although", r"\balthough\b"),
    ("though", r"\bthough\b"),
    # 低权重推进型
    ("also", r"\balso\b"),
    ("further", r"\bfurther\b"),
    ("in contrast", r"\bin\s+contrast\b"),
    ("by contrast", r"\bby\s+contrast\b"),
    ("conversely", r"\bconversely\b"),
])

# 句尾/句中挂载型衔接手段（零连接词）
ATTACHMENTS = OrderedDict([
    (", and", r",\s+and\b"),
    (", with", r",\s+with\b"),
    (", while", r",\s+while\b"),
    (", whereas", r",\s+whereas\b"),
    (", indicating", r",\s+indicating\b"),
    (", suggesting", r",\s+suggesting\b"),
    (", supporting", r",\s+supporting\b"),
    (", resulting in", r",\s+resulting\s+in\b"),
    (", highlighting", r",\s+highlighting\b"),
    (", consistent with", r",\s+consistent\s+with\b"),
    ("consistent with (any)", r"\bconsistent\s+with\b"),
    ("accompanied by", r"\baccompanied\s+by\b"),
])


def split_sentences(text):
    """与 style_compare.py 保持完全一致的分句口径。"""
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    return [p.strip() for p in parts if len(p.split()) >= 5]


def read_sentences(path, strip_appendix=False):
    """读入语料并分句。语料为「一行一摘要」，故先按行读、再逐行分句。

    strip_appendix=True 时，在 `<!-- APPENDIX -->` 处截断（与 style_compare.py /
    anti_ai_check.py / count_markers.py 的 `--strip-appendix` 口径一致）。
    立此参数的直接原因是 [ERR-2026W39-26]/[-04] 家族：附录自述文本会被计入正文口径，
    使连接词密度虚高（W40 D02 实测 44.44 vs 真值 23.5，虚高 1.9 倍）。
    """
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    if strip_appendix:
        raw = re.split(r"<!--\s*APPENDIX\s*-->", raw, maxsplit=1)[0]
    sents = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        sents.extend(split_sentences(line))
    return sents


def count(patterns, text_lower, total):
    out = {}
    for label, pat in patterns.items():
        n = len(re.findall(pat, text_lower, flags=re.IGNORECASE))
        out[label] = {"count": n, "per_100sent": round(n * 100.0 / total, 2) if total else 0.0}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--corpus", required=True, help="每行一句的语料 txt")
    ap.add_argument("--json", default=None, help="可选：写出 json")
    ap.add_argument("--min-ratio", type=float, default=0.5,
                    help="判定「低频合法词」的阈值（每百句），默认 0.5")
    ap.add_argument("--strip-appendix", action="store_true",
                    help="在 <!-- APPENDIX --> 处截断（对交付类稿件必用；防止附录自述污染正文口径）")
    args = ap.parse_args()

    sents = read_sentences(args.corpus, strip_appendix=args.strip_appendix)
    total = len(sents)
    if total == 0:
        print("[count_connectors] 语料为空", file=sys.stderr)
        return 1
    text_lower = "\n".join(sents).lower()

    # ---------- 口径 ①：官方口径（与 style_compare.py / extract_language.py 完全一致） ----------
    #     必须复用同一 CONNECTIVES 表，否则跨轮指标不可比。导入失败时降级为「不可用」而不静默替换。
    official = None
    official_words = []
    try:
        import os as _os
        import sys as _sys
        _sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))
        from extract_language import CONNECTIVES as _OFFICIAL  # type: ignore
        official_words = list(_OFFICIAL)
        official = {}
        for w in official_words:
            n = len(re.findall(r"\b" + re.escape(w) + r"\b", text_lower))
            official[w] = {"count": n,
                           "per_100sent": round(n * 100.0 / total, 2) if total else 0.0}
    except Exception as e:  # noqa: BLE001
        print(f"[count_connectors] ⚠️ 无法导入官方 CONNECTIVES（{e}）；"
              f"官方口径不可用，仅输出扩展口径。", file=sys.stderr)

    # ---------- 口径 ②：扩展口径（含 but / also / yet / further 等真人高频词） ----------
    conn = count(CONNECTORS, text_lower, total)
    attach = count(ATTACHMENTS, text_lower, total)

    ext_total = sum(v["count"] for v in conn.values())
    ext_density = round(ext_total * 100.0 / total, 2)

    if official is not None:
        off_total = sum(v["count"] for v in official.values())
        off_density = round(off_total * 100.0 / total, 2)
        off_types = sum(1 for v in official.values() if v["count"] > 0)
        # 不在官方表内的词（扩展表特有）
        extra_only = [w for w in CONNECTORS if w not in official_words]
    else:
        off_total = off_density = off_types = None
        extra_only = list(CONNECTORS)

    # 句内对比型占比（扩展口径内）
    inline_keys = ["while", "whereas", "but", "yet", "although", "though"]
    inline_total = sum(conn[k]["count"] for k in inline_keys)
    inline_share = round(inline_total * 100.0 / ext_total, 1) if ext_total else 0.0

    # 冒号句占比（本系统 A-31 / C-09 口径：句末标点切分的句子中含冒号）
    colon_sents = sum(1 for s in sents if ":" in s)

    payload = {
        "corpus": args.corpus,
        "sentence_total": total,
        "_口径声明": {
            "官方口径": "复用 extract_language.CONNECTIVES（43 词），与 style_compare.py 一致；"
                        "跨轮/跨日比较**只能**用此值",
            "扩展口径": "本脚本宽表（含 but/also/yet/further/subsequently 等真人高频词）；"
                        "仅用于观察趋势，**严禁**与官方口径互换表述",
        },
        "official": {
            "total": off_total,
            "density_per_100sent": off_density,
            "types": off_types,
            "words": official,
        },
        "extended": {
            "total": ext_total,
            "density_per_100sent": ext_density,
            "types": sum(1 for v in conn.values() if v["count"] > 0),
            "words": conn,
            "words_not_in_official_table": extra_only,
        },
        "inline_contrast_total": inline_total,
        "inline_contrast_share_pct": inline_share,
        "colon_sentence_count": colon_sents,
        "colon_sentence_share_pct": round(colon_sents * 100.0 / total, 1),
        "attachments": attach,
    }

    print("=" * 66)
    print(f"[count_connectors] 语料 {args.corpus}")
    print(f"  句数 {total}")
    print(f"  ① 官方口径（跨轮比较用此值）：合计 {off_total}｜密度 {off_density} / 百句｜种类 {off_types}")
    print(f"  ② 扩展口径（仅供参考，禁止混称）：合计 {ext_total}｜密度 {ext_density} / 百句")
    print(f"  句内对比型合计 {inline_total}（占扩展口径连接词 {inline_share}%）")
    print(f"  含冒号句 {colon_sents}（{payload['colon_sentence_share_pct']}%）")
    print("-" * 66)
    if official is not None:
        print("  官方表逐词（仅列命中 > 0）：")
        for label, v in sorted(official.items(), key=lambda kv: -kv[1]["count"]):
            if v["count"]:
                flag = "  ← 低频合法词（≥%.2f/百句，不得列为绝对禁词，见 D-13）" % args.min_ratio \
                    if v["per_100sent"] >= args.min_ratio else ""
                print(f"    {label:18s} {v['count']:5d}   {v['per_100sent']:7.2f}/百句{flag}")
    print("  扩展表特有词（不在官方表内，仅列命中 > 0）：")
    for label in extra_only:
        v = conn[label]
        if v["count"]:
            print(f"    {label:18s} {v['count']:5d}   {v['per_100sent']:7.2f}/百句")
    print("  挂载型手段（零连接词衔接，仅列命中 > 0）：")
    for label, v in sorted(attach.items(), key=lambda kv: -kv[1]["count"]):
        if v["count"]:
            print(f"    {label:18s} {v['count']:5d}   {v['per_100sent']:7.2f}/百句")
    print("=" * 66)

    if args.json:
        with open(args.json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)
        print(f"[count_connectors] JSON → {args.json}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
