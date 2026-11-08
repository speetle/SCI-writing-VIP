#!/usr/bin/env python3
"""Locate sentences that require manual evidence-calibration review.

This script does not infer study design, evidence strength, citation support,
or whether a claim is correct. It only marks language patterns for human review.
"""

import argparse
import re
from collections import Counter
from pathlib import Path

HEDGES = [
    r"\bmay\b", r"\bmight\b", r"\bcould\b", r"\bpotentially\b",
    r"\bpossibly\b", r"\bperhaps\b", r"\bappears?\b",
    r"\bseems?\b", r"\bsuggests?\b", r"\bindicates?\b",
]
DISCLAIMERS = [
    r"\bcannot conclude\b", r"\bdoes not establish\b", r"\bdo not imply\b",
    r"\bdoes not imply\b", r"\bcannot exclude\b", r"\bcannot rule out\b",
    r"\bshould be interpreted with caution\b", r"\bwith caution\b",
    r"\bfurther (?:research|studies|work)(?:\s+\w+){0,3}\s+(?:is|are|will be)\s+(?:needed|required|warranted)\b",
    r"\bseveral limitations\b", r"\bhas limitations\b", r"\blimitations? (?:should|must) be acknowledged\b",
]
CAUSAL = [
    r"\bcaus(?:e|es|ed|ing)\b", r"\bdrives?\b", r"\bestablish(?:es|ed)?\b",
    r"\bdemonstrat(?:e|es|ed)\b", r"\bproves?\b", r"\brequired for\b",
    r"\bsufficient for\b", r"\bresults? in\b", r"\bleads? to\b",
]
PREDICTION = [
    r"\bpredicts?\b", r"\bpredictive\b", r"\bclinical utility\b",
    r"\bclinically useful\b", r"\bready for clinical\b",
]
GENERIC_FUTURE = [
    r"\bfurther (?:research|studies|work)\b", r"\bmore studies\b",
    r"\bwarrants? further investigation\b", r"\bneeds? further validation\b",
]
EMPTY_EMPHASIS = [
    r"\bprovides? (?:new |valuable )?insights?\b", r"\bopens? new avenues\b",
    r"\blays? (?:a )?(?:solid )?foundation\b", r"\bplays? (?:a )?(?:crucial|pivotal|key) role\b",
    r"\bof great (?:importance|significance)\b",
]


def compile_patterns(patterns):
    return [re.compile(p, re.I) for p in patterns]


HEDGE_RE = compile_patterns(HEDGES)
DISCLAIMER_RE = compile_patterns(DISCLAIMERS)
CAUSAL_RE = compile_patterns(CAUSAL)
PREDICTION_RE = compile_patterns(PREDICTION)
GENERIC_FUTURE_RE = compile_patterns(GENERIC_FUTURE)
EMPTY_EMPHASIS_RE = compile_patterns(EMPTY_EMPHASIS)
NUMBER_RE = re.compile(r"(?:\b\d+(?:\.\d+)?%?\b|\bP\s*[=<]|\b95%\s*CI\b|\bAUC\b)", re.I)


def clean_lines(text):
    text = text.split("<!-- APPENDIX -->", 1)[0]
    lines = []
    in_fence = False
    for number, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence or not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(">") or stripped.startswith("|"):
            continue
        if re.match(r"^[-*]\s+", stripped):
            stripped = re.sub(r"^[-*]\s+", "", stripped)
        if stripped:
            lines.append((number, stripped))
    return lines


def sentence_candidates(lines):
    for number, line in lines:
        parts = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9(])", line)
        for part in parts:
            sentence = part.strip()
            if len(sentence.split()) >= 5:
                yield number, sentence


def hits(patterns, sentence):
    return [p.pattern for p in patterns if p.search(sentence)]


def audit(sentence):
    flags = []
    hedge_count = len(hits(HEDGE_RE, sentence))
    disclaimer_count = len(hits(DISCLAIMER_RE, sentence))
    if hedge_count >= 2:
        flags.append("HEDGE_STACK")
    if disclaimer_count:
        flags.append("DISCLAIMER_REVIEW")
    if disclaimer_count >= 2:
        flags.append("DISCLAIMER_STACK")
    if hits(CAUSAL_RE, sentence):
        flags.append("CAUSAL_CLAIM")
    if hits(PREDICTION_RE, sentence):
        flags.append("PREDICTION_CLAIM")
    if hits(GENERIC_FUTURE_RE, sentence):
        flags.append("GENERIC_FUTURE")
    if hits(EMPTY_EMPHASIS_RE, sentence):
        flags.append("EMPTY_EMPHASIS")
    if NUMBER_RE.search(sentence) and hedge_count:
        flags.append("NUMERIC_WITH_HEDGE")
    return flags


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    source = Path(args.manuscript).expanduser().resolve()
    target = Path(args.out).expanduser().resolve()
    text = source.read_text(encoding="utf-8")
    rows = []
    counts = Counter()
    for number, sentence in sentence_candidates(clean_lines(text)):
        flags = audit(sentence)
        if flags:
            counts.update(flags)
            rows.append((number, flags, sentence))

    lines = [
        "# 证据校准机检候选",
        "",
        f"- 输入：`{source}`",
        f"- 候选句：{len(rows)}",
        "- 边界：本脚本只定位语言模式，不判断证据等级、文献支撑度或结论正误；每条均须人工裁决。",
        "",
        "## 标记汇总",
        "",
        "| 标记 | 数量 | 人工核查重点 |",
        "|---|---:|---|",
    ]
    explanations = {
        "HEDGE_STACK": "同句多个弱化标记，是否过度防御",
        "DISCLAIMER_REVIEW": "是否真实边界，是否可并入主判断",
        "DISCLAIMER_STACK": "同句多个免责节点，是否重复",
        "CAUSAL_CLAIM": "设计是否支持因果、必要性或充分性",
        "PREDICTION_CLAIM": "验证层级是否支持预测或临床用途",
        "GENERIC_FUTURE": "是否改为具体缺口与研究设计",
        "EMPTY_EMPHASIS": "是否用意义句替代具体判断",
        "NUMERIC_WITH_HEDGE": "数字是实测结果还是解释；实测结果不应无谓弱化",
    }
    for key in sorted(counts):
        lines.append(f"| {key} | {counts[key]} | {explanations[key]} |")
    lines.extend([
        "",
        "## 逐句候选",
        "",
        "| 行号 | 标记 | 原句 | 人工裁决 |",
        "|---:|---|---|---|",
    ])
    for number, flags, sentence in rows:
        escaped = sentence.replace("|", "\\|")
        lines.append(f"| {number} | {', '.join(flags)} | {escaped} | 待人工判定 |")
    lines.extend([
        "",
        "## 必须另行人工完成",
        "",
        "- 将每条承重结论填入 Claim Ledger，标主张类型、F/I/H、E0–E4 与四把范围锁。",
        "- 回读原始文献或数据，核查引用存在性与支撑度。",
        "- 逐段执行主线五问；本脚本不能判断离题、重复背景或证据链断裂。",
        "- 保留真实边界、阴性结果、关键对照和强制合规声明。",
        "",
    ])
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")
    print(f" candidates={len(rows)} out={target}")


if __name__ == "__main__":
    main()
