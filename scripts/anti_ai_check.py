#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
anti_ai_check.py — 「AI 味」机器检测（英文稿）

配套 references/anti-ai-checklist.md §二（12 条负面清单）与 §四（中译英痕迹）。
纯标准库、不联网、可对任何 .md/.txt 运行。

为什么需要它：清单里写着「加载去 AI 味技能（中文 qu-aiwei-zh／英文 humanizer）」，
但那是通用文本改写技能，不看学术稿的特有模式（无来源的量化、伪重复、
按操作顺序罗列结果等）。本脚本把 §二 的条目落成可复现的正则判据，
使每周的检测口径一致、可环比——口径不一致的「AI 味指数」没有比较意义。

用法
  python3 anti_ai_check.py --file 04_仿写训练/2026-W39_training_manuscript.md
  python3 anti_ai_check.py --file m.md --out report.md --json out.json

说明
  - 默认跳过引用块（> 开头）、代码块、表格；只检测正文散文。
  - `[TO BE MEASURED]` 等占位标记不计入「无来源的量化」。
  - 得分口径：10 - 加权命中密度，四舍五入到整数，下限 1。分数越高越像人写。
    该口径由 W39 基线轮定义；改动口径必须在 EVOLUTION_LEDGER 里注明，
    否则跨周不可比。
"""
import argparse
import json
import re
import sys

# 每条：(规则号, 名称, 正则, 权重, 说明)
RULES = [
    ("R1", "套话开头 / Delayed start",
     r"\bin recent years\b|\bwith the rapid (?:development|growth|advance)\b|"
     r"plays an increasingly important role\b|\bhas attracted (?:increasing|growing) attention\b",
     2.0, "删掉时间状语铺垫，直接从具体事实或数字切入"),
    ("R2", "空洞强调 / Empty emphasis",
     r"\bplays? a (?:crucial|key|vital|pivotal) role\b|\bit is worth noting that\b|"
     r"\bdelve[sd]? into\b|\bpaves? the way for\b|\bshed[s]? light on\b|"
     r"\bholds? great promise\b|\ba growing body of evidence\b|\bprovides? new insights?\b",
     2.0, "改为给出具体效应量或具体对象"),
    ("R3", "机械连接 / Mechanical connectives",
     r"(?:^|(?<=[.!?]\s))(?:Moreover|Furthermore|Additionally|In addition),",
     1.0, "相邻句连用同义连接词时，改逻辑承接（This ... translated into ...）"),
    ("R4", "伪并列 / False enumeration",
     r"(?:^|(?<=[.!?]\s))First(?:ly)?,|(?:^|(?<=[.!?]\s))Second(?:ly)?,|"
     r"(?:^|(?<=[.!?]\s))Third(?:ly)?,",
     0.5, "若三句实为递进/从属关系，改用连接性叙述"),
    ("R5", "无信息量形容词 / Vacuous adjectives",
     r"\bnovel\b|\bcomprehensive\b|\brobust\b|\bcutting-edge\b|\bstate-of-the-art\b|"
     r"\bdramatic(?:ally)?\b|\bprofound\b|\bgroundbreaking\b",
     1.0, "未做基准对比/稳健性检验/首创声明时不使用"),
    ("R6", "同义反复 / Tautological summary",
     r"\bin summary,?\s|\bin conclusion,?\s|\btaken together,?\s",
     0.5, "检查该句是否只是把前文结论换个说法再说一遍"),
    ("R7", "过度 hedge / Over-hedging",
     r"\bmay potentially\b|\bcould possibly\b|\bmight perhaps\b|"
     r"\bit could be considered\b|\bseems? to suggest that\b",
     1.5, "改为 is consistent with / is associated with，或直接给证据强度"),
    ("R8", "结尾升华 / Uplifting ending",
     r"\blays? a solid foundation\b|\bprovides? valuable insights\b|"
     r"\bopens? new avenues\b|\bfuture research (?:should|is needed)\b|"
     r"\bwarrants? further investigation\b",
     2.0, "改为具体、可执行的下一步（prospective cohort with ...）"),
    ("R9", "中译英痕迹 / Translationese",
     r"\bstud(?:y|ies) on\b|\bresearch about\b|\bthe reason is because\b|"
     r"\bit is well known that\b|\bmake[s]? great progress\b|\battach(?:es)? importance to\b",
     2.0, "改写为英语学术惯用搭配"),
    ("R12", "无来源的量化 / Unsourced quantification",
     r"(?<![A-Za-z])\d+(?:\.\d+)?\s?%|\b\d+(?:\.\d+)?-?fold\b",
     1.0, "每个百分比/倍数须有 PMID / accession / 统计输出出处，或标 [TO BE MEASURED]"),
]

# §四 英文专用检查
EN_RULES = [
    # 仅在「data」作句子主语时告警：Whether ... data is doubtful 这类是合法用法，属误报
    ("E1", "data is（学术惯例用 data are；限句首主语位置）",
     r"(?:^|(?<=[.!?]\s)|(?<=,\s))[Dd]ata is\b"),
    ("E2", "etc. 出现在正文", r"\betc\."),
    ("E3", "悬垂修饰怀疑（句首分词短语 + 主句主语不一致之高风险型式）",
     r"(?:^|(?<=[.!?]\s))(?:Using|Based on|Compared with|Given)\b[^.]{0,80},\s+(?:the|this|these|it)\b"),
]

# 低特异性规则：命中的多数情形在学术写作中完全合规（如并列的方法/局限清单），
# 需人工裁定，不计入分数，只在报告中列出待复核。
LOW_SPEC = {"R4", "R6"}

SKIP_LINE = re.compile(r"^\s*(?:>|\||```|\s*[-*]\s|#)")
PROTECTED = re.compile(r"\[TO BE MEASURED\]|\[PMID:\d+\]|GSE\d+|TCGA-[A-Z]+")


def prose_lines(text):
    """返回 (行号, 文本) —— 仅正文散文行。

    跳过：代码块、引用块、表格、列表项、标题行。
    遇到 `## References` 或 `## 附：...` 即停止扫描：参考文献与稿件附件
    （技法回执 / 数值溯源 / AI 自查记录）不是稿件散文；而自查记录会**引用被删掉的
    AI 味原句**，若纳入扫描会造成系统性误报。
    """
    out, in_code = [], False
    for i, ln in enumerate(text.split("\n"), 1):
        if ln.strip().startswith("```"):
            in_code = not in_code
            continue
        if re.match(r"^##\s*(References|附[:：])", ln.strip()):
            break
        if in_code or SKIP_LINE.match(ln) or not ln.strip():
            continue
        out.append((i, ln))
    return out


def scan(text):
    hits = []
    covered = [[False] * len(ln) for _, ln in prose_lines(text)]
    lines = prose_lines(text)
    for idx, (no, ln) in enumerate(lines):
        for rid, name, pat, w, advice in RULES:
            for m in re.finditer(pat, ln, flags=re.I):
                if rid == "R12" and PROTECTED.search(ln):
                    continue
                for k in range(m.start(), min(m.end(), len(covered[idx]))):
                    covered[idx][k] = True
                hits.append({"rule": rid, "name": name, "line": no,
                             "text": m.group(0).strip(), "weight": w, "advice": advice})
    # 相邻机械连接（R3 加权）
    starts = [(no, ln) for no, ln in lines
              if re.match(r"\s*(?:Moreover|Furthermore|Additionally|In addition),", ln)]
    for a, b in zip(starts, starts[1:]):
        if b[0] - a[0] <= 3:
            hits.append({"rule": "R3", "name": "机械连接（相邻连用）", "line": b[0],
                         "text": b[1].strip()[:80], "weight": 1.5,
                         "advice": "相邻段落/句子连用 moreover/furthermore，改逻辑承接"})
    for rid, name, pat in EN_RULES:
        for no, ln in lines:
            for m in re.finditer(pat, ln, flags=re.I):
                hits.append({"rule": rid, "name": name, "line": no,
                             "text": m.group(0).strip(), "weight": 0.5, "advice": "§四 英文专用检查"})
    return lines, hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    text = open(a.file, encoding="utf-8").read()
    lines, hits = scan(text)
    nwords = len(re.findall(r"[A-Za-z][A-Za-z'\-]*", "\n".join(l for _, l in lines))) or 1

    weighted = sum(h["weight"] for h in hits if h["rule"] not in LOW_SPEC)
    lowspec = sum(h["weight"] for h in hits if h["rule"] in LOW_SPEC)
    density = 1000.0 * weighted / nwords          # 每千词加权命中（仅计高特异性规则）
    score = max(1, min(10, round(10 - density / 3.0)))

    by_rule = {}
    for h in hits:
        by_rule.setdefault((h["rule"], h["name"]), []).append(h)

    rep = []
    rep.append(f"# AI 味机器检测报告\n")
    rep.append(f"- 受检文件：`{a.file}`")
    rep.append(f"- 检测脚本：`scripts/anti_ai_check.py`（配套 `references/anti-ai-checklist.md` §二/§四）")
    rep.append(f"- 正文词数（散文部分）：{nwords}")
    rep.append(f"- 高特异性规则加权命中：{weighted:g}；每千词密度：{density:.2f}")
    rep.append(f"- 低特异性规则加权命中（需人工裁定，不计分）：{lowspec:g}")
    rep.append(f"- **AI 味指数（10 分制，越高越像人写）：{score}**\n")
    rep.append("| 规则 | 名称 | 命中 | 权重/条 | 计入评分 |")
    rep.append("|---|---|---:|---:|:---:|")
    for (rid, name), hs in sorted(by_rule.items()):
        rep.append(f"| {rid} | {name} | {len(hs)} | {hs[0]['weight']:g} | "
                   f"{'否（低特异性）' if rid in LOW_SPEC else '是'} |")
    if not by_rule:
        rep.append("| — | 未命中任何规则 | 0 | — | — |")
    rep.append("\n## 命中明细\n")
    if not hits:
        rep.append("未命中任何规则。\n")
    for (rid, name), hs in sorted(by_rule.items()):
        rep.append(f"### {rid} {name}（{len(hs)} 处）")
        for h in hs[:20]:
            rep.append(f"- L{h['line']}：`{h['text'][:70]}`")
        if len(hs) > 20:
            rep.append(f"- …另 {len(hs)-20} 处")
        rep.append(f"- 处理建议：{hs[0]['advice']}\n")

    out = "\n".join(rep)
    print(out)
    if a.out:
        open(a.out, "w", encoding="utf-8").write(out)
    if a.json:
        json.dump({"file": a.file, "words": nwords, "weighted": weighted,
                   "density": round(density, 3), "score": score, "hits": hits},
                  open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
