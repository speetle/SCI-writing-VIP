# SCI-writing-VIP

> 可持续自我迭代型生物医学 / 生信 SCI 科研助手 —— 用真实 PubMed 文献训练写作能力，而不是套用通用模板。
>
> A self-iterating SCI writing assistant for biomedical & bioinformatics research. It learns writing craft from real PubMed literature instead of applying generic templates.

---

## 这是什么

一个 WorkBuddy / Agent Skill。它把「英文论文写作能力」拆成一套**可重复执行的周循环**，靠两个机制逼近真人写作水平：

1. **样本 A / 样本 B 对照** —— 样本 A 是 PubMed 真人原文，样本 B 是自己产出的文本。所有诊断都是 A 与 B 的**量化对照**。
2. **累积型知识库** —— 每周的收获落成可复用条目（句式、衔接范式、结构规则、错题），下次训练前先读。

## 双层节奏

| 节奏 | 内容 | 频率 |
|---|---|---|
| **日课** | 七阶段：文献归档 → 语言范式提取 → 英文仿写初稿 → 句级差异诊断 → 两轮强制修订 → 沉淀 | 每日（≥75 篇文献） |
| **周课** | 三件套：领域前沿研究快报（Word）＋ IMRAD 架构拆解（50 篇扫面 + 2 篇全文深拆）＋ 通用写作框架模板升版 | 每周 1 次 |

## 核心特色

- **量化去 AI 味**：把「有点 AI 感」变成可测量的指标 —— 连接词密度、强化词/限制语比、句长分布与标准差、短句占比、AI 模板短语命中数。并提供**章内基线**（引言 24.2 词/短句 16.7%、讨论 23.9/16.5%、方法与结果 21.0/33.4%），按章节对齐而非用单一平均值。
- **结构规则来自统计**：IMRAD 规则不是泛泛而谈，而是从全文实测得出（如 Methods 子标题 99% 为名词短语、Results 子标题在 IF>3 期刊约半数写成论断句、91% 的论文把局限写在 Discussion 正文且平均 9.7 句）。
- **红线可执行**：禁止编造数据与文献；未实测数值必须写 `[TO BE MEASURED]`；IF 抓不到一律 `PENDING` 不估算；官方 JIF 与代理指标严禁混称；交付前强制占位符扫描。
- **真实踩坑记录**：内置两个会导致数据静默错位的陷阱及其修复（PubMed `ArticleIdList` 递归命中参考文献导致 DOI/PMCID 错位；期刊指标站搜索兜底返回静态列表污染整表）。

## 安装

### 方式一：WorkBuddy 技能市场（推荐）

在 WorkBuddy 中打开【技能管理】或【专家 → 技能市场】搜索 `SCI-writing-VIP`，一键安装。

### 方式二：手动安装（任意支持 Agent Skills 的环境）

```bash
git clone https://github.com/<your-name>/SCI-writing-VIP.git
mkdir -p ~/.workbuddy/skills
cp -r SCI-writing-VIP ~/.workbuddy/skills/
```

安装后目录结构应为：

```
~/.workbuddy/skills/SCI-writing-VIP/
├── SKILL.md
├── references/
│   ├── daily-sop.md
│   ├── weekly-sop.md
│   ├── imrad-anatomy-protocol.md
│   ├── language-extraction-protocol.md
│   ├── harvest-protocol.md
│   ├── reading-depth.md
│   ├── anti-ai-checklist.md
│   ├── writing-craft-taxonomy.md
│   └── templates/
└── scripts/            # 13 个脚本，除 report_md_to_docx.py 外全部为标准库实现
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
| 「跑今天的文献训练」 | 日课七阶段全流程 |
| 「跑本周前沿快报」 | 检索层建周池 → 周课 ⑧ 出 Word 报告 |
| 「拆解这批论文的 IMRAD 架构」 | 周课 ⑨ 50 篇扫面 + 2 篇深拆 |
| 「帮我看这篇稿子有没有 AI 味」 | 复用模式：加载历史积累 + 双样本量化对照 + 三列改写建议 |
| 「帮我设计这篇论文的大纲」 | 按通用写作框架模板逐段生成 |

**建议首次使用**：先在一个空目录里跑一次「本周文献训练」，让技能建立自己的周池与语言范式库。后续每周的积累会持续叠加。

## 配置

技能默认在 `~/Documents/SCI-Writing-VIP/` 建立项目目录。若要改路径，在调用时指定，或在自动化任务的 `cwds` 中设定工作目录。

## 免责声明

- 本技能是**写作训练与辅助工具**，不替代研究者的科学判断与署名责任。
- 训练稿带有「不得投稿」警示块，请勿直接投稿。
- 文献指标（影响因子等）来自第三方聚合站点，**非 JCR 官方导出**，仅供分层参考；代理指标一律明确标注。
- 请遵守所在机构与出版方的文献使用与版权规定。

## 许可

MIT License，见 [LICENSE](LICENSE)。
