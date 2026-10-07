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

> 可持续自我迭代型**生物医药** SCI 科研助手 —— 用真实 PubMed 文献训练「如何表述问题」，而不是套用通用模板。
>
> A self-iterating SCI writing assistant for **biomedical** research (no field restriction — bioinformatics is only one of many). It learns how human scientists frame problems and assert claims from real PubMed literature, instead of applying generic templates.

---

## 这是什么

一个 WorkBuddy / Agent Skill。它把「英文论文写作能力」拆成一套**可重复执行的日循环与周循环**，靠三个机制逼近真人写作水平：

1. **样本 A / 样本 B 对照** —— 样本 A 是 PubMed 真人原文，样本 B 是自己产出的文本。所有诊断都是 A 与 B 的**量化对照**。
2. **累积型知识库** —— 每周的收获落成可复用条目（句式、衔接范式、结构规则、错题），下次训练前先读。
3. **问题表述优先于指标对齐** —— 机器检测的 hedge 密度等分布指标是**次要的**；先看人敢不敢下判断（见下节）。

## 三层取材（v2.4 核心结构）

| 层 | 产物 | 时间窗 / IF | 规模 | 用途 | 硬约束 |
|---|---|---|---|---|---|
| **① 周课主池** | `01_文献库/<周次>/papers_master.csv` | 近 1 年 / 全分层 | ≥500 篇 / 周 | **保量归档**、热点速览 | 10 个检索块覆盖全生物医药；IF 分层不得有 UNBINNED |
| **② 顶刊 reserve 池** | `01_文献库/_顶刊池/papers_toppool.csv` | **近十年 2016–2026** / **IF>20** / 三大顶刊系为主 | ~470 篇 / 已建成 | **日课仿写头号素材源**；学人类如何表述问题；周课深拆候选 | IF 未取到一律 `PENDING`（刊名硬门槛豁免的除外，此时 `if_bin=UNBINNED`，**不得写 IF 数值**） |
| **③ 当日清单** | `01_文献库/<周次>/D0n/` | 同 ① | **≥74 篇 / 日** | 当日七阶段的输入 | 全周并集必须等于池总数，重复 0 篇 |

**两条不可动摇的分工：**

- **保量走 ①，学表述走 ②，二者不可互换。** 不能把「日课全改成 IF>20」字面执行——实测主池 520 篇里 IF>20 只有 11 篇，远低于每日 74 篇的硬要求（其中仅 3 篇有 PMCID）。
- **时间窗不统一，且不可合并：** 周课前沿快报的热点**固定近 2 年**（时间敏感）；顶刊池取近十年（文体敏感，要看断言强度的年代演变）。

## 双层节奏与推送约定

| 节奏 | 内容 | 频率 | 推送 |
|---|---|---|---|
| **日课** | 七阶段：取材 → 归档 → 语言范式提取 → 选材 → 仿写初稿 → 句级差异诊断 → 两轮修订 → 沉淀 | 每日（≥74 篇文献） | **静默**：只落盘，不推送日报 |
| **周课** | 三件套：领域前沿研究快报（Word）＋ IMRAD 架构扫面（50 篇）+ 全文深拆（≤2 篇）＋ 写作框架模板升版 | 每周 1 次 | **《本周热点》**（一页四块） |

**《本周热点》是使用者每周收到的唯一一条消息**，四块内容：① 本周热点 ② 本周练了什么 ③ 新进四库 ④ 短板与下周专项。它单独成页，**不并入 Word 报告**。

## 训练重心：学人类如何表述问题

AI 写作最常见的毛病不是「不地道」，是**太过保守**——数据明明支持，却写成 "may potentially be associated with"。人类学者不会这样。因此诊断的第一维度不是连读率，而是：

| 维度 | 看什么 | 落到哪个库 |
|---|---|---|
| **P1 问题命名** | 首句是否把问题**点名**，还是绕了一圈铺垫 | `C_真人写作习惯` |
| **P2 断言强度** | 结论用 `drives` / `confirms` / `decreased` 还是 `might` / `could` | `C_真人写作习惯` |
| **P3 免责形态** | 免责是**一句**还是连环套（不构成／不等于／宁可不…） | `D_AI腔黑名单` |
| **P4 保守度差** | 自己稿 vs 真人稿的**强度差**，0–3 分打分取均值 | 每日沉淀对比表 |

> ⚠️ **元规则：指标服务于表述，不反过来约束表述。**
> 若 P4 显示过保守，而某个机检指标（如 hedge 密度）显示「达标」——**以 P4 为准**，把 hedge 降下来；
> **不得以「机检已达标」为由回退表述强度。**
>
> 提取顺序也不可颠倒：**问题表述 → 地道句式 → 衔接范式 → 量化基线 → AI 腔黑名单**。

## 领域口径：整个生物医药，不局限生信

取样**不设领域门槛**——生信／组学只是其中一类；药理与药物化学、临床试验与真实世界、动物模型与在体、免疫机制与炎症、分子机制与信号通路、纳米递送、中药与天然产物等同样纳入。落地在 10 个检索块：

| B1 生信核心 | B2 组学测序 | B3 算法建模 | B4 公共数据 | B5 纯生信标志物 |
|---|---|---|---|---|
| **B6 药理与药物化学** | **B7 临床研究与真实世界** | **B8 动物模型与疾病模型** | **B9 免疫机制与炎症** | **B10 分子机制与信号通路** |

- 检索与筛选**必须成对改**：只加检索块不补 `TAGS` 标签，新找回的文章会全部卡在相关性门槛被剔除。
- **生信基本盘保底** `--min-bioinfo-ratio 0.25`：某窗口命中生信核心 13 标签的篇数低于阈值时自动补回（常规窗口实测约 82%，只在异常窗口兜底）。
- 代价：单周候选 6,689 → 10,279（+54%），日课抓取约 4 → 6 分钟。压成本请调 `--max-per-block`，**不要删 B6–B10**。

## 核心特色

- **量化去 AI 味**：把「有点 AI 感」变成可测量的指标 —— 连接词密度、强化词/限制语比、句长分布与标准差、短句占比、AI 模板短语命中数。并提供**章内基线**（引言 24.2 词/短句 16.7%、讨论 23.9/16.5%、方法与结果 21.0/33.4%），按章节对齐而非用单一平均值。
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
└── scripts/            # 20 个脚本，除 report_md_to_docx.py 外全部为标准库实现
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
| 「跑今天的文献训练」 | 日课七阶段全流程（静默执行，只落盘） |
| 「本周热点是什么」 | 周课最先产出《本周热点》一页四块 |
| 「跑本周前沿快报」 | 检索层建周池 → 周课 ⑧ 出 Word 报告（热点固定近 2 年） |
| 「拆解这批论文的 IMRAD 架构」 | 周课 ⑨ 50 篇扫面 + 2 篇全文深拆（**优先从顶刊 reserve 池取**） |
| 「从顶刊池重新建一次 reserve 池」 | `harvest_toppool.py --start 2016/01/01 --end 2026/09/30 --per-year 45` |
| 「帮我看这篇稿子有没有 AI 味」 | 复用模式：加载历史积累 + 双样本量化对照 + 三列改写建议 |
| 「帮我设计这篇论文的大纲」 | 按通用写作框架模板逐段生成 |

**建议首次使用**：先在一个空目录里跑一次「本周文献训练」，让技能建立自己的周池与语言范式库。后续每周的积累会持续叠加。

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
- 训练稿带有「不得投稿」警示块，请勿直接投稿。
- 文献指标（影响因子等）来自第三方聚合站点，**非 JCR 官方导出**，仅供分层参考；代理指标一律明确标注。
- 刊名硬门槛豁免的条目 IF 为 `PENDING`，**引用这批文献时不得写出 IF 数值**。
- 请遵守所在机构与出版方的文献使用与版权规定。

## 许可

MIT License，见 [LICENSE](LICENSE)。变更记录见 [CHANGELOG.md](CHANGELOG.md)。
