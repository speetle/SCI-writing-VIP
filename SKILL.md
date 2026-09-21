---
name: SCI-writing-VIP
description: >-
  可持续自我迭代型生物医学/生信 SCI 科研助手。以真实 PubMed 文献为唯一语言样本，
  通过双层节奏持续训练写作能力：日课七阶段（每日 ≥75 篇文献归档 → 语言范式提取 →
  英文仿写初稿 → 句级差异诊断 → 两轮强制修订 → 沉淀），周课三件套（领域前沿研究快报
  Word + 50 篇 IMRAD 架构扫面与 2 篇全文深拆 + 通用写作框架模板升版）。
  产出含中文报告与英文稿件，全程禁止编造数据与文献，一切数值可溯源到 PMID 或 accession。
when_to_use: >-
  用户需要：每日/每周文献训练；从 PubMed 文献中提取地道句式与逻辑衔接范式；诊断并去除
  英文稿的 AI 写作文风；生成领域前沿研究快报；拆解论文 IMRAD 架构；设计论文大纲；修改
  论文结构与段落；润色英文稿；模拟审稿；核验参考文献。触发词：SCI 写作、去 AI 味、AI 腔、
  句式库、语言范式、IMRAD、写作进化、每日训练、文献训练、前沿快报、润色、审稿、论文大纲。
license: MIT
agent_created: true
metadata:
  emoji: "🧬"
  requires:
    bins:
      - python
    python:
      - python-docx
---

# SCI-writing-VIP — 可持续自我迭代的 SCI 科研助手

## 0. 这个技能解决什么问题

通用 AI 写英文论文有两个绕不开的毛病：**AI 腔**（模板化过渡、空洞强化词、段落等长、句式单一），以及**无据可溯**（数据、机制、参考文献来源不明）。

本技能的做法是把写作能力当成可以**用真实文献训练出来的技能**，靠两个机制逼近真人写作：

1. **样本 A / 样本 B 对照**——样本 A 是 PubMed 真人原文，样本 B 是自己产出的文本。所有诊断都必须是 A 与 B 的**量化对照**，不是套用网上通用 SCI 模板。
2. **累积型知识库**——每周的收获必须落成可复用的条目（句式、衔接范式、错题、结构规则），下次训练前先读，不许从零开始。

**核心立场**：不提取 = 没读过；不量化 = 没进步；结论强度不得超过阅读深度；红线优先于完成度。

---

## 1. 铁律（任何情况不得违背）

| # | 铁律 | 落地方式 |
|---|---|---|
| L1 | 所有科学观点、机制、结论 **100% 来源于 PubMed 原始文献** | 每条句/机制须可回溯到 PMID；禁止编造数据、虚构机制、杜撰结论 |
| L2 | **不夸大研究意义**，无充分证据禁用 `novel` / `ground-breaking` / `remarkable` | `novel` 每篇 ≤1 次且须有操作化定义 |
| L3 | **完整流程不省略、不合并、不跳步** | 日课七阶段逐个产出文件；周课三件套独立产出 |
| L4 | 每周形成知识库沉淀，下周训练前**主动参考** | 每次训练前必读语言范式四库 + 错题本 |
| L5 | 全程区分**样本 A（真人原文）** 与 **样本 B（自产文本）** | 诊断与修订阶段强制双样本对照 |
| L6 | 输出排版分大标题/二级小标题，要点条目化 | 拒绝无分割的流水文字 |

### 系统红线 R1–R8

| # | 红线 | 判定 |
|---|---|---|
| **R1** | 不编造数据 | 训练稿数值只能来自已发表论文真实数值（注 PMID）或公开数据集（注 accession）；否则写 `[TO BE MEASURED]` |
| **R2** | 不编造文献 | 所有 PMID/DOI 必须来自真实检索结果，**禁止凭记忆生成** |
| **R3** | 指标可溯源 | 官方 JIF 与代理指标（OpenAlex 2yrMCC）**严禁混称**；抓不到标 `PENDING`，**绝不估算** |
| **R4** | 结论强度 ≤ 阅读深度 | 摘要级信息不得写成"精读发现"；未读全文不评价方法学细节 |
| **R5** | 训练稿不得投稿 | 训练稿首部必须带警示块 |
| **R6** | 不静默修改 | 任何清洗、剔除、筛选规则变更留在 `search_log.md` |
| **R7** | 交付前占位符扫描 | `[REF` / `TODO` / `XXX` / `待补` / `待核` 五类 0 命中（唯一允许 `[TO BE MEASURED]`，须在稿首声明） |
| **R8** | 字段级修复须回溯下游 | 对已交付数据源做回溯修复后，必须列出该字段的**全部下游依赖项**并逐项复核 |

---

## 2. 双层节奏总览

> 周量 ≥500 篇 = 日课 7 天 × ≥75 篇。周课每周只执行一次。

```
日课（D01–D07，每日 ≥75 篇）              周课（每周 1 次）
① 文献基础归档（科学问题/设计/结论/局限）     ⑧ 领域前沿研究快报（Word）
② 语言范式深度拆解（4 类清单入累积库）         ⑨ IMRAD 架构拆解（50 篇扫面 + 2 篇深拆）
③ 热点与选题速览（当日增量）                  ⑩ 通用写作框架模板升版
④ AI 训练写作初稿（350–500 词）
⑤ 写作差异诊断报告（句级，样本A vs B）
⑥ 两轮修订（rev1 纠错改风格 / rev2 投稿向）
⑦ 当日沉淀（收获/坑点/明日改进）
```

**前置动作**：首次使用需先建周池（见 §5）。日课的七个阶段不重复建池。

---

## 3. 日课七阶段

完整 SOP 见 `references/daily-sop.md`。

| 阶段 | 产出 | 关键约束 |
|---|---|---|
| ① 归档 | `01_文献库/<周次>/D0n/归档笔记.md` | 每篇记 科学问题 / 设计类型 / 核心结论 / 局限性；**未命中线索写"摘要未述"，不推断** |
| ② 语言范式 | `语言范式原料.md` → 汇入 `03_语言范式库/A~D` | **不提取 = 没读过**；每条须含原文引句 + PMID |
| ③ 热点速览 | 追加至当日归档末尾 | 只记增量 |
| ④ 初稿 | `05_仿写训练/<周次>/D0n/01_AI训练写作初稿.md` | 350–500 词；题材取自当日文献；**允许保留 AI 习惯**（便于诊断） |
| ⑤ 诊断 | `02_写作差异诊断报告.md` | **句级**：初稿原句 ↔ 真人参考句（附 PMID）↔ 差异实质；禁用"有点 AI 感" |
| ⑥ 两轮修订 | `03_第1轮修订稿.md`、`04_第2轮最终修订稿.md` | 两轮**独立**，不得合并；科学事实不变；**每轮修订后立即重新计词数** |
| ⑦ 沉淀 | `06_进化复盘/沉淀_<周次>_D0n.md` | 收获 / 坑点 / 3 个主要短板 / 明日专项；含 rev0/rev1/rev2 指标对比表 |

**每次训练前固定动作（L4）**：读 `03_语言范式库/` 四份文件 + `06_进化复盘/ERROR_DO_NOT_REPEAT.md` → 复述本次专项 → 再动手。

---

## 4. 周课三件套

| 产出 | 路径 | 必备内容 |
|---|---|---|
| ⑧ 领域前沿研究快报（Word） | `02_前沿快报/领域前沿研究快报_<周次>_<日期>.docx` | 2-1 当前 3–5 个核心热点（主流在做什么 + 主流技术手段）；2-2 每个热点的**研究缺口**（已做到哪 / 没解决 / 有争议 / 待验证）；2-3 **原创选题灵感 3 条**（主题 + 生信或实验思路 + 创新点 + 现实意义 + 前置风险，须可行不空泛）；2-4 冷热提示（可关注 / 竞争激烈 / 需改造）；附方法学声明（检索式、时间窗、去重数、筛选规则、IF 来源与抓取日、代理指标占比、阅读深度声明） |
| ⑨ IMRAD 架构拆解 | `04_IMRAD架构库/<周次>_IMRAD拆解.md` | 50 篇**结构扫面统计** + 2 篇**逐段深拆**（I 叙事链条 / M 组织与参数报告习惯 / R 叙事顺序与图表配合 / D 六段链与 limitation 写法）+ 交叉结论 + 置信度分级 |
| ⑩ 通用写作框架模板升版 | `04_IMRAD架构库/通用写作框架模板.md` | 把 ⑨ 的结论落进框架；与上一版冲突处**不得静默覆盖**，须写明冲突与解释；每版留更新日志 |

细则见 `references/weekly-sop.md`、`references/imrad-anatomy-protocol.md`。

---

## 5. 检索层（建周池，日课前置）

```bash
SKILL=<本技能目录>
WEEK=<周次目录，如 01_文献库/2026-W39>

# 1) 建周池（两遍法，第二遍命中缓存）
python3 $SKILL/scripts/harvest.py --out-dir $WEEK/_pool --cache-dir $WEEK/_cache \
  --start <起> --end <止> --target 1400 --no-if

# 2) 建官方 JIF 表（建议 5 片并行）
python3 $SKILL/scripts/journal_if.py --from-csv $WEEK/_pool/papers_master.csv \
  --col journal_iso --full-col journal_full --out 00_系统/journal_metrics.csv
python3 $SKILL/scripts/check_if_table.py --table 00_系统/journal_metrics.csv   # 归属自检

# 3) 终版精选（≥500 篇）
python3 $SKILL/scripts/harvest.py --out-dir $WEEK --cache-dir $WEEK/_cache \
  --start <起> --end <止> --target 520 --if-table 00_系统/journal_metrics.csv

# 4) 官方 JIF 覆盖不足时，用代理指标补齐（严格标注，不混称）
python3 $SKILL/scripts/journal_if_openalex.py --pool $WEEK/papers_master.csv \
  --out 00_系统/journal_metrics_openalex.csv --patch-pool

# 5) 【强制】ID 字段自检——建池后必跑
python3 $SKILL/scripts/repair_ids.py --pool $WEEK/papers_master.csv \
  --report $WEEK/_verify/id_repair_report.md
```

### ⚠️ 两个必须知道的坑

**坑 1：ArticleIdList 递归陷阱（会导致数据错位）**

`efetch db=pubmed` 返回的 XML 中，`art.findall(".//ArticleIdList/ArticleId")` 会**递归命中 `ReferenceList/*/ArticleIdList`**（参考文献自己的 DOI/PMCID），且循环赋值使**最后一条胜出**。结果：`doi` / `pmcid` / `oa` 三列记的是别篇文献的标识。

实测：PMID `42756821` 被记成 `PMC10553084` / `10.1021/acsami.4c09037`，真实值为 `PMC13583601` / `10.3389/fimmu.2026.1925910`。

**正确写法**：`art.findall("./PubmedData/ArticleIdList/ArticleId")`，并用 `if not doi` 而非直接覆盖。任何引用 `[OA]/[非OA]` 或用 PMCID 取全文的流程，**必须先跑 `repair_ids.py`**。

**坑 2：bioxbio 站内搜索兜底已废弃**

该站搜索页为前端 JS 渲染，服务端返回静态热门列表（全部指向同一本刊），会**静默污染**整个 IF 表。现行策略：期刊 slug 逐个尝试 + 页面归属校验；校验不过一律 `PENDING`。

- 检索块、筛选规则、IF 分层口径见 `references/harvest-protocol.md`。
- 三级阅读深度与结论强度对照见 `references/reading-depth.md`。

---

## 6. 目录约定

```
<PROJECT_DIR>/
├── 00_系统/              训练体系、检索式演进、journal_metrics*.csv、每日自检清单、_verify/、模板/
├── 01_文献库/<周次>/      papers_master.csv、search_log.md、bins_summary.json、D01…D07/
├── 02_前沿快报/           领域前沿研究快报_<周次>_<日期>.docx（周更）
├── 03_语言范式库/         A_地道句式清单.md、B_逻辑衔接范式.md、C_真人写作习惯.md、D_AI腔黑名单.md（累积型，每次训练前必读）
├── 04_IMRAD架构库/        <周次>_IMRAD拆解.md、通用写作框架模板.md（累积升版）
├── 05_仿写训练/<周次>/D0n/ 01_AI训练写作初稿.md、02_写作差异诊断报告.md、03_第1轮修订稿.md、04_第2轮最终修订稿.md
└── 06_进化复盘/           EVOLUTION_LEDGER.md、ERROR_DO_NOT_REPEAT.md、沉淀_<周次>_D0n.md
```

首次使用若目录缺失，按上表创建，并从 `references/templates/` 复制初始文件。**默认项目目录建议为 `~/Documents/SCI-Writing-VIP/`，可在自动化任务中改用其他路径。**

---

## 7. 触发与路由

| 用户说 | 进入 |
|---|---|
| 跑今天的训练 / 每日训练 | 日课 ①→⑦（先建或复用周池） |
| 跑本周文献 / 前沿快报 / 热点 | 检索层 → 周课 ⑧ |
| 解构写作手法 / 句式 / 连接词 | 日课 ②（更新 A~D 四库） |
| IMRAD / 架构拆解 / 框架模板 | 周课 ⑨⑩ |
| 写一段英文练手 | 日课 ④→⑦ |
| 我哪里进步了 / 复盘 | 账本 + 错题本更新 |
| **帮我写/改/润色/审我自己的论文** | **复用模式（见 §8，最高优先）** |

---

## 8. 复用模式 — 处理用户的**真实稿件**（最高优先场景）

**固定动作（顺序不可变）**：

1. **加载积累**：读 `03_语言范式库/A~D` + `04_IMRAD架构库/通用写作框架模板.md` + `06_进化复盘/ERROR_DO_NOT_REPEAT.md`（未标 ✅ 的条目即本次必查项）。
2. **结构诊断**：按框架模板的检查单逐段核对（Introduction 3 段 × 段内功能链 / Methods 四层 / Results 段末边界句 / Discussion 六段链 / 局限段形态）。
3. **句级体检**：
   ```bash
   python3 $SKILL/scripts/style_compare.py --human <同领域真人语料> --mine <用户稿件> --out <诊断.md>
   python3 $SKILL/scripts/anti_ai_check.py --file <用户稿件>
   ```
   把「AI 感」变成数字，而不是形容词。
4. **改写**：改动一律以「**原句 → 修正句 → 依据（引句 + PMID）**」三列返回，便于逐条取舍。
5. **回写**：本次暴露的新 AI 腔形态 → 追加到 `D_AI腔黑名单.md`；新结构问题 → 追加到错题本。

| 场景 | 组合 |
|---|---|
| 写新论文 / 大纲 | 框架模板 → 起草 → 去 AI 味机检 → 10 维度自评 |
| 结构修改 | 框架模板逐段核对 → 出「段落功能缺失表」→ 重排 |
| 润色 / 翻译 | 黑名单逐条排查；三列对照返回 |
| 审稿 | 模拟审稿 → 统计审查 → 证据等级评估 |
| 引文核验 | 多源交叉验证参考文献 |

---

## 9. 可用脚本（`scripts/`）

| 脚本 | 用途 | 节奏 |
|---|---|---|
| `harvest.py` | 文献猎取、初筛、打标、IF 分层、精选（含 `--cache-dir`） | 检索层 |
| `journal_if.py` | 官方 JIF 指标表构建（含页面归属校验） | 检索层 |
| `journal_if_openalex.py` | 用 OpenAlex 代理指标补齐 JIF 缺失（**严格标注，不混称**） | 检索层 |
| `check_if_table.py` | IF 表红线自检（URL slug ↔ journal_iso） | 检索层 |
| `repair_ids.py` | **修复 doi/pmcid/oa 错位**（ArticleIdList 陷阱），输出核对报告 | 检索层（强制） |
| `imrad_scan.py` | IMRAD 结构扫面：按 IF 配额抽样 → 抓 PMC OA 全文 → 统计章节序/段句数/章内句长/子标题/图注 | 周课 ⑨ |
| `daily_pick.py` | 周池 → 按日确定性切分（IF 均衡、不重不漏） | 日课 ⓪ |
| `archive_extract.py` | 阶段① 文献基础归档（摘要级句级抽取） | 日课 ① |
| `extract_language.py` | 阶段② 语言范式原料（按修辞角色分类 + 文体指标） | 日课 ② |
| `style_compare.py` | 样本 A ↔ 样本 B 文体指标对照（AI 腔量化） | 日课 ⑤ / 复用模式 |
| `anti_ai_check.py` | 英文稿 AI 味机检（负面清单，10 分制指数） | 日课 ⑤⑥ |
| `select_for_reading.py` | 按 IF 区间配额抽样阅读清单 | 检索层 |
| `report_md_to_docx.py` | Markdown → Word（保留真表格） | 周课 ⑧ |

### 运行环境

**仅 `report_md_to_docx.py` 需要第三方库**（`python-docx`），其余脚本均为 Python 标准库实现（3.9+ 可运行）。

```bash
python3 -m venv ~/.sci-vip-venv
~/.sci-vip-venv/bin/pip install python-docx
~/.sci-vip-venv/bin/python $SKILL/scripts/report_md_to_docx.py --md <报告>.md --out <报告>.docx
```

> 在 WorkBuddy 环境中，可直接使用隔离环境：
> `~/.workbuddy/binaries/python/envs/default/bin/python`（需已安装 `python-docx`）。

---

## 10. 参考文件

- `references/daily-sop.md` — **日课七阶段逐条 SOP（可直接照做）**
- `references/language-extraction-protocol.md` — 语言范式四类拆分口径 + 样本 A/B 对照方法
- `references/imrad-anatomy-protocol.md` — IMRAD 50 篇扫面 + 2 篇深拆口径，含**已实测的解析陷阱**与 W39 统计基线
- `references/weekly-sop.md` — 周课 SOP
- `references/harvest-protocol.md` — 检索块、筛选规则、IF 分层口径
- `references/reading-depth.md` — 三级阅读深度与结论强度对照
- `references/anti-ai-checklist.md` — AI 味负面清单与机检流程
- `references/writing-craft-taxonomy.md` — 技法分类体系
- `references/templates/` — 归档、诊断报告、快报、IMRAD、复盘、错题本、账本模板
- `docs/PUBLISH.md` — 本技能的打包与发布流程

---

## 11. 进化机制（不可省）

- **每 8 周**输出趋势小结（进步 / 停滞 / 需外部输入）。
- **每周**：记检索式演进（零命中但预期有货的方向补词、噪声大的词降权）→ `00_系统/检索式演进.md`。
- **每日**：错题本未闭环条目必须在当日沉淀中完成「已进入下次自检清单」标记，否则视为未闭环。
- **技法条目**连续 3 轮未被使用 → 标 `待淘汰`（保留，不删）。
- **积累规则**：四库与框架模板**只增不减**；发现更优表述标 `[替代 A-xx]` 并保留旧条。
