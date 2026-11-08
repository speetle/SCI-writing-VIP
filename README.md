# SCI-writing-VIP

> **作者**：连彬（Bin Lian）· ORCID 0000-0002-1477-9137 · drmilo@gkd.edu.cn
> **首发**：2026-09-21 · **源仓库**：https://github.com/speetle/SCI-writing-VIP
> **许可**：个人非商业使用；转载须完整保留本署名；**禁止移除署名、禁止重新打包发布**（见 `LICENSE`）。
>
> © 2026 连彬 (Bin Lian). All rights reserved.

> ⚠️ **历史版本与许可变更 / Version & licence notice**
>
> **v2.0.0 及更早版本以 MIT 协议发布**，该授权对当时已发出的副本**不可撤销**——这些旧版本可被自由再分发，包括商业转售。本人无法回收已发出的 MIT 副本。
> **v2.0.1 及之后所有版本**适用本仓库的 `LICENSE`（个人非商业使用；禁止移除或篡改署名；禁止将作品整体或实质性部分重新打包发布到任何技能市场）。本作品**不在任何技能市场出售**，也从未授权任何第三方转售。
> 请始终使用 `main` 分支的最新版，勿使用旧版本 zip。
>
> Releases up to and including v2.0.0 were published under the MIT License. That grant is irreversible for copies already distributed, so those early versions may be redistributed, including for commercial resale, and cannot be recalled. All versions from v2.0.1 onward are governed by the `LICENSE` file in this repository. This work is not sold on any skills marketplace and no third-party resale has been authorised. Always use the latest `main` branch.

---

> 可持续自我迭代型**生物医药** SCI 科研助手 —— 用真实 PubMed 文献训练“如何表述问题”，而不是套用通用模板。
>
> A self-iterating SCI writing assistant for **biomedical** research (no field restriction — bioinformatics is only one of many). It learns how human scientists frame problems and assert claims from real PubMed literature, instead of applying generic templates.

---

## 这是什么

一个 WorkBuddy / Agent Skill。它把“英文论文写作能力”拆成一套**可重复执行的日循环与周循环**，靠三个机制逼近真人写作水平：

1. **样本 A / 样本 B 对照** —— 样本 A 是 PubMed 真人原文，样本 B 是自己产出的文本。所有诊断都是 A 与 B 的**量化对照**。
2. **累积型知识库** —— 每周的收获落成可复用条目（句式、衔接范式、结构规则、错题），下次训练前先读。
3. **证据与主线优先于指标对齐** —— 机器检测的 hedge 密度等分布指标是**次要的**；先核对证据能支持什么判断，再看人如何表述，最后删除不服务主线的铺垫与重复免责（见下节）。

## 三层取材（v2.4 核心结构）

| 层 | 产物 | 时间窗 / IF | 规模 | 用途 | 硬约束 |
|---|---|---|---|---|---|
| **① 周课主池** | `01_文献库/<周次>/papers_master.csv` | 近 1 年 / 全分层 | ≥500 篇 / 周 | **保量归档**、热点速览 | 10 个检索块覆盖全生物医药；IF 分层不得有 UNBINNED |
| **② 顶刊 reserve 池** | `01_文献库/_顶刊池/papers_toppool.csv` | **近十年 2016–2026** / **IF>20** / 三大顶刊系为主 | ~470 篇 / 已建成 | **日课仿写头号素材源**；学人类如何表述问题；周课深拆候选 | IF 未取到一律 `PENDING`（刊名硬门槛豁免的除外，此时 `if_bin=UNBINNED`，**不得写 IF 数值**） |
| **③ 当日清单** | `01_文献库/<周次>/D0n/` | 同 ① | **≥74 篇 / 日** | 当日七阶段的输入 | 全周并集必须等于池总数，重复 0 篇 |

**两条不可动摇的分工：**

- **保量走 ①，学表述走 ②，二者不可互换。** 不能把“日课全改成 IF>20”字面执行——实测主池 520 篇里 IF>20 只有 11 篇，远低于每日 74 篇的硬要求（其中仅 3 篇有 PMCID）。
- **时间窗不统一，且不可合并：** 周课前沿快报的热点**固定近 2 年**（时间敏感）；顶刊池取近十年（文体敏感，要看断言强度的年代演变）。

## 双层节奏与推送约定

| 节奏 | 内容 | 频率 | 推送 |
|---|---|---|---|
| **日课** | 七阶段：取材 → 归档 → 语言范式提取 → 选材 → 仿写初稿 → 句级差异诊断 → 两轮修订 → 沉淀 | 每日（≥74 篇文献） | **静默**：只落盘，不推送日报 |
| **周课** | 三件套：领域前沿研究快报（Word）＋ IMRAD 架构扫面（50 篇）+ 全文深拆（≤2 篇）＋ 写作框架模板升版 | 每周 1 次 | **《本周热点》**（一页四块） |

**《本周热点》是使用者每周收到的唯一一条消息**，四块内容：① 本周热点 ② 本周练了什么 ③ 新进四库 ④ 短板与下周专项。它单独成页，**不并入 Word 报告**。

## 训练重心：学人类如何表述问题

AI 写作最常见的毛病不是“不地道”，是**太过保守**——数据明明支持，却写成 "may potentially be associated with"。人类学者不会这样。因此诊断的第一维度不是连读率，而是：

| 维度 | 看什么 | 落到哪个库 |
|---|---|---|
| **P1 问题命名** | 首句是否把问题**点名**，还是绕了一圈铺垫 | `C_真人写作习惯` |
| **P2 断言强度** | 结论用 `drives` / `confirms` / `decreased` 还是 `might` / `could` | `C_真人写作习惯` |
| **P3 免责形态** | 免责是**一句**还是连环套（不构成／不等于／宁可不…） | `D_AI腔黑名单` |
| **P4 保守度差** | 自己稿 vs 真人稿的**强度差**，0–3 分打分取均值 | 每日沉淀对比表 |

> ⚠️ **元规则：指标服务于表述，不反过来约束表述。**
> 若 P4 显示过保守，而某个机检指标（如 hedge 密度）显示“达标”——**以 P4 为准**，把 hedge 降下来；
> **不得以“机检已达标”为由回退表述强度。**
>
> 提取顺序也不可颠倒：**问题表述 → 地道句式 → 衔接范式 → 量化基线 → AI 腔黑名单**。

## 领域口径：整个生物医学（生物医药），不局限生信

取样**不设领域门槛**——覆盖整个生物医学／生物医药，生信／组学只是其中一类；药理与药物化学、临床试验与真实世界、动物模型与在体、免疫机制与炎症、分子机制与信号通路、神经、心血管、纳米递送、中药与天然产物、疫苗等同样纳入。落地在 10 个检索块：

| B1 生信核心 | B2 组学测序 | B3 算法建模 | B4 公共数据 | B5 纯生信标志物 |
|---|---|---|---|---|
| **B6 药理与药物化学** | **B7 临床研究与真实世界** | **B8 动物模型与疾病模型** | **B9 免疫机制与炎症** | **B10 分子机制与信号通路** |

- 检索与筛选**必须成对改**：只加检索块不补 `TAGS` 标签，新找回的文章会全部卡在相关性门槛被剔除。
- **生信基本盘保底** `--min-bioinfo-ratio 0.25`：某窗口命中生信核心 13 标签的篇数低于阈值时自动补回（常规窗口实测约 82%，只在异常窗口兜底）。
- 代价：单周候选 6,689 → 10,279（+54%），日课抓取约 4 → 6 分钟。压成本请调 `--max-per-block`，**不要删 B6–B10**。

## 五项核心能力（C1–C4 于 v2.7 建立，C5 于 v2.10 新增）

| 能力 | 什么时候用 | 做什么 | 协议 |
|---|---|---|---|
| **C1 论文框架拆解** | 每日读文献 | 逐篇拆**研究框架（F1–F7）/ 叙事逻辑（F8：N1–N4 排法）/ 论证闭环（F9：缺口→设计→结果→讨论回指）**：作者如何构思、如何让逻辑自洽、用什么方法讲清了什么问题。三问均须给位置（摘要原句、图号）。当日 ≥74 张 **9 字段**快速卡 ＋ ≥3 张展开卡（含“叙事替选”），按 P1–P8 八种论证原型归档，并统计三类闭环断链 | `references/framework-dissection-protocol.md` |
| **C2 分部写法拆解** | 写稿、改稿、拆他人文章 | 摘要 / 引言 / 方法 / 结果 / 讨论 / 结论 / figure legend / table / cover letter 各部位的结构、行文逻辑、写法套路、图表布局与自检；引言按漏斗四步法；与每日操练逐项对比连接词、句长比例、信息密度、啰嗦废话、结论强度和图文关系；归纳真人写 SCI 方法 | `references/section-playbooks.md` + `references/architecture-writing-system.md` |
| **C3 顶刊叙事与论证标准** | 选题评估、大纲、Discussion 重写、投稿前 | 三把尺子打分（**现实痛点 / 理论进展 / 关键机制**，6 分制）＋ **故事质量四问**（透彻 / 可信 / 有启发性 / 为什么值得解决，四问全过才算顶刊级）；多篇对比扫描判“已解决透彻 / 仍存空白 / 结论矛盾”（矛盾处须给可检验的区分假设）；**Gap Ledger** 保证引言→方法→结果→讨论闭环；**Figure Ledger** 逐图六问：支撑哪句 / 为何此图型 / 为何在此位置 / 证明什么 / 不能证明什么 / 与前后图关系 | `references/narrative-argument-standard.md` |
| **C4 AI 痕迹三步** | 每次修订、每份真实稿件 | ①删漂亮话后剩 ≤2 句有效信息的段落，按**具体结果＋依据＋个人判断**重写；②核心变量/方法/指标**从头到尾叫法一致**，纠正同义替换导致的研究对象偏移；③**逐条读原文**核文献真实存在且确实支撑，并校准结论放大或过保守 | `references/ai-trace-remediation.md` |
| **C5 证据校准与主线写作** | 日课、周课、写稿改稿、投稿前 | 将阅读深度 L0–L2 与具体主张的证据包 E0–E4 分开；按描述、关联、预测、必要性、充分性、机制、疗效、安全性等主张类型审查最低证据；用对象、比较、终点、时间四把范围锁限制外推；区分事实 F、推断 I、猜测 H；以 Q/G/A/F/C 主线和逐段五问删除离题冗余；真实边界随主张写一次，通用免责删除，合规声明保留 | `references/evidence-calibration-protocol.md` + `references/templates/证据校准与主线审查模板.md` |

### 证据强度如何约束结论强度（v2.10 新增）

C5 同时纠正“过度防御”和“无据断言”：直接测量结果不叠加 `may/might/could`；关联不写成因果，内部验证不写成临床预测，必要性不写成充分性；推断只用一个明确标记并紧邻依据，猜测须标身份并给出可测后果或反证条件。证据不足时写清缺失的是对象、对照、测量、验证、随访还是全文，以及它影响哪一条判断，而不是用通用免责兜底。

规则来自本机日课与周课的 12 组真人 PMID 证据—结论对照，包括体外扰动与回补、RCT 预设终点、外部验证、横断面因果边界和阴性预测结果。真人样本只提供写法证据，不自动等于正确结论；单篇不得直接升级为普遍规则。

### 周课 Word 快报的解读规格（v2.8 改，v2.10 校准）

快报**不是文献计量报告**，只解读重要文献，且每篇按固定七块拆：

> ① 采用什么方法　② 解决了什么问题　③ 弥补了什么空白（G1–G5）　④ **方法学体系 M1–M7**　⑤ 证据与结论（主张类型、E 级、证据句、结论句、四把范围锁、F/I/H）　⑥ 影响结论的具名边界　⑦ 可迁移写法

方法学体系七层：**M1 研究设计 / M2 对象与样本 / M3 数据与测量 / M4 分析或实验链条 / M5 验证策略 / M6 统计与判据 / M7 边界与失效条件**，外挂一行“方法-问题映射（因果/相关/外推，充分/超配/欠配）”。缺层、或摘要未述却推断，均判不合格。

**篇幅**：正文 ≤8 页 / ≤6500 字，热点 3–5 个，解读 3–8 篇（每热点 1–2 篇），宁少不凑。**强制删除**：IF 区间分布全表、研究模式构成表、剔除统计、方法学趋势宽表、纯生信选题独立章、写作观察独立章、检索式全文附录。保留红线：PMID 与 IF、JIF 与代理不混称、摘要级不写成精读。

配套机检（只给候选，判定必须人工）：

```bash
python3 scripts/term_consistency.py --manuscript 稿.md --out 术语一致性.md
python3 scripts/ref_verify.py      --manuscript 稿.md --out 引用核验.md
python3 scripts/claim_audit.py     --manuscript 稿.md --out 证据校准机检.md
```

- `term_consistency.py`：同一实体多写法 / 缩写未定义 / 单位与 P 值写法 / 高危词族混用（knockdown vs silencing、OS vs survival outcomes…）。
- `ref_verify.py`：抽 PMID/DOI → PubMed E-utilities 核存在性 → 引用句与原文实词重叠度提示（<0.15 标“必读原文”）。
- `claim_audit.py`：定位连续 hedge、因果/预测主张、通用展望、空泛意义句、重复免责和“数字+弱化”候选句；不判断研究设计、E 级、引用支撑度或结论正误，每条必须人工裁决。

### 论文架构与各部分写法（与每日操练并列）

`references/architecture-writing-system.md` 与 `references/templates/架构写法拆解模板.md` 是新增的并列训练模块：逐篇覆盖 Abstract、Introduction、Methods、Results、Discussion、Conclusion、Figure legend、Table；拆解整篇闭环、图表排版布局，并将真人论文与每日训练稿按连接词、章内句长比例、啰嗦废话、结论强度、图文关系逐项对照。每日执行全篇架构卡 ≥74 篇、≥3 篇各部分写法卡、≥1 段 A/B 对照；摘要级不推断全文方法与图表布局。

- **量化去 AI 味**：把“有点 AI 感”变成可测量的指标 —— 连接词密度、强化词/限制语比、句长分布与标准差、短句占比、AI 模板短语命中数。并提供**章内基线**（引言 24.2 词/短句 16.7%、讨论 23.9/16.5%、方法与结果 21.0/33.4%），按章节对齐而非用单一平均值。
- **结构规则来自统计**：IMRAD 规则不是泛泛而谈，而是从全文实测得出（如 Methods 子标题 99% 为名词短语、Results 子标题在 IF>3 期刊约半数写成论断句、91% 的论文把局限写在 Discussion 正文且平均 9.7 句）。
- **红线可执行**：禁止编造数据与文献；未实测数值必须写 `[TO BE MEASURED]`；IF 抓不到一律 `PENDING` 不估算；官方 JIF 与代理指标严禁混称；交付前强制占位符扫描。
- **真实踩坑记录**：内置若干会导致数据静默错位的陷阱及其修复（PubMed `ArticleIdList` 递归命中参考文献导致 DOI/PMCID 错位；期刊指标站搜索兜底返回静态列表污染整表；**刊名白名单里的期刊因 IF 表缺条目而整批静默消失**；**占比类指标用错判定口径会指向反向决策**；长任务崩溃点恰好落在 meta 出口）。

## 安装

### 方式一：WorkBuddy 技能市场（推荐）

在 WorkBuddy 中打开【技能管理】或【专家 → 技能市场】搜索 `SCI-writing-VIP`，一键安装。

### 方式二：手动安装（任意支持 Agent Skills 的环境）

```bash
git clone https://github.com/speetle/SCI-writing-VIP.git
mkdir -p ~/.workbuddy/skills
cp -r SCI-writing-VIP ~/.workbuddy/skills/
```

安装后目录结构应为：

```
~/.workbuddy/skills/SCI-writing-VIP/
├── SKILL.md
├── README.md
├── CHANGELOG.md
├── references/
│   ├── daily-sop.md
│   ├── weekly-sop.md
│   ├── imrad-anatomy-protocol.md
│   ├── language-extraction-protocol.md
│   ├── harvest-protocol.md
│   ├── deep-dissection-protocol.md
│   ├── reading-depth.md
│   ├── anti-ai-checklist.md
│   ├── writing-craft-taxonomy.md
│   └── templates/
└── scripts/            # 25 个脚本，除 report_md_to_docx.py 外全部为标准库实现
```

**依赖**：Python 3.9+。仅 `scripts/report_md_to_docx.py` 需要 `python-docx`：

```bash
python3 -m venv ~/.sci-vip-venv
~/.sci-vip-venv/bin/pip install python-docx
```

## 使用

安装后直接用自然语言触发：

| 你说 | 它做什么 |
|---|---|
| “跑今天的文献训练” | 日课七阶段全流程（静默执行，只落盘） |
| “本周热点是什么” | 周课最先产出《本周热点》一页四块 |
| “跑本周前沿快报” | 检索层建周池 → 周课 ⑧ 出 Word 报告（热点固定近 2 年） |
| “拆解这批论文的 IMRAD 架构” | 周课 ⑨ 50 篇扫面 + 2 篇全文深拆（**优先从顶刊 reserve 池取**） |
| “从顶刊池重新建一次 reserve 池” | `harvest_toppool.py --start 2016/01/01 --end 2026/09/30 --per-year 45` |
| “帮我看这篇稿子有没有 AI 味” | 复用模式：加载历史积累 + C5 证据与主线审查 + 双样本量化对照 + 三列改写建议 |
| “结论是不是太保守或太绝对，废话和免责声明太多” | C5：Claim Ledger + E0–E4 + 四把范围锁 + F/I/H + 主线五问删除测试 |
| “帮我设计这篇论文的大纲” | 按通用写作框架模板逐段生成 |

**建议首次使用**：先在一个空目录里跑一次“本周文献训练”，让技能建立自己的周池与语言范式库。后续每周的积累会持续叠加。

## 配置

技能默认在 `~/Documents/SCI-Writing-VIP/` 建立项目目录。若要改路径，在调用时指定，或在自动化任务的 `cwds` 中设定工作目录。

本仓库的同步脚本可直接复用到别的 skill：`scripts/push_skill_to_github.py` 走 GitHub Git Data API，
**默认不 prune**（远端有、本地无的文件不删），仓库自有文件（README / CHANGELOG / LICENSE / docs / .gitignore）在保护名单内，
推送前打印差异清单，逐文件 sha 比对校验。用法：

```bash
export GH_TOKEN=ghp_xxx
python3 scripts/push_skill_to_github.py \
  --skill ~/.workbuddy/skills/SCI-writing-VIP \
  --repo speetle/SCI-writing-VIP \
  --msg "feat: v2.4 — 三层取材 + 问题表述训练 + 领域扩至全生物医药"
```

## 免责声明

- 本技能是**写作训练与辅助工具**，不替代研究者的科学判断与署名责任。
- 训练稿带有“不得投稿”警示块，请勿直接投稿。
- 文献指标（影响因子等）来自第三方聚合站点，**非 JCR 官方导出**，仅供分层参考；代理指标一律明确标注。
- 刊名硬门槛豁免的条目 IF 为 `PENDING`，**引用这批文献时不得写出 IF 数值**。
- 请遵守所在机构与出版方的文献使用与版权规定。

## 许可

个人非商业使用；再分发须完整署名，禁止重新打包发布，见 [LICENSE](LICENSE)。v2.0.0 及更早已发出副本仍适用其当时的 MIT 授权，详见文首“历史版本与许可变更”。变更记录见 [CHANGELOG.md](CHANGELOG.md)。
