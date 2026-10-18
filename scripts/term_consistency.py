#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
term_consistency.py — 术语一致性检测（AI 痕迹三步法的第二步机检）

检测四类问题：
  1. VARIANT        同一实体的多种写法（大小写 / 连字符 / 单复数 / 全角）
  2. ACRONYM_UNDEF  缩写首现未定义，或定义后仍混用全称
  3. UNIT_FORM      单位与统计符号写法不一致（5mg/kg vs 5 mg/kg；P vs p）
  4. HIGH_RISK      高危词族混用（knockdown / silencing / inhibition 等同句出现）

只给候选，不做判定。领域同形词会误报，最终由人工裁决。

用法：
  python3 term_consistency.py --manuscript 稿.md --out 术语一致性报告.md
  python3 term_consistency.py --manuscript 稿.md --json
"""
import argparse
import json
import re
import sys
from collections import defaultdict

# ---------------- 高危词族：混用会改变研究对象/干预强度 ----------------
HIGH_RISK_FAMILIES = {
    "干预强度": ["knockdown", "knockout", "silencing", "inhibition", "depletion", "ablation"],
    "生存终点": ["overall survival", "progression-free survival", "disease-free survival", "survival rate"],
    "因果措辞": ["associated with", "correlated with", "caused", "drives", "leads to"],
    "显著表述": ["significant", "significantly", "notable", "marked"],
    "体外体内": ["in vitro", "in vivo", "ex vivo"],
    "表达操作": ["overexpression", "ectopic expression", "re-expression", "rescue"],
}

# 不参与 VARIANT 的常见词（大小写误报源）
STOP = set("""
a an the and or but if then than that this these those of in on at to for from by with without
as is are was were be been being has have had do does did not no nor so such it its we our they their
here there however therefore moreover furthermore thus although whereas while because since
figure fig table supplementary data results methods discussion introduction abstract
we found shown show shows used using was were compared compare group groups control controls
mean means total number numbers rate rates level levels time times day days week weeks month months year years
high low higher lower increase increased decrease decreased effect effects change changes
patient patients sample samples cell cells study studies model models analysis analyses
p ns sd sem ci hr or rr hr ci n mean
""".split())

UNIT_RE = re.compile(
    r"(?<![\w.])(\d+(?:\.\d+)?)\s*(mg/kg|mg\s*kg|mg|µg|μg|ng|pg|g|kg|mL|ml|µL|μL|L|"
    r"nM|µM|μM|mM|M|nm|µm|μm|mm|cm|km|min|h|hr|hrs|s|sec|days|weeks|months|years|°C)(?![\w])"
)
P_RE = re.compile(r"(?<![\w])([Pp])\s*([=<>≤≥])\s*(0?\.\d+|\d+\.\d+|\d+)(?![\w])")
PCT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(%|percent)")
ACRO_DEF_RE = re.compile(r"\(([A-Z]{2,8})\)")
ACRO_USE_RE = re.compile(r"(?<![\w\-])([A-Z]{2,8})(?![\w\-])")
# 缩写检测跳过的通用符号（不含数字的基因符号已在正则层排除）
ACRO_SKIP = set("""PMID DOI DNA RNA PCR SD SEM CI HR OR RR NS FIG FIGURE TABLE
SUPPL SI WT KO OE PBS FBS DMSO ELISA IHC QPCR ALL ANY AND THE""".split())
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-\.]*")


def read_text(path):
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        return fh.read()


def split_lines(text):
    return text.splitlines()


def is_term_like(tok):
    """含内部大写 / 数字 / 连字符，才视为术语候选。"""
    if len(tok) < 2:
        return False
    if tok.lower() in STOP:
        return False
    body = tok[1:]
    if any(c.isupper() for c in body):
        return True
    if any(c.isdigit() for c in body):
        return True
    if "-" in tok:
        return True
    return False


def norm_key(tok):
    return re.sub(r"[\-\.\s]", "", tok).lower()


def find_variants(lines):
    occ = defaultdict(lambda: defaultdict(list))  # key -> form -> [lineno]
    for i, line in enumerate(lines, 1):
        for m in WORD_RE.finditer(line):
            tok = m.group(0).strip(".-")
            if not is_term_like(tok):
                continue
            occ[norm_key(tok)][tok].append(i)
    out = []
    for key, forms in occ.items():
        if len(forms) < 2:
            continue
        total = sum(len(v) for v in forms.values())
        if total < 2:
            continue
        forms_sorted = sorted(forms.items(), key=lambda kv: (-len(kv[1]), kv[0]))
        out.append({
            "key": key,
            "forms": [{"form": f, "count": len(v), "lines": sorted(set(v))[:8]} for f, v in forms_sorted],
            "total": total,
        })
    out.sort(key=lambda d: (-d["total"], d["key"]))
    return out


def find_acronyms(text, lines):
    defined = {}
    for m in ACRO_DEF_RE.finditer(text):
        if m.group(1) in ACRO_SKIP:
            continue
        defined.setdefault(m.group(1), 0)
        defined[m.group(1)] += 1
    used = defaultdict(list)
    for i, line in enumerate(lines, 1):
        for m in ACRO_USE_RE.finditer(line):
            tok = m.group(1)
            if tok in ACRO_SKIP or tok.lower() in STOP or len(tok) < 2:
                continue
            used[tok].append(i)
    undefined = []
    for tok, ls in used.items():
        if tok in defined:
            continue
        if len(ls) >= 2:  # 用两次以上才算“应在首现处定义”
            undefined.append({"acronym": tok, "count": len(ls), "lines": sorted(set(ls))[:8]})
    undefined.sort(key=lambda d: (-d["count"], d["acronym"]))
    return sorted(defined.keys()), undefined


def find_units(text):
    unit_forms = defaultdict(set)   # unit -> {spacing variant}
    unit_lines = defaultdict(list)
    for i, line in enumerate(split_lines(text), 1):
        for m in UNIT_RE.finditer(line):
            unit = m.group(2)
            gap = "space" if re.match(r"\d+\.?\d*\s", m.group(0)) else "nospace"
            unit_forms[unit].add(gap)
            unit_lines[(unit, gap)].append(i)
    unit_issues = []
    for unit in sorted(unit_forms):
        if len(unit_forms[unit]) > 1:
            unit_issues.append({
                "unit": unit,
                "variants": sorted(unit_forms[unit]),
                "lines": {g: sorted(set(unit_lines[(unit, g)]))[:6] for g in unit_forms[unit]},
            })

    p_forms = defaultdict(list)
    for i, line in enumerate(split_lines(text), 1):
        for m in P_RE.finditer(line):
            p_forms[m.group(1)].append(i)
    p_issue = None
    if len(p_forms) > 1:
        p_issue = {k: sorted(set(v))[:8] for k, v in p_forms.items()}

    pct_forms = defaultdict(list)
    for i, line in enumerate(split_lines(text), 1):
        for m in PCT_RE.finditer(line):
            gap = "space" if re.match(r"\d+\.?\d*\s", m.group(0)) else "nospace"
            pct_forms[gap].append(i)
    pct_issue = None
    if len(pct_forms) > 1:
        pct_issue = {k: sorted(set(v))[:8] for k, v in pct_forms.items()}

    return unit_issues, p_issue, pct_issue


def find_high_risk(text):
    low = text.lower()
    hits = []
    for fam, members in HIGH_RISK_FAMILIES.items():
        present = [m for m in members if re.search(r"(?<![\w])" + re.escape(m) + r"(?![\w])", low)]
        if len(present) >= 2:
            lines = {}
            for m in present:
                ls = [i for i, line in enumerate(split_lines(text), 1)
                      if re.search(r"(?<![\w])" + re.escape(m) + r"(?![\w])", line.lower())]
                lines[m] = ls[:6]
            hits.append({"family": fam, "members": present, "lines": lines})
    return hits


def build_report(res, src):
    L = []
    add = L.append
    add("# 术语一致性报告")
    add("")
    add("- 源文件：`%s`" % src)
    add("- 判定口径：见 `references/ai-trace-remediation.md` 第二步（本报告只给候选，最终人工裁决）")
    add("")
    add("## 一、汇总")
    add("")
    add("| 类别 | 命中 |")
    add("|---|---|")
    add("| VARIANT 同一实体多写法 | %d |" % len(res["variants"]))
    add("| ACRONYM_UNDEF 缩写未定义 | %d |" % len(res["acronyms_undefined"]))
    add("| UNIT_FORM 单位写法不一致 | %d |" % (len(res["units"]) + (1 if res["p_case"] else 0) + (1 if res["pct"] else 0)))
    add("| HIGH_RISK 高危词族混用 | %d |" % len(res["high_risk"]))
    add("")

    add("## 二、VARIANT（同一实体的多种写法）")
    add("")
    if res["variants"]:
        add("| 归一化键 | 写法（出现次数） | 行号 |")
        add("|---|---|---|")
        for v in res["variants"][:60]:
            forms = " / ".join("%s(%d)" % (f["form"], f["count"]) for f in v["forms"])
            lines = ", ".join(sorted({str(x) for f in v["forms"] for x in f["lines"]})[:10])
            add("| `%s` | %s | %s |" % (v["key"], forms, lines))
    else:
        add("无命中。")
    add("")

    add("## 三、ACRONYM_UNDEF（缩写首现未定义，出现 ≥2 次）")
    add("")
    if res["acronyms_undefined"]:
        add("| 缩写 | 次数 | 行号 |")
        add("|---|---|---|")
        for a in res["acronyms_undefined"][:40]:
            add("| `%s` | %d | %s |" % (a["acronym"], a["count"], ", ".join(str(x) for x in a["lines"])))
    else:
        add("无命中。")
    if res["acronyms_defined"]:
        add("")
        add("已检测到定义的缩写（供核对是否全文统一）：%s" % ", ".join("`%s`" % a for a in res["acronyms_defined"][:40]))
    add("")

    add("## 四、UNIT_FORM（单位与统计符号）")
    add("")
    if res["units"]:
        add("| 单位 | 出现的写法 | 行号 |")
        add("|---|---|---|")
        for u in res["units"]:
            add("| `%s` | %s | %s |" % (u["unit"], ", ".join(u["variants"]),
                                        "; ".join("%s: %s" % (g, ",".join(map(str, ls))) for g, ls in u["lines"].items())))
    else:
        add("单位空格写法一致。")
    if res["p_case"]:
        add("")
        add("**P/p 大小写混用**：%s" % "; ".join("%s: %s" % (k, ",".join(map(str, v))) for k, v in res["p_case"].items()))
    if res["pct"]:
        add("")
        add("**百分号空格混用**：%s" % "; ".join("%s: %s" % (k, ",".join(map(str, v))) for k, v in res["pct"].items()))
    add("")

    add("## 五、HIGH_RISK（高危词族混用）")
    add("")
    if res["high_risk"]:
        for h in res["high_risk"]:
            add("### %s：%s" % (h["family"], " / ".join("`%s`" % m for m in h["members"])))
            for m, ls in h["lines"].items():
                add("- `%s`：行 %s" % (m, ", ".join(map(str, ls))))
            add("")
    else:
        add("无命中。")
    add("")
    add("## 六、人工复核清单")
    add("")
    add("- [ ] 五类高危替换（研究对象 / 干预强度 / 终点指标 / 时间窗剂量 / 统计口径）逐条核")
    add("- [ ] 每个 VARIANT 组确认是否为同一实体（同形词误报直接划掉）")
    add("- [ ] 同一数字在 Abstract / Results / 图注 / Discussion 完全一致（含小数位）")
    add("- [ ] 缩写首现定义、此后不再混用全称")
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser(description="术语一致性检测（AI 痕迹三步法第二步）")
    ap.add_argument("--manuscript", required=True, help="稿件文件（md / txt）")
    ap.add_argument("--out", help="输出报告路径（.md）")
    ap.add_argument("--json", action="store_true", help="输出 JSON 到 stdout")
    args = ap.parse_args()

    text = read_text(args.manuscript)
    lines = split_lines(text)
    defined, undefined = find_acronyms(text, lines)
    units, p_case, pct = find_units(text)
    res = {
        "source": args.manuscript,
        "variants": find_variants(lines),
        "acronyms_defined": defined,
        "acronyms_undefined": undefined,
        "units": units,
        "p_case": p_case,
        "pct": pct,
        "high_risk": find_high_risk(text),
    }

    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
        return 0

    report = build_report(res, args.manuscript)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(report)
        n = (len(res["variants"]) + len(res["acronyms_undefined"]) + len(res["units"])
             + (1 if p_case else 0) + (1 if pct else 0) + len(res["high_risk"]))
        print("WROTE %s | issues=%d" % (args.out, n))
    else:
        sys.stdout.write(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
