# 检索协议（Harvest Protocol）

## 一、时间窗

- 默认：**上一个完整自然周**（周一 00:00 至周日 23:59，按 EDAT）。
- 今天是周一时，用上一周窗口——当周数据尚未入库完整，会产生系统性遗漏。
- EDAT（Entrez Date）= 记录进入 PubMed 的日期，最贴近「本周新出现」。不要用 `[dp]`（出版日期，滞后 1–6 个月）。

## 二、检索块（5 块，OR 关系）

| 块 | 目标 | 核心词 |
|---|---|---|
| B1 生信核心 | 方法学自述 | bioinformatics / computational biology / in silico / systems biology / network pharmacology / molecular docking / molecular dynamics simulation |
| B2 组学测序 | 数据类型 | transcriptom* / RNA-seq / scRNA-seq / single-cell / spatial transcriptom* / proteom* / metabolom* / epigenom* / multi-omics / whole-exome / WGS / metagenom* / microbiome |
| B3 算法建模 | 计算范式 | machine learning / deep learning / AI / random forest / LASSO / WGCNA / nomogram / neural network / foundation model / LLM / Mendelian randomization / radiomics |
| B4 公共数据 | 干实验证据 | GEO / Gene Expression Omnibus / TCGA / GTEx / UK Biobank / ArrayExpress / ICGC / CPTAC / cBioPortal / GEPIA / TIMER / CCLE / GDSC / DepMap / CELLxGENE / publicly available dataset / open dataset |
| B5 纯生信标志物 | 典型产出形态 | differentially expressed genes / hub genes / immune infiltration / prognostic signature / risk score / diagnostic model / co-expression network / pathway enrichment / PPI network / tumor microenvironment / drug target prediction / virtual screening |
| B6 药理与药物化学 | 药物评价 | drug repurposing / pharmacokinetic* / pharmacodynamic* / IC50 / structure-activity relationship / drug design / pharmacophore / bioavailability / dose-response / drug safety / adverse drug / toxicity evaluation |
| B7 临床研究与真实世界 | 临床证据 | randomized controlled trial / double-blind / placebo / prospective cohort / retrospective cohort / case-control study / clinical trial / real-world data / observational study / diagnostic accuracy / sensitivity and specificity |
| B8 动物模型与疾病模型 | 在体证据 | mouse model / murine model / rat model / animal model* / xenograft / knockout mouse / transgenic mouse / disease model / in vivo |
| B9 免疫机制与炎症 | 免疫学 | T-cell activation / cytokine release / macrophage polarization / T helper cell / autoantibod* / vaccine efficacy / antigen presentation / inflammasome / complement activation / innate immune / adaptive immune |
| B10 分子机制与信号通路 | 基础机制 | signaling pathway / molecular mechanism / gene expression regulation / transcription factor / ubiquitin* / autophagy / apoptosis / post-translational modification / protein stability |

后缀统一为 `AND ("<start>"[EDAT] : "<end>"[EDAT]) AND english[lang]`。

> **B6–B10 是 2026-10-01 先生指定「不局限生信，整个生物医药都可以」后新增的。**
> 起因：**原先 B1–B5 全部是生信／组学／算法／公共数据语义 ⇒ 药理、临床、免疫、动物实验类文章根本不进入候选池，
> 任何放宽筛选的改动都无从生效。** 检索块决定候选池，TAGS 决定能否过门槛，两者必须成对审计（见 §六及错题本 `-40` 同源缺陷）。

**相关性门槛（2026-10-01 修正）**：标题+摘要+MeSH 命中任一**生物医药**主题标签（不限生信）才保留；
否则剔除，剔除原因记为「**未识别到生物医药领域信号**」（旧文案「无生信/组学信号」与事实不符，已弃用）。
对应的 4 条非生信标签「药代/药效评价」「临床研究与RCT」「动物模型/在体」「分子机制/信号通路」**必须与 B6–B10 同时存在**，
否则新检索块找回的文章会全卡在门槛上。

**检索式必须与代码一致**：`scripts/harvest.py` 顶部的 `QUERY_BLOCKS` 是唯一真源；报告中的检索式原文直接引用 `search_log.md`，不得手写。

## 三、筛选规则

**排除（非研究性文献）**：Editorial、Comment、Published Erratum、Retraction of Publication、Retracted Publication、News、Biography、Historical Article、Congress、Interview、Personal Narrative、Autobiography、Newspaper Article、Expression of Concern。

**保留**：Journal Article、Review、Systematic Review、Meta-Analysis 等。

**摘要门槛**：≥200 字符（低于此无法做任何实质编码，宁可剔除也不臆测）。

**相关性门槛**：标题+摘要+MeSH 至少命中 1 个生信/组学主题标签，否则剔除。

## 四、排序与精选

```
score = 3×主题标签数 + 2×癌种/疾病标签数
      + {纯生信: 3, 干湿结合: 4, 湿实验为主: 3, 计算/未见数据来源: 1}
      + 2（含算法/工具信号）
      + min(摘要长度/400, 3)
      + IF 层级加成 {>10: 8, 5-10: 6, 3-5: 4, 1-3: 2, UNBINNED: 1}
```

取 top `target`（默认 520，满足「500+」要求）。

> **2026-10-01 调整理由**：旧权重 `{纯生信: 4, 干湿结合: 2}` 会让湿实验类文章在 top520 里系统性靠后，
> 与「整个生物医药都可以」直接冲突。改为**干湿结合最高**（真实写作里既有数据又有结论，最利于学问题表述），
> 纯生信与湿实验为主同档——**先生本人做生信，但训练不应只剩一类**。

**领域配比必须可审计**：产物 `bins_summary.json` 新增两项——

- `"生信信号占比"`：**生信类标签（BIOINFO_TAGS 15 个）命中的篇数 / 入选篇数**。失衡（**生信 >70% 或 <15%**）即告警，说明检索块或权重又漂回去了。
- `"检索块贡献(入选文章)"`：每个检索块对**最终入选文章**的实际贡献篇数（**不是 esearch 命中数**——命中只说明"找得到"，贡献才说明"真进池了"，两者可差很远）。

**生信基本盘保底（防检索漂移）**：入选后若命中生信核心 13 标签的篇数 < `target × --min-bioinfo-ratio`（默认 0.25），
从未入选候选里按 score 补生信文章进来。常规窗口实测生信占比约 **82%**，故该机制**几乎不触发**，只在异常窗口兜底；
`--min-bioinfo-ratio 0` 可关闭。

> ⚠️ **判定口径（三种口径差一个数量级，勿改回）**：同一份实采池（3 天 / target 400）——
> `mode=='纯生信' or public_data=='Y'` → **14.8%**（**低估**：干湿结合的生信稿被算成湿实验）；
> 生信核心 13 标签 → **82.2%**（**采信**）；
> 生信标签全集（+「肿瘤微环境/免疫浸润」「生物标志物/诊断」两个边界标签）→ **92.6%**（**灌水**：湿实验的 biomarker 研究被算生信）。
> 详见错题本 `[ERR-2026W40-46]`。

⚠️ 候选规模代价：新增 5 块后，单周窗口去重候选由 **6,689 → 10,279（+54%）**，日课抓取耗时由约 4 分钟涨到约 6 分钟（3 天窗口实测）。
若需压回成本，优先调 `--max-per-block`（默认 2500），**不要**删 B6–B10。

## 五、IF 分层口径

区间：`<1` / `1-3` / `3-5` / `5-10` / `>10` / `UNBINNED`。

- 取值：`journal_if.py` 抓取 bioxbio.com 的最新年度 IF，写入 `00_系统/journal_metrics.csv`。
- 每一行都带 `if_source_url` 与 `fetch_date`，任何数值可回溯到具体页面。
- **抓不到的期刊标 `PENDING`，其论文标 `UNBINNED`**——不得用「相近期刊」或「记忆中的值」估算。
- 报告须注明：`IF 数据来源：bioxbio.com（聚合站，抓取日 YYYY-MM-DD），非 JCR 官方导出，用于分层参考。`

## 六、干湿实验判定（决定是否「纯生信」）

| 判定 | 条件 |
|---|---|
| **纯生信** | 命中公共数据来源 **且** 未命中湿实验动词 |
| **干湿结合** | 命中公共数据来源 **且** 命中湿实验动词 |
| **湿实验为主** | 命中湿实验动词、未命中公共数据来源 |
| **计算/未见数据来源** | 两者皆未命中（多为方法学或综述） |

湿实验动词表（正则）：`we performed/conducted/established/cultured/transfected/treated/constructed/generated`、`mice were`、`xenograft`、`western blot`、`qRT-PCR`、`immunohistochem*`、`ELISA`、`flow cytom*`、`CCK-8`、`transwell`、`cell line`、`organoid`、`zebrafish` 等。

> ⚠️ 该判定是**基于摘要文本的启发式规则**，不是人工核验结论。报告中须表述为「摘要自动判定」，不得表述为「已核实为纯生信」。

## 七、顶刊 reserve 池（**2026-10-01 新增**，近十年 / IF>20 / 三大顶刊为主）

> **为什么单开一层**：先生 2026-10-01 指定「日常写作训练先从 IF>20 选，范围扩展到近十年，以三大顶刊为主」。
> 但 **W40 实测周课主池 520 篇中 IF>20 仅 11 篇**，远低于日课「每日 ≥74 篇」硬要求
> （11 篇里三大顶刊仅 3 篇、有 PMCID 仅 3 篇）。
> → 因此**不能把日课整体改成 IF>20**，只能**加一层**：**保量走主池，学表述走顶刊池。**

### 7.1 三层分工

| 层 | 时间窗 | IF | 规模 | 用途 |
|---|---|---|---|---|
| 周课主池 | 近 1 年 | 全分层 | ≥500 | 日课保量归档、热点速览 |
| **顶刊 reserve 池** | **2016–2026（近十年）** | **>20** | ~400–500 | **日课 ④ 仿写头号素材**；「人类如何表述问题」样本；周课 ⑨ 深拆候选 |
| 今日清单 | 同主池 | 同主池 | ≥74/日 | 执行单元（由主池轮转切出） |

### 7.2 建池命令

```bash
python3 <skill>/scripts/harvest_toppool.py \
  --out-dir <项目>/01_文献库/_顶刊池 \
  --if-table <项目>/00_系统/journal_metrics.csv \
  --start 2016/01/01 --end 2026/09/30 --per-year 45
```

产出：`papers_toppool.csv`（含 `year` / `pmcid` / `oa` / `if_source_url` 列）+ `toppool_meta.json`。

### 7.3 口径要点

- **期刊白名单**（脚本内 `TOP_JOURNALS`）：三大顶刊体系为主——
  Nature 系（Nature / Nat Med / Nat Genet / Nat Biotechnol / Nat Cell Biol / Nat Cancer / Nat Immunol / Nat Commun）、
  Cell 系（Cell / Cancer Cell / Immunity / Mol Cell / Cell Metab / Neuron / Cell Rep / Cell Stem Cell / Cell Res）、
  Science 系（Science / Sci Adv / Sci Transl Med / Sci Signal / Sci Immunol）；
  外加 12 本生物医学 IF>20 常青刊（Cancer Res / JCO / Gut / Circulation / Eur Heart J / Kidney Int /
  Signal Transduct Target Ther / Mol Cancer / Adv Sci / Nucleic Acids Res / Genome Biol / Autophagy）。
- **IF 硬门槛 `--min-if 20.0`**：IF 表匹配不上（改名/更名）的一律丢弃，标 PENDING 不得估算（R3）。
  **⚠️ 2026-10-01 实测发现的指令级缺口**：`journal_metrics.csv`（973 刊）**没有 `Science` 主刊**，
  于是缓存里 437 篇 Science 全部因「IF 未匹配」被剔，**三大顶刊之一在池里是 0 篇**，
  与先生「以三大顶刊为主」的指令直接冲突。
  → 脚本内增设 **`IF_EXEMPT_JOURNALS`（刊名硬门槛豁免集）**：刊名在集内 ⇒ 即使 IF 表缺失也保留，
  但 **IF 仍写 `PENDING（刊名硬门槛；未取 IF，未估算）`、`if_bin = UNBINNED`、绝不平估或补值**。
  该集合**只放本身即顶刊的刊名**，不含任何"估计它大概 >20"的语义。首批：`Science` / `Cell` / `Nature` 的主刊名。
  **选材时引用这批（现为 27 篇 Science）不得写出 IF 数值。**
- **每年配额 `--per-year 45`**：**近 `--recent-years`（默认 3）年先占满配额**，再回填更早年份——
  服务先生「主要看最新的发现」；[[2016–2023]] 的历史层用于观察**表述风格的年代演变**（见 `language-extraction-protocol.md` §0.5）。
  **⚠️ 不可设回 2**：只放大最近两年会让 2024 掉到 22 篇（其余年份 43–45），
  十年窗内出现中段塌陷，会直接污染"逐年断言强度演变"这条曲线的判读。
- **摘要下限 `--min-abstract 300`**（顶刊摘要普遍长于主池的 200）。
- **排除**：非研究性文献（Editorial/Letter/Comment/News）、预印本。

### 7.4 可全文性（必须如实交代，这是顶刊层的固有短肋）

顶刊多为订阅制。**顶刊 reserve 池中有 `PMCID` 的比例通常显著低于主池**。
- 有 PMCID → 可做**全文级深拆**（逐图四问）；
- 无 PMCID → **只能摘要级训练**（`depth: abstract-only`），**不得写"精读发现"**（R4）。
- **交付说明必须写明「候选中可全文 M/N」**，不得略过。

### 7.5 时间窗不可统一（易错点）

| 用途 | 时间窗 | 依据 |
|---|---|---|
| 周课 ⑧ 前沿快报 / 热点 | **近 2 年** | 先生原话「热点新闻依旧是近两年的」；热点是**时间敏感**的 |
| 顶刊 reserve 池 / 表述训练 | **近十年** | 先生原话「范围扩展到近十年」；表述是**文体敏感**的 |

**把快报也拉到近十年是错的**——会把 2017 年的旧发现当成新进展写进热点。

---

## 八、每周检索式演进

把下列情况记入 `00_系统/检索式演进.md`：
- 某方向「预期有货但命中为 0」→ 补同义词；
- 某词命中大量无关文献（如 microbiome 混入非计算类）→ 加限定（如 `AND (analysis OR sequencing OR bioinformatic*)`）；
- 出现新的研究范式（新算法名、新数据源）→ 新增入 B3/B4。
