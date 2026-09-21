# Changelog

遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

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
