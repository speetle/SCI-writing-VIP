#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""style_compare.py — 阶段5 差异诊断的量化层（样本A vs 样本B）

同一套文体指标，同时测量：
  - 样本 A：真人语料（当日 PubMed 摘要 / 选定范文全文）
  - 样本 B：我自己的训练稿

输出逐项差值与判定，把"有点 AI 感"这种空话变成可核对的数字。
判定阈值取自本系统的实测口径，**不是文献定论**，只作自检参考。

用法:
  python3 style_compare.py \
      --human 01_文献库/2026-W39/D01/_human_corpus.txt \
      --mine  05_仿写训练/2026-W39/D01/01_AI训练写作初稿.md \
      --out   05_仿写训练/2026-W39/D01/_style_compare.md
"""
import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from extract_language import CONNECTIVES, HEDGES, BOOSTERS, AI_TEMPLATES, style_stats  # noqa: E402


def read_text(p):
    """提取稿件正文。

    必须剔除的内容（否则会把"改动说明里引用的黑名单短语"误判为正文命中）：
      - 头部引用块说明、代码块
      - Markdown 标题行
      - **表格行**（改动说明、指标表）
      - 行内代码 span
      - 附录区（`<!-- APPENDIX -->` 之后）
    """
    with open(p, encoding="utf-8") as f:
        t = f.read()
    cut = t.find("<!-- APPENDIX -->")
    if cut != -1:
        t = t[:cut]
    t = re.sub(r"^>.*$", "", t, flags=re.M)          # 引用块
    # 占位标记 `[TO BE MEASURED]` 必须整体剔除，否则：
    #   ① 其 "TO BE MEASURED" 会被被动式正则 `be\s+\w+(?:ed|en)` 误命中（每个占位符 +1 假阳性）；
    #   ② 其 3 个字母词会虚增词数，使 350–500 的字数自检失真。
    # （[ERR-2026W39-32]；与 anti_ai_check.py 的 PROTECTED 口径对齐）
    t = re.sub(r"\[?\s*TO\s+BE\s+MEASURED\s*\]?", " ", t, flags=re.I)
    t = re.sub(r"```.*?```", "", t, flags=re.S)      # 代码块
    t = re.sub(r"^#{1,6}\s.*$", "", t, flags=re.M)   # 标题
    t = re.sub(r"^\s*\|.*$", "", t, flags=re.M)      # 表格行
    t = re.sub(r"^\s*-{3,}\s*$", "", t, flags=re.M)  # 分隔线
    t = re.sub(r"`[^`]*`", "", t)                    # 行内代码
    t = re.sub(r"[*_\[\]]", "", t)
    return t


def split_sentences(text):
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[.!?])\s+(?=[A-Z(])", text)
    return [p.strip() for p in parts if len(p.split()) >= 5]


def extra_metrics(sents):
    low = " ".join(sents).lower()
    n = max(len(sents), 1)
    words = re.findall(r"[a-zA-Z][a-zA-Z-]+", low)
    passive = len(re.findall(r"\b(?:was|were|is|are|been|be)\s+\w+(?:ed|en)\b", low))
    first_person = len(re.findall(r"\b(?:we|our|us)\b", low))
    nominal = len(re.findall(r"\b\w{6,}(?:tion|sion|ment|ance|ence|ity|ness)\b", low))
    return {
        "passive_per_100sent": round(passive / n * 100, 1),
        "first_person_per_100sent": round(first_person / n * 100, 1),
        "nominalization_per_100words": round(nominal / max(len(words), 1) * 100, 2),
    }


def verdict(key, a, b):
    """返回 (判定, 提示)。阈值仅为本系统自检口径。"""
    rules = {
        "len_mean": (lambda x, y: y > x + 3, "我的平均句长明显长于真人"),
        "len_sd": (lambda x, y: y < x * 0.7, "我的句长波动不足（缺长短交错）"),
        "share_short_le15": (lambda x, y: y < x * 0.6, "我的短句比例过低，缺'短句下结论'"),
        "share_long_ge35": (lambda x, y: y > max(x * 1.8, x + 8), "我的超长句比例过高"),
        "conn_per_100sent": (lambda x, y: y > max(x * 1.4, x + 15), "连接词密度过高，疑模板堆砌"),
        "conn_types": (lambda x, y: y < x * 0.7, "连接词种类少，过渡手段单一"),
        "hedge_booster_ratio": (lambda x, y: y < min(1.0, x * 0.7), "审慎语气不足 / 强化词偏多"),
        "booster_per_100sent": (lambda x, y: y > max(x * 1.6, x + 3), "绝对化强化词偏多"),
        "ttr": (lambda x, y: y < x * 0.9, "词汇丰富度低于真人语料"),
        "ai_template_hits": (lambda x, y: y > 0, "命中 AI 模板短语，需逐条替换"),
        "passive_per_100sent": (lambda x, y: y > x * 1.6, "被动句偏多，行文发沉"),
        "nominalization_per_100words": (lambda x, y: y > x * 1.5, "名词化过重，动词被吃掉"),
    }
    fn = rules.get(key)
    if not fn:
        return "", ""
    try:
        bad = fn(a, b)
    except Exception:
        return "", ""
    return ("⚠️", fn.__doc__ or "") if bad else (("✅", "") if key else ("", ""))


LABELS = {
    "sentences": "句子数",
    "words": "词数",
    "len_mean": "平均句长（词）",
    "len_sd": "句长标准差",
    "len_p10": "句长 P10",
    "len_p50": "句长 P50",
    "len_p90": "句长 P90",
    "len_max": "最长句",
    "share_short_le15": "≤15 词短句占比 %",
    "share_long_ge35": "≥35 词长句占比 %",
    "conn_per_100sent": "连接词密度 /百句",
    "conn_types": "连接词种类数",
    "hedge_per_100sent": "模糊限制语 /百句（v1.0 核心口径）",
    "hedge_per_100sent_v2": "模糊限制语 /百句（v2.0 扩展口径）",
    "booster_per_100sent": "强化词 /百句",
    "hedge_booster_ratio": "hedge/booster 比（v1.0）",
    "hedge_booster_ratio_v2": "hedge/booster 比（v2.0）",
    "ttr": "TTR 词汇丰富度",
    "passive_per_100sent": "被动式 /百句",
    "first_person_per_100sent": "第一人称 /百句",
    "nominalization_per_100words": "名词化 /百词",
    "ai_template_hits": "AI 模板短语命中",
}

HINTS = {
    "len_mean": "我的平均句长明显长于真人（差 >3 词）",
    "len_sd": "我的句长波动不足（< 真人的 70%），缺长短交错",
    "share_short_le15": "我的短句比例过低，缺'短句下判断'的节奏",
    "share_long_ge35": "我的超长句比例过高",
    "conn_per_100sent": "连接词密度过高（> 真人 1.4 倍），疑模板堆砌",
    "conn_types": "连接词种类过少，过渡手段单一",
    "hedge_booster_ratio": "审慎语气不足 / 强化词偏多",
    "booster_per_100sent": "绝对化强化词偏多",
    "ttr": "词汇丰富度低于真人语料",
    "ai_template_hits": "命中 AI 模板短语，需逐条替换",
    "passive_per_100sent": "被动句偏多，行文发沉",
    "nominalization_per_100words": "名词化过重，动词被吃掉",
}

CHECK = {
    "len_mean": ("up", 3),
    "len_sd": ("down_rel", 0.7),
    "share_short_le15": ("down_rel", 0.6),
    "share_long_ge35": ("up_rel_abs", 1.8),
    "conn_per_100sent": ("up_rel_abs", 1.4),
    "conn_types": ("down_rel", 0.7),
    "hedge_booster_ratio": ("down_min", 1.0),
    "booster_per_100sent": ("up_rel_abs", 1.6),
    "ttr": ("down_rel", 0.9),
    "ai_template_hits": ("up_zero", 0),
    "passive_per_100sent": ("up_rel", 1.6),
    "nominalization_per_100words": ("up_rel", 1.5),
}


def check(k, a, b):
    c = CHECK.get(k)
    if not c:
        return ""
    mode, t = c
    if mode == "up":
        return HINTS[k] if b > a + t else ""
    if mode == "down_rel":
        return HINTS[k] if b < a * t else ""
    if mode == "up_rel":
        return HINTS[k] if b > a * t else ""
    if mode == "up_rel_abs":
        return HINTS[k] if b > max(a * t, a + 8) else ""
    if mode == "down_min":
        return HINTS[k] if b < min(1.0, a * t) else ""
    if mode == "up_zero":
        return HINTS[k] if b > 0 else ""
    return ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--human", required=True, help="样本A：真人语料文本")
    ap.add_argument("--mine", required=True, help="样本B：我的稿子")
    ap.add_argument("--out", default="")
    ap.add_argument("--label-a", default="样本A 真人语料")
    ap.add_argument("--label-b", default="样本B 我的初稿")
    a = ap.parse_args()

    sa = style_stats(split_sentences(read_text(a.human)))
    sb = style_stats(split_sentences(read_text(a.mine)))
    ea = extra_metrics(split_sentences(read_text(a.human)))
    eb = extra_metrics(split_sentences(read_text(a.mine)))
    sa.update(ea)
    sb.update(eb)

    L = [
        "# 文体指标对照（阶段5 量化层）",
        "",
        f"- {a.label_a}：`{a.human}`（{sa.get('sentences')} 句 / {sa.get('words')} 词）",
        f"- {a.label_b}：`{a.mine}`（{sb.get('sentences')} 句 / {sb.get('words')} 词）",
        "",
        "> 阈值仅为本系统自检口径，非文献定论。样本 A 是摘要级语料时，其句长天然短于全文正文，",
        "> 因此「句长类」指标的同口径比较优先级低于「连接词密度 / hedge-booster 比 / 模板短语」类指标。",
        "",
        "| 指标 | 样本A 真人 | 样本B 我的 | 差值 | 判定 | 说明 |",
        "|---|---|---|---|---|---|",
    ]
    flags = []
    # 短文本豁免：片段级稿件（<60 句）无法在"种类数""词汇丰富度"上与千句语料同口径比较，
    # 这类指标只作参考，不参与判定。否则会稳定产生假阳性。
    SHORT_TEXT = sb.get("sentences", 0) < 60
    SKIP_WHEN_SHORT = {"conn_types", "ttr"}
    for k, lab in LABELS.items():
        av, bv = sa.get(k, 0), sb.get(k, 0)
        try:
            d = round(float(bv) - float(av), 2)
        except Exception:
            d = ""
        if SHORT_TEXT and k in SKIP_WHEN_SHORT:
            h = f"（样本过短：{sb.get('sentences')} 句 < 60，不判定）"
            L.append(f"| {lab} | {av} | {bv} | {d:+} | — | {h} |" if isinstance(d, float)
                     else f"| {lab} | {av} | {bv} | | — | {h} |")
            continue
        h = check(k, float(av or 0), float(bv or 0))
        if h:
            flags.append(h)
        L.append(f"| {lab} | {av} | {bv} | {d:+} | {'⚠️' if h else '✅'} | {h} |" if isinstance(d, float)
                 else f"| {lab} | {av} | {bv} | | {'⚠️' if h else '✅'} | {h} |")

    L += ["", "## 待处理清单（按严重度排序，逐条对应到具体句子）", ""]
    if flags:
        for i, h in enumerate(flags, 1):
            L.append(f"{i}. {h}")
    else:
        L.append("（各项指标均在容差内，但**仍须做句级人工对照**——指标合格 ≠ 没有 AI 腔）")

    tmpl_b = sb.get("ai_template_detail", {})
    if tmpl_b:
        L += ["", "### 我稿中命中的 AI 模板短语（逐条替换或删除）", ""]
        for k, v in sorted(tmpl_b.items(), key=lambda x: -x[1]):
            L.append(f"- `{k}` × {v}")

    L += ["", f"_生成：style_compare.py_"]
    txt = "\n".join(L)
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as f:
            f.write(txt)
        print(f"[style_compare] → {a.out}")
    else:
        print(txt)
    print(f"  待处理项：{len(flags)}")
    print(f"  AI 模板短语命中：{sb.get('ai_template_hits')}（真人语料 {sa.get('ai_template_hits')}）")


if __name__ == "__main__":
    main()
