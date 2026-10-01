# 同类型生信/医学 SCI 论文通用写作框架模板

> **版本**：v0.1（2026-09-21 建立，**Provisional / 待周课校验**）
> **证据基础**：2026-W39 文献池 520 篇摘要级结构统计（见下方"结构实测"）。**尚未完成** 50 篇 IMRAD 逐段扫描与 2 篇全文深度拆解——该步骤属周课输出，完成后升版为 v1.0 并回溯标注本文中未经验证的推断。
> **使用方式**：可直接用于论文大纲设计与结构修改。凡标 `[待校验]` 的条目，在用于正式稿件前必须由周课深拆结果确认。

---

## 一、结构实测（可溯源）

| 项目 | 实测值 | 来源 |
|---|---|---|
| 样本量 | 520 篇（2026-W39 入选池） | `01_文献库/2026-W39/papers_master.csv` |
| 摘要含结构化标签 | 230 篇（**44%**） | 正则标注统计 |
| 主流标签顺序 | `BACKGROUND > METHODS > RESULTS > CONCLUSIONS`（54 篇）+ 同类变体 | 同上 |
| 平均摘要句数 | **11.3 句**（范围 4–26） | 同上 |
| 平均句长 | **22.6 词**，SD **9.5** | 同上 |
| 句长分布 | ≤15 词 23.0%｜16–20 词 23.6%｜21–25 词 21.7%｜26–30 词 14.1%｜31–35 词 8.7%｜≥36 词 9.0% | 同上 |

> 统计口径提示：`INTRODUCTION` / `PURPOSE` 等标签的位置统计受正文中同名词汇干扰，存在噪声；顺序统计**只作参考**，不作结论。

---

## 二、章节功能框架（v0.1）

### 2.1 Introduction — 五段递进链

| 段 | 功能 | 句数参考 | 真人范式（含 PMID） |
|---|---|---|---|
| ① | 疾病/现象定性：说清"是什么 + 后果" | 1–2 | `X is a leading cause of Y and Z worldwide.`　`PMID 42753319` |
| ② | 已知机制进展：给一个具体机制锚点 | 1–3 | `X is characterized by <特征1>, <特征2>, and <特征3>.`　`PMID 42740387` |
| ③ | 缺口：**必须回答"不知道会损失什么"** | 1–2 | `However, the relationship between A and B remains unclear, limiting its application in C.`　`PMID 42745263`（IF >10） |
| ④ | 本研究目的：**限定语前置**，或先给目的双缺口 | 1 | `We aimed to define the microenvironmental mechanisms underlying X in Y.`　`PMID 42759446`（IF >10） |
| ⑤ | 方法与贡献概览（可选，摘要型论文必写） | 1 | `To address these limitations, we developed ...`　`PMID 42759131`（IF >10） |

**反模式（本系统黑名单）**：①段写成 `X has attracted increasing attention`；③段写成 `Few studies have investigated Y`（无边界、不可证伪）；④段出现 `comprehensively explore the potential mechanisms`（范围放大器）。

### 2.2 Methods — 三层组织

1. **数据层**：数据源 + accession + 样本量 + 纳排标准。真人会写 `n =`、`GSE`/`TCGA-` 编号（`PMID 42750049`：`four independent datasets ... (n = 5132)`）。
2. **分析层**：**"筛选—验证"两段式**是生信论文标准骨架——`<Targets> were screened using <计算手段>, and <实验> were conducted to validate <claim>.`　`PMID 42745263`（IF >10）
3. **统计层**：模型名称 + 软件/版本 + 阈值 + 校正方法。**必写**；软件版本与阈值缺失是最常见的可复现性扣分点。

**避坑点**：
- 工具清单**允许长句并列**（`PMID 42759461` 一句排七个手段），但**禁止**把参数细节塞进摘要；
- 被动与主动的分工：**筛选/分析**常用被动（主语是基因/数据），**设计与决策**用主动（主语是 we）。

### 2.3 Results — 按论证链而非按图表顺序 `[待校验]`

- **叙事顺序**：优先"图 1 → 图 2 → 图 3"若图表本身即论证链；若图表为并列验证关系（如多数据集验证），则按**证据强度递进**叙述。
- **阳性结果**：`<指标> was higher in A than in B (AUC, x.xxx); the adjusted AUC was x.xxx.`　`PMID 42745358` —— 先主轴、再限定、后校正。
- **阴性/失败结果**：**≤25 词 + 给数值 + 不辩解**。`Performance drop in external validation (EXVAL) likely reflects population differences (AUC range: 0.55-0.72).`　`PMID 42733093`（Nat Med）
- **图表与正文分工**：正文**只写结论性数值**，不复述全部数字；并列同类结果压缩成一句（`PMID 42762578` 一句并列四个 HR+CI）。

### 2.4 Discussion — 六段标准链

| 段 | 功能 | 真人范式 |
|---|---|---|
| ① | 主要发现总结（**四重降级**） | `These findings suggest that X may represent a promising candidate ..., warranting further validation.`　`PMID 42737434` |
| ② | 与文献横向对比（一致/不一致） | `<A> <结果A>, whereas <B> <结果B>.`　`PMID 42737434`（矛盾结果直接并列） |
| ③ | 机制解释（**未做因果实验即不许用因果动词**） | `X was also expressed in Y, potentially induced by Z such as A and B.`　`PMID 42748718` |
| ④ | 本研究优势 | `[待校验]`——需 50 篇扫描后给出统计化范式 |
| ⑤ | 局限（**领域级方法学风险，非自贬**） | `Most reported associations ... remain retrospective or exploratory, and their definitions are sensitive to sampling, segmentation, and threshold selection.`　`PMID 42746148` |
| ⑥ | 展望（≥3 个具体待办 or 1 个准入门槛） | `Future studies should prioritize A, B, C, and D before these measures can be incorporated into E.`　`PMID 42750989` |

### 2.5 图表与补充材料 `[待校验]`
待周课 50 篇扫描后补充（图注句式、统计标注规范、补充材料引用方式）。

---

## 三、直接可用的写作检查单（用于先生真实稿件）

- [ ] Introduction ③段是否回答了"不知道这件事会损失什么"？
- [ ] Introduction ④段的限定语是否**收窄**而非**放大**范围？
- [ ] Methods 是否写明软件版本、阈值、校正方法？
- [ ] Results 是否出现 `Moreover` / `In addition`？（应为 0 次）
- [ ] 阴性/失败结果是否 ≤25 词且带数值？
- [ ] Discussion ②段是否用 `whereas` 在句内完成对比？
- [ ] Discussion ⑤段是否避免了 `Our study has several limitations`？
- [ ] Discussion ⑥段是否有 ≥3 个具体待办？
- [ ] 全篇强化词（`novel`/`crucial`/`remarkable`…）是否 ≤1 次且 `novel` 有操作化定义？
- [ ] hedge/booster 比是否 > 1.0？
- [ ] 连接词密度是否低于真人基线（18.3/百句）的 1.4 倍？

---

## 更新日志

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-09-21 | v0.1 | 建立；基于 520 篇摘要结构实测 + D01 语言范式（A/B/C/D 四库 v1.0）。②③⑤⑥ 段已实证，④段与图表部分待周课深拆补齐 |
