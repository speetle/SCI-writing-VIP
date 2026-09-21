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

后缀统一为 `AND ("<start>"[EDAT] : "<end>"[EDAT]) AND english[lang]`。

**检索式必须与代码一致**：`scripts/harvest.py` 顶部的 `QUERY_BLOCKS` 是唯一真源；报告中的检索式原文直接引用 `search_log.md`，不得手写。

## 三、筛选规则

**排除（非研究性文献）**：Editorial、Comment、Published Erratum、Retraction of Publication、Retracted Publication、News、Biography、Historical Article、Congress、Interview、Personal Narrative、Autobiography、Newspaper Article、Expression of Concern。

**保留**：Journal Article、Review、Systematic Review、Meta-Analysis 等。

**摘要门槛**：≥200 字符（低于此无法做任何实质编码，宁可剔除也不臆测）。

**相关性门槛**：标题+摘要+MeSH 至少命中 1 个生信/组学主题标签，否则剔除。

## 四、排序与精选

```
score = 3×主题标签数 + 2×癌种/疾病标签数
      + 4（纯生信）/ 2（干湿结合）
      + 2（含算法/工具信号）
      + min(摘要长度/400, 3)
      + IF 层级加成 {>10: 8, 5-10: 6, 3-5: 4, 1-3: 2, UNBINNED: 1}
```

取 top `target`（默认 520，满足「500+」要求）。

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

## 七、每周检索式演进

把下列情况记入 `00_系统/检索式演进.md`：
- 某方向「预期有货但命中为 0」→ 补同义词；
- 某词命中大量无关文献（如 microbiome 混入非计算类）→ 加限定（如 `AND (analysis OR sequencing OR bioinformatic*)`）；
- 出现新的研究范式（新算法名、新数据源）→ 新增入 B3/B4。
