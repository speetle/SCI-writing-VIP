# Changelog

遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [2.6.0] — 2026-10-05

### 修复
- **`scripts/report_md_to_docx.py`：加粗区间内嵌行内代码时反引号原样落进 Word。**
  根因：`add_inline()` 只用一条正则切分，`**…**` 分支**只剥外层加粗标记**；当加粗区间内嵌行内代码（如 `**`>5` 占 68.0%**`）时，内层反引号未被处理。
  **潜伏三周未被发现**：W39 / W40 / W41 交付 docx 分别残留 **7 / 28 / 30** 处。
  修法：新增 `_add_runs()`，按反引号切分后逐段设等宽字体，`add_inline()` 改调用它。修复后 **30 → 0、20 → 0**。
  已备份原脚本为 `report_md_to_docx.py.bak-20261005`（**该备份不纳入分发**）。**历史 docx 不追溯重生成。**

### 新增
- **`references/daily-sop.md` §⑦-bis「计分：10 维质量分 ＋ 过程合规性记录位（两者并存，不可互相替代）」**。
  根因修复：此前**两者的关系未写入任何 SOP**，导致周课复盘时把 `沉淀 §九` 的「记录位」（10 项**流程字段**）**误读为替代 10 维计分**，账本写下「不评 10 维」。
  本条以表格写死「管什么 / 计分 / 分母 / 写入位置 / 用途」，并明确：**I/D-only 日 D3 记 N/A → 分母 45**；**逐维合计必须 = 总分**；**误记须明账保留原值 + 标注差异，禁止静默择一**。
  「完成判据」同步增两条勾选项（沉淀 §九 已填、10 维已评且逐维合计 = 总分）。对应错题 `ERR-2026W41-77`。

### 变更
- **⑧-b 精简阅读版篇幅口径定案 = 字节比**（`weekly-sop.md`）：行数比须**同时报出但仅作参考**，分歧时以字节比为准；并固化「**篇幅比须在生成 docx 之前算完**」（`-76`：W41 首版 68.0% 直到交付前才发现）。
- **⑨ 深拆候选加「实测抓取探测」步骤**（`weekly-sop.md` ⑧-c **②-bis**、`imrad-anatomy-protocol.md` 一·第二步）：
  **`pmcid` 非空由「充分条件」降为「必要条件」**——W41 实测候选 **8/16 = 50.0%**（池内标了 PMCID，Europe PMC 未收录完整 XML，返回 HTTP 500）。
  定选前**逐篇跑 `fetch_pmc_fulltext.py` 实测，抓到才定选**；**候选池按目标篇数 2× 准备**。对应错题 `ERR-2026W41-75`。
- **⑨ 候选顺序补记顶刊池口径实测**：顶刊池 `pmcid` 非空 **261/467 = 55.9%** ≥ 20% 阈值 → 「逐图深拆」对第二层**成立**（W40 §7.6 悬置问题关闭），但候选实测成功率仅 50.0%。

### 说明
- 本轮**未改** `SKILL.md`；**未改**任何脚本的判据阈值。
- `-75` / `-76` / `-77` 三条错题**均已做 SOP 根因修复**，非仅补说明。

### 已知限制
- **`scripts/push_repo_to_github.py` 刻意不纳入分发**：该脚本的 `--create` 分支把一篇**未发表课题的题目**作为默认仓库描述硬编码在源码里（`mitoxyperilysis … lower-grade glioma`）。**公开发布会提前泄露未发表选题**，故保留为**本地工具**，远端不含此文件。⚠️ **这不是遗漏，是决定**——勿在下一次同步时"顺手补上"。已由 `push_skill_to_github.py` 的 **`LOCAL_ONLY`** 白名单在代码层拦住。
- **`push_skill_to_github.py` 加两道排除**：① `LOCAL_ONLY`（上一条）；② 文件名含 `.bak` 一律跳过（原 `SKIP_SUFFIX` 只按后缀精确匹配，拦不住 `report_md_to_docx.py.bak-20261005` 这类带日期的备份）。空跑实测：待推文件 **44 → 42**、新增 **2 → 0**。
- **`.gitignore` 的改动不进推送清单**：该文件既受 `PROTECT` 保护、又因是点文件被 `walk_local()` 跳过。本次本地补的 `*.bak-*` / `*.orig` / `*.rej` **远端不会有**——**备份文件的拦截实际由脚本侧的 `.bak` 规则承担**，不依赖 `.gitignore`。
- ⚠️ **GitHub connector 对本仓库只有读权限**（写端点返回 `403 Resource not accessible by integration`）→ **推送仍必须走 `push_skill_to_github.py` + `GH_TOKEN` 通道**。

## [2.5.0] — 2026-10-04

### 变更（分发与权益）
- **许可协议更换**：MIT → 自定义「保留所有权利 + 有限授权」。允许个人非商业使用与原样署名转载；**禁止商业使用、禁止移除/泛化署名、禁止重新打包发布、禁止闭源衍生**。详见新增的 `LICENSE`。
  - ⚠️ MIT 对 **v2.0.0 及更早版本的已分发副本不可撤销**；新协议仅适用于此后发布的版本。
- **署名嵌入三处**：`SKILL.md` 的 frontmatter（`author` / `author_orcid` / `copyright` / `license` / `first_published` / `canonical_source`）、`SKILL.md` 正文顶部署名块、`SKILL.md` 文末署名与许可节；`README.md` 顶部同步。
- **新增 `.gitignore`**：排除 `__pycache__/`、`*.pyc`、`.DS_Store`、凭据类文件与训练产出的本地数据目录。
- **发布前清理**：移除 `scripts/__pycache__/` 缓存（`build_skillhub_pkg.py` 本已排除，此处为源目录同步清理）。

### 说明
- 已核实：SkillHub 上 `@user_4cb21c50/sci-writing-vip`（v2.0.1）与 `dist/_skillhub/SCI-writing-VIP/`（本仓库构建产物）的 `README.md` / `LICENSE.md` / `CHANGELOG.md` 三文件 **sha256 完全一致**，系本作品自行构建发布的版本，非第三方盗用。

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
