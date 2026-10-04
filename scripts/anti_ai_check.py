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

SKIP_LINE = re.compile(r"^\s*(?:>|\||```|\s*[-*]\s|\d+[.)]\s|#)")
# ⚠️ `\d+[.)]\s` 为 2026-10-03 补入：此前**有序列表项**（稿首「起草前四项强制声明」的 `1. …`）
#    未被剔除，会被当作正文计入词数与 R 类命中（[ERR-2026W40-55]，与 `style_compare.py` 同步修）。
PROTECTED = re.compile(r"\[TO BE MEASURED\]|\[PMID:\d+\]|GSE\d+|TCGA-[A-Z]+")

# 方法学参数豁免（[ERR-2026W39-22]，D07 落地为脚本规则）
# 下列"数字"是**方法参数**而非**结果数值**，其来源为方法本身/素材 Methods，不属"无来源量化"：
#   ① 交叉验证折数 `10-fold` / `fivefold`；② 显著性阈值 `p < 0.05` / `p = 0.001`；
#   ③ 样本量 `n = 103`；④ 效应量阈值 `|log2FC| > 1`；⑤ 软件版本 `v4.1.0` / `R version 4.3`；
#   ⑥ 剂量 / 时间等实验参数（`50 mg/kg`、`6 h`、`37 °C`）。
# ⚠️ 本豁免**只对 R12 生效**，且**须在报告中逐条列出**（避免变成"静默放过"）。
METHOD_PARAM = re.compile(
    r"^\s*\d+(?:\.\d+)?[\s-]?fold\s*$"
    r"|^\s*[Pp]\s*[<>=]\s*0?\.\d+\s*$"
    r"|^\s*n\s*=\s*\d+\s*$"
    r"|^\s*\|\s*log2\s*FC\s*\|.*$"
    r"|^\s*v?\d+(?:\.\d+){1,2}\s*$"
    r"|^\s*\d+(?:\.\d+)?\s*(?:mg/kg|mg|μg|µg|ug|ng|mL|μL|uL|µL|mM|µM|uM|nM|h|hr|hrs|hours|min|days|weeks|months|°C)\s*$"
)


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
    method_skips = []
    covered = [[False] * len(ln) for _, ln in prose_lines(text)]
    lines = prose_lines(text)
    for idx, (no, ln) in enumerate(lines):
        for rid, name, pat, w, advice in RULES:
            for m in re.finditer(pat, ln, flags=re.I):
                if rid == "R12" and PROTECTED.search(ln):
                    continue
                # R12 方法学参数豁免（[ERR-2026W39-22]）：`10-fold` / `p < 0.05` / `n = 103`
                # / `v4.1.0` / `50 mg/kg` 等属方法参数，不计入"无来源量化"。
                if rid == "R12" and METHOD_PARAM.match(m.group(0)):
                    method_skips.append({"rule": rid, "line": no,
                                         "text": m.group(0).strip()})
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
    return lines, hits, method_skips


def strip_appendix(text):
    """截断附录区，避免「本稿起草说明 / 指标表」里引用的黑名单短语被计入正文。

    修复依据：[ERR-2026W39-13]（机检脚本被稿件附录污染）在 `style_compare.py` 已修复，
    但 `anti_ai_check.py` 至 D03 仍直接读整份文件 → 同一缺陷在本脚本复现
    （D03 rev0 的 R2 命中中，2/4 处来自附录《起草说明》的自述清单）。
    """
    cut = text.find("<!-- APPENDIX -->")
    if cut != -1:
        text = text[:cut]
    # 再去掉引用块（稿首警示/素材来源声明），避免把声明本身当作正文
    text = re.sub(r"^>.*$", "", text, flags=re.M)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--file", required=True)
    ap.add_argument("--out", default="")
    ap.add_argument("--json", default="")
    ap.add_argument("--no-strip-appendix", action="store_true",
                    help="不截断附录（默认截断；一般无需开启）")
    a = ap.parse_args()

    raw = open(a.file, encoding="utf-8").read()
    # 稿首素材来源声明：若声明了 PMID，则 R1/R12 的量化命中降级为「已声明来源」不计分
    # ⚠️ D07 修正：原正则 `PMID\s*\d{6,}` 无法容忍 markdown 强调标记（`PMID **42759982**`），
    #    导致"已声明来源"被误判为"未声明"。改为允许 PMID 与数字之间出现任意非数字字符（≤6 个）。
    head = raw[:raw.find("<!-- APPENDIX -->")] if "<!-- APPENDIX -->" in raw else raw[:1500]
    declares_source = bool(re.search(r"PMID[^\d]{0,6}\d{6,}", head))
    text = raw if a.no_strip_appendix else strip_appendix(raw)
    lines, hits, method_skips = scan(text)
    # 词数同样须剔除占位标记，否则 "TO BE MEASURED" 会被当作 3 个字母词虚增词数，
    # 使每千词密度被稀释、350–500 的字数自检失真（[ERR-2026W39-32]，与 style_compare 对齐）。
    prose = PROTECTED.sub(" ", "\n".join(l for _, l in lines))
    nwords = len(re.findall(r"[A-Za-z][A-Za-z'\-]*", prose)) or 1

    # 降级规则：R1（无来源的量化）/ R12 属同族；本题稿首已声明素材 PMID 时不计分
    DOWNGRADE = {"R1", "R12"} if declares_source else set()
    weighted = sum(h["weight"] for h in hits
                   if h["rule"] not in LOW_SPEC and h["rule"] not in DOWNGRADE)
    lowspec = sum(h["weight"] for h in hits if h["rule"] in LOW_SPEC)
    downgraded = sum(h["weight"] for h in hits if h["rule"] in DOWNGRADE)
    density = 1000.0 * weighted / nwords          # 每千词加权命中（仅计高特异性规则）
    score = max(1, min(10, round(10 - density / 3.0)))

    by_rule = {}
    for h in hits:
        by_rule.setdefault((h["rule"], h["name"]), []).append(h)

    rep = []
    rep.append(f"# AI 味机器检测报告\n")
    rep.append(f"- 受检文件：`{a.file}`")
    rep.append(f"- 检测脚本：`scripts/anti_ai_check.py`（配套 `references/anti-ai-checklist.md` §二/§四）")
    rep.append(f"- 正文范围：{'整份文件' if a.no_strip_appendix else '已截断 `<!-- APPENDIX -->` 并剔除稿首引用块'}")
    rep.append(f"- 稿首是否声明素材 PMID：{'是' if declares_source else '否'}"
               + ("（R1/R12 命中降级为「已声明来源」，不计分，须逐值人工复核）" if declares_source else ""))
    rep.append(f"- 正文词数（散文部分）：{nwords}")
    rep.append(f"- 高特异性规则加权命中：{weighted:g}；每千词密度：{density:.2f}")
    rep.append(f"- 低特异性规则加权命中（需人工裁定，不计分）：{lowspec:g}")
    if downgraded:
        rep.append(f"- 降级命中（R1/R12，稿首已声明来源，不计分）：{downgraded:g}")
    if method_skips:
        rep.append(f"- **R12 方法学参数豁免命中（不计分，须逐条人工确认）**：{len(method_skips)} 处 —— "
                   + "、".join(f"`{s['text']}`(L{s['line']})" for s in method_skips))
    rep.append(f"- **AI 味指数（10 分制，越高越像人写）：{score}**\n")
    rep.append("| 规则 | 名称 | 命中 | 权重/条 | 计入评分 |")
    rep.append("|---|---|---:|---:|:---:|")
    for (rid, name), hs in sorted(by_rule.items()):
        if rid in LOW_SPEC:
            mark = "否（低特异性）"
        elif rid in DOWNGRADE:
            mark = "否（稿首已声明来源）"
        else:
            mark = "是"
        rep.append(f"| {rid} | {name} | {len(hs)} | {hs[0]['weight']:g} | {mark} |")
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
