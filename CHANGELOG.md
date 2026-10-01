# Changelog

遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.4.0] — 2026-10-01

### 新增
- **三层取材结构**（`SKILL.md` §2.1）：周课主池（近 1 年 / 全 IF / ≥500 篇，保量）→ **顶刊 reserve 池（近十年 2016–2026 / IF>20 / 三大顶刊为主，学表述）** → 今日清单（≥74 篇/日）。
- `scripts/harvest_toppool.py` 与顶刊 reserve 池 `01_文献库/_顶刊池/papers_toppool.csv`（467 篇，逐年 43–45 篇；三大顶刊 Nature 170 / Cell 69 / Science 27 占 57.0%；可全文 55.9%）；`references/harvest-protocol.md` §七「顶刊 reserve 池」。
- **问题表述强度训练**（训练重心）：`references/daily-sop.md` §5-0 的 **P1 问题命名 / P2 断言强度 / P3 免责形态 / P4 保守度差** 四维核验；`references/language-extraction-protocol.md` §〇 规定提取顺序（表述 → 句式 → 衔接 → 量化 → AI 腔黑名单）；`SKILL.md` 立 **L7 铁律**。
- **推送降频**：日课全程静默（不写日报、不弹卡片），《本周热点》为每周唯一推送（`SKILL.md` §2.2 / §7.5、`references/weekly-sop.md`）。
- **训练领域扩至整个生物医药**：`harvest.py` 检索块 5 → **10 块**（B1–B5 生信、B6 药理与药物化学、B7 临床研究与真实世界、B8 动物模型与疾病模型、B9 免疫机制与炎症、B10 分子机制与信号通路）；`TAGS` 补 4 条非生信标签；生信保底 `--min-bioinfo-ratio 0.25`。
- 新脚本：`scripts/count_connectors.py`、`scripts/count_markers.py`、`scripts/extract_prose.py`、`scripts/fetch_pmc_fulltext.py`、`scripts/results_boundary_scan.py`、`scripts/push_skill_to_github.py`。
- `references/deep-dissection-protocol.md`：全文级逐图四问深拆规范（每图 ①解决什么 ②怎么做 ③得到什么 ④链条位置与设计讲究）。
- 错题本扩展至 `ERR-2026W40-46`。

### 修复
- **`Science` 主刊一篇未进池**：`journal_metrics.csv` 缺 Science 条目，缓存中 437 篇 Science 因「IF 未匹配」整批剔除（指令「以三大顶刊为主」被静默违背）。新增 `IF_EXEMPT_JOURNALS` 刊名硬门槛豁免，Science 27 篇入池。
- **生信占比三种口径差一个数量级**（14.8% / 82.2% / 92.6%），用错会反向调参；收敛为「生信核心 13 标签」口径，保底阈值 0.25（实测常规窗口 82.5%，保底不触发）。
- 近两年放大致 2024 年塌陷（22 篇）→ 新增 `--recent-years 3`，恢复至 45 篇。
- 长流程脚本崩在 meta 出口，`toppool_meta.json` 自检字段全缺（CSV 正常，造成虚假完成感）→ `window` 改为由参数直接生成。
- `bin_of` 缺 `>20` 档致 `if_bin` 列零区分度；排序键对空 IF 做 `float('')`。
- 顶刊 white-list 内刊因 IF 表缺失静默消失 → 豁免集扩为白名单全部刊名 + 缩写（65 项）。

### 变更
- 单周候选规模 6,689 → **10,279（+54%）**，日课抓取约 4 → 6 分钟。压成本调 `--max-per-block`，**勿删 B6–B10**。
- 时间窗分工：周课 ⑧ 前沿快报/热点**固定近 2 年**（时间敏感）；日课仿写与表述样本取**近十年**（文体敏感，看十年演变）。
- 新增元规则：**指标服务于表述，不反过来约束表述**（P4 显示过保守时以 P4 为准，不得以「机检已达标」回退表述强度）。

### 已知限制
- 顶刊池内刊名豁免行的 `if_latest` 恒为 `PENDING（刊名硬门槛；未取 IF，未估算）`，`if_bin` 为 `UNBINNED`——**引用这批文章不得写出 IF 数值**。
- 顶刊可全文率 55.9%；`>10` 区间全文可得率仍显著低于主池。
- GitHub 推送需凭据：`push_skill_to_github.py` **默认不 prune**，受保护名单含 `README.md` / `CHANGELOG.md` / `LICENSE` / `.gitignore` / `docs/PUBLISH.md`。

## [2.0.0] — 2026-09-21

### 新增
- **双层节奏**：日课七阶段（每日）＋ 周课三件套（每周），替代原六阶段周循环。
- `scripts/imrad_scan.py` —— IMRAD 结构扫面：按 IF 区间配额抽样 → 抓 PMC OA 全文 → 统计章节序列、章内句长分布、段落句数、子标题句法、图注首句、局限节位置。
- `scripts/repair_ids.py` —— 修复文献池中 `doi` / `pmcid` / `oa` 三列的错位，并输出核对报告。
- `references/daily-sop.md`、`references/language-extraction-protocol.md`、`references/imrad-anatomy-protocol.md`。
- **章内文体基线**：引言 24.2 词 / 短句 16.7%；方法 21.1 / 33.0%；结果 21.0 / 33.7%；讨论 23.9 / 16.5%（n = 32 篇全文）。取代原「摘要基线」单一口径。
- **Results 段末边界句四类模板**（外推 / 设计 / 证据等级 / 统计）。
- 语言范式四库（A 地道句式 / B 逻辑衔接 / C 真人写作习惯 / D AI 腔黑名单），累积型，每次训练前必读。

### 修复
- **`harvest.py` DOI/PMCID 错位**（严重）：`art.findall(".//ArticleIdList/ArticleId")` 会递归命中 `ReferenceList/*/ArticleIdList`（参考文献自身的 DOI/PMCID），且循环赋值使最后一条胜出，导致 `doi`/`pmcid`/`oa` 三列记的是别篇文献的标识。已改为 `./PubmedData/ArticleIdList/ArticleId`，并以 `if not doi` 防止覆盖。
- **`imrad_scan.py` 段落解析**：`sec.findall("./p")` 只取直接子级段落，而多数期刊把 `<p>` 放在子章节内，导致 Methods / Results 章统计样本坍塌（28 → 2）。已改为递归 `.//p` 并跳过容器节点。
- `style_compare.py`：正文提取不再被附录污染（引入 `<!-- APPENDIX -->` 截断），短文本（<60 句）对「连接词种类数 / TTR」设豁免。
- `check_if_table.py`：新增 IF 表页面归属校验（URL slug ↔ journal_iso）。

### 变更
- 日课仿写篇幅由 2500–4000 词全稿改为 **350–500 词片段**（每日一次），全稿改为周课可选。
- 语言范式库由原 `CRAFT_KB.md` 单一文件拆为 A / B / C / D 四份累积文件。
- 词数校验时机由「首稿后」改为「**每轮修订后立即计数**」（原规则导致同一错误一周内复发两次）。

### 已知限制
- 「Results 段末边界句」规则当前仅 1 篇全文证据支撑，需扩至 ≥20 篇验证。
- `>10` 区间全文可得率仅 40%（顶刊多为订阅制），顶刊方法学细节结论强度有限。
- 影响因子来自第三方聚合站点，**非 JCR 官方导出**，仅用于分层参考。

## [1.0.0] — 2026-09-21

### 新增
- 六阶段周循环：S1 文献猎取 → S2 热点解读 → S3 技法解构 → S4 仿写 → S5 复盘 → S6 固化。
- `scripts/harvest.py`（PubMed 猎取 + 初筛 + 打标 + IF 分层 + 精选，含缓存）、`journal_if.py`、`journal_if_openalex.py`、`select_for_reading.py`、`report_md_to_docx.py`。
- 10 维度写作能力评分与 AI 味指数；错题本机制。
