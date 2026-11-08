# 证据校准与主线写作协议（C5）

> 目的：同时纠正四种相反但常并存的失误——过度防御、无证据断言、偏离主线、重复免责声明。
> 总原则：**实测结果直接写，解释按证据写，猜测标明身份写；结论可以明确，但不得越过对象、设计、终点与时间范围。**

## 一、优先级与不可替代规则

任何写作、改写、诊断和文献解读按以下顺序裁决：

1. 原始数据与原文是否真实支持；
2. 本协议的证据层级、主张类型与范围锁；
3. 主线是否成立；
4. 章节功能与读者判断；
5. 句法、连接词、P4/P2、hedge/booster 等文体指标。

**P4/P2、词频、黑名单和机检均不得反向降低或抬高证据所允许的结论强度。** 真人文本提供可学写法，不自动提供正确结论；仍须核对其研究设计。

### 旧规则冲突裁决

- C-01 的“四重降级”、C-46 的“纯推测句配额”、任何“保留 N 个 hedge/booster”的做法均不得作为目标。
- “D 章 3 档句一律过强”不再作为通用规则。因果证据充分时可以明确写因果；证据不足时，即使只有 1 档也可能越界。
- “集中写 limitation 段”与“禁止独立 limitation 段”都不是普遍规则。由期刊格式和边界是否重复决定。
- 摘要级 P4、断言:推测、免责密度只作文体观察，不能替代本协议的逐主张审查。

## 二、先分四件事：阅读深度、证据强度、主张类型、外推范围

### 2.1 阅读深度不等于证据强度

沿用 `reading-depth.md` 的 L0–L2：

- L0/L1 只能报告标题或摘要实载内容；不得补全 Methods、对照、验证和局限。
- L2 才能依据全文判断证据链是否真正闭合。
- 即使原文结论很强，若本助手只读到摘要，也只能写“摘要报告称……”，不得把未核实的作者结论转写为自己的精读判断。

### 2.2 证据层级 E0–E4

E 级描述的是**针对某一主张的最小证据包**，不是论文整体质量，也不是期刊等级。同一篇论文的不同句子可落在不同层级。

| 层级 | 典型证据 | 允许的最强表述 | 不允许的跃迁 |
|---|---|---|---|
| **E0 未核或未测** | 只有标题、二手转述、检索未命中、摘要未述、未完成实验 | `not reported in the abstract`、`not assessed in this dataset`、`the sources reviewed do not answer whether…` | 把“未找到”写成“没有研究”；把空白写成反向结论；补造方法或数值 |
| **E1 直接观察** | 描述性测量、横断面、单队列、单数据集、无外部验证的计算分析 | `observed`、`measured`、`identified`、`was associated with`、`was higher/lower in <context>`；给效应量、CI、n | `caused/drives`、机制已成立、临床可用、跨人群普适、未验证的 `predicts` |
| **E2 复现或三角验证** | 独立队列、外部验证、正交测量、敏感性分析，仍无干预 | `replicated/validated the association`、`was robust across <tested datasets>`、`supports X as a candidate` | 把一致性当因果；把遗传或统计因果证据自动写成已证分子机制；超出验证人群 |
| **E3 受控功能或干预证据** | 有对照的扰动、回补、随机分组、剂量反应、特异性对照 | 在明确模型与条件内写 `reduced/increased`、`required for` 或 `was sufficient for`；RCT 可写 `improved the prespecified endpoint` | 必要性推出充分性；单细胞系推出人体；单模型推出所有疾病；开放延伸期推出比较疗效 |
| **E4 因果与可迁移性汇合** | 多模型因果链 + 独立复现，或多项高质量临床研究 + 一致外部证据 | `demonstrates/establishes … under the tested conditions`；可向已验证人群与场景做有限推广 | 无限定普遍真理；凭机制研究直接给临床建议；凭单项研究改变指南 |

**E4 不是每篇论文必须追求的目标。** 若研究问题只需 E1 描述，准确完成 E1 比虚假升级到 E3 更好。

### 2.3 主张类型单独核证据

| 主张 | 最低证据要求 | 证据不足时的正确写法 |
|---|---|---|
| 描述与方向 | 直接测量、对象和比较清楚 | `X was higher in A than B in this dataset`；不附加意义尾巴 |
| 关联 | 设计、效应量、CI/统计、混杂处理与范围 | `was associated with`；不写 `independent driver`，除非设计确实支持 |
| 预测 | 锁定模型、适当验证、区分度与校准；临床应用还需外部验证 | 仅内部验证时写 `showed internal discrimination`，不写 `predicts clinical outcomes` |
| 必要性 | 功能缺失 + 表型改变；最好有回补和特异性对照 | 只有敲低时限定方法；不写 `sufficient for` |
| 充分性 | 功能获得或外源补充在相应背景中产生表型 | 只有必要性证据时写 `required for`，不写 `sufficient to drive` |
| 机制链 | 顺序扰动、直接读数、特异性与回补/正交证据 | 富集、共表达、对接、细胞通讯只能生成候选机制 |
| 临床疗效 | 目标人群中的适当对照、预设终点、效应量与随访 | 单臂或开放延伸只报告观察到的应答和持续性，不写比较疗效 |
| 优效或等效 | 直接头对头，或预设且适用的间接比较 | 不做跨试验数值大小比较；写 `provides a benchmark for future direct comparison` |
| 安全性 | 明确不良事件口径、样本量与随访 | `No related grade ≥3 events were observed during <window>`；不写笼统 `safe` |
| 趋势 | 同口径的多个时间点，满足本系统 ≥4 周同向规则 | 单周写 `this week's count`，不写 `increasing/emerging trend` |
| 首创或证据空白 | 可复现的系统检索范围与日期 | `not identified in the sources searched through <date>`；不写绝对 `no studies exist` |

### 2.4 四把范围锁与确定性分开审

每个承重结论必须锁定：

1. **对象**：物种、细胞系、人群、数据集、亚组；
2. **比较**：干预、剂量、对照、分析方法；
3. **终点**：直接测量终点不得换成上位终点；
4. **时间与条件**：随访、疾病阶段、实验环境、验证场景。

确定性词不能修复范围越界。`may improve survival in patients` 仍然越界，如果实验只做了小鼠肿瘤细胞。

## 三、事实、推断、猜测：三种句子三种写法

| 身份 | 判定 | 写法 | 常见错误 |
|---|---|---|---|
| **事实 F** | 原文或本研究直接测得，能定位图、表、数值或原句 | 直接报告，不加 `may/might/could`；保留对象、数值与条件 | 给实测结果加 hedge；把显著性写成重要性 |
| **推断 I** | 由事实推出，但包含作者解释或竞争解释取舍 | 用一个明确标记：`supports`、`suggests`、`indicates`、`is consistent with`、`likely reflects`；紧邻依据 | 连续 `suggest + may + potentially`；把推断写成新事实 |
| **猜测 H** | 当前数据不能判定，用于提出可检验假设 | `we hypothesize/propose`、`one possibility is that`；同句或下一句给可测后果或反证条件 | 无依据地补机制、临床用途、患者获益；用猜测填空白 |

**正文不必给每句加 F/I/H 标签；标签用于审计表。** 最终文本应自然呈现证据关系。

### 证据不足时的标准动作

1. 写清缺的是哪一层：对象、对照、测量、验证、随访还是全文；
2. 写清该缺口影响哪一个推断，而不是否定整项研究；
3. 写清能解除缺口的下一次测量或研究；
4. 若该缺口不影响主线，删除，不单独铺陈。

模板：`The current data establish <limited fact> in <scope>, but do not resolve <specific missing link>; testing <specific design> would distinguish <alternatives>.`

## 四、主线优先：每段必须承重

### 4.1 先钉五个锚点

写作与改稿前写出一行主线：

`主问题 Q → 缺口 G → 设计 A → 关键发现 F → 领域判断 C`

每个段落必须服务其中一个锚点，并完成一种功能：命名问题、建立缺口、说明设计、报告证据、解释证据、限定外推、提出下一步。

### 4.2 五问删除测试

逐段回答：

1. 这段服务 Q/G/A/F/C 中哪一个？
2. 相对前段新增了什么事实、推断或必要边界？
3. 删除后，主结论或研究可复现性是否受损？
4. 是否只是背景展示、方法清单、结果复述、意义升华或自我防御？
5. 若必须保留但会打断主线，是否应移入 Methods、补充材料或 `search_log.md`？

**无锚点 + 无新增信息 = 删除。** 不因“写得很顺”保留。

### 4.3 常见冗余的处置

| 冗余 | 处置 |
|---|---|
| 重复领域背景、通用疾病负担 | 只留能导出缺口的最新一句；其余删除 |
| 文献逐篇罗列 | 按一致、冲突、空白三组压缩；只留改变判断的文献 |
| 方法软件与参数全集进 Introduction/Discussion | 移回 Methods；正文只留决定证据等级的设计 |
| Results 数字在 Discussion 再报一遍 | Discussion 只回收判断；仅保留比较所需数字 |
| 每段末尾重复“这说明很重要” | 删除；每节只在承重处给一次判断 |
| 同一限制在结果、讨论、结论反复出现 | 第一次随主主张写清；后文只在影响改变时回收 |
| 与主问题无关的亚组、机制或临床联想 | 删除或转为一句明确的后续问题，不展开 |

**不得误删**：阴性结果、反向证据、关键对照、影响结论解释的真实边界、必要伦理与合规声明。这些不是废话。

## 五、免责声明与限缩：只保留能改变读者判断的部分

### 5.1 三类边界

| 类型 | 是否保留 | 写法 |
|---|---|---|
| **影响主结论的真实边界** | 必须 | 与受影响的 claims 同段，优先同句；写清缺口及影响 |
| **决定下一步设计的未决问题** | 可保留一次 | 写具体对象、设计、终点和反证条件 |
| **通用免责与自我保护** | 删除 | `further research is needed`、`should be interpreted with caution`、连续 `does not establish/do not imply/cannot exclude` |

### 5.2 单句限缩公式

`Although <specific unresolved factor>, <direct evidence> supports <bounded judgment>.`

或：`<direct result>; however, <specific endpoint/population> was not tested.`

每段最多一个核心限缩。相同的限缩不得在 Abstract、Results、Discussion、Conclusion 中机械重复；各节独立阅读确需保留时，只写该节所需的最短版本。

### 5.3 不属于可删免责声明的内容

训练稿“不得投稿”警示、伦理审批、知情同意、数据可得性、利益冲突、统计不确定性、真实安全风险及期刊强制声明均保留。本协议削减的是**论证中的重复防御**，不是合规信息。

## 六、真实人类样本：从例句到规则

### 6.1 提取时必须成对抄录

每条样本至少包含：

- 证据原句：设计、比较、数值或验证；
- 结论原句：动词、范围、hedge、外推；
- PMID 与章节；
- 本助手阅读深度；
- F/I/H 身份、E 层级、四把范围锁；
- 可迁移规则与不适用范围。

只摘 `suggest/demonstrate` 等动词而不摘证据，不得入库。

### 6.2 本机日课与周课样本给出的可操作证据

| PMID | 真人原文或原文要点 | 可提炼规则 |
|---|---|---|
| 42794653 | `…was associated with increased dementia risk, whereas evidence for PM10 and ozone remained inconclusive.` | 同句区分已见关联与证据不确定；不把 inconclusive 改写成无效或有害 |
| 42759461 | `In vitro experiments further demonstrated that BPA exposure reduced…whereas YY1 overexpression partially restored…` | 扰动与回补支持该体外体系内的功能判断；范围仍限体外条件 |
| 42744774 | `…identifies 11 risk proteins…with four showing causal evidence from colocalization or Mendelian randomization analyses.` | 11 个关联对象与 4 个具因果证据对象分开计数、分开措辞 |
| 42733093 | `Performance drop in external validation…likely reflects population differences…` | 性能下降是事实，人群差异是解释；`likely reflects` 只放在解释层 |
| 42736779 | `The HALP score alone did not show predictive capability (P = .59).` | 阴性结果直接报告，不用“趋势可能提示”捞回结论 |
| 42812379 | `…the cross-sectional decompositions do not establish causal mediation.` | 边界精确指向横断面分解不能支持的因果中介，而非泛称研究不可靠 |
| 42934671 | `Although we cannot formally exclude…, the limited spatial proximity…suggests that they may not be the primary mediators…` | 保留竞争解释，同时根据实测空间邻近度给出有方向的判断；单句完成，不叠加免责 |
| 38128537 | 全文以双向代谢操控、位点定位、功能读数、PDO/PDX 支撑 `lactylation regulates HR` | 多层功能证据允许明确机制动词；仍不自动外推为临床疗效 |
| 39642888 | D-mannose 表型、同位素示踪、OGT 敲除与 rescue、三类 T 细胞产品形成链条 | 必要性由功能缺失与回补闭合；可制造性另由工艺证据支持，不能由机制实验代替 |
| 41429981 | 双盲 sham 对照试验达到预设 ACR20 终点 | RCT 允许直接写 `achieved its primary efficacy endpoint`；开放期数据另行限定，不替代随机比较 |
| 42735488 | `TCGA data confirmed upregulated FGF19…but showed no survival association…` | 同一句承认外部复现的阳性方向，也直接承认预后关联为阴性 |
| 42759982 | `CIPHER shows promise as…but warrants prospective validation before clinical translation.` | 候选工具身份与临床转化门槛各写一次；既不把潜力写成效用，也不层层弱化 |

来源：`03_语言范式库/A~D`、`04_IMRAD架构库/2026-W43_IMRAD拆解.md`、`04_IMRAD架构库/2026-W45_IMRAD拆解.md`、`01_文献库/2026-W45/D01/架构写法拆解_2026-W45_D01.md`。这些例子说明写法，不替代对原文全文的再次核验。

### 6.3 从样本归纳规则的升级门槛

1. **单篇**：只能登记“存在这种写法”，不得升级为普遍规则；
2. **同章型 ≥2 篇**：可形成候选范式，须保留逐篇差异；
3. **跨多篇、跨设计一致**：可形成写法建议，仍须注明适用主张类型；
4. **证据冲突**：优先回到设计与数据，不以多数票决定科学结论；
5. **真人原文自相矛盾或越界**：作为反例保留，不因已发表而照抄。

## 七、日课接入

| 日课环节 | 必做动作 | 产出 |
|---|---|---|
| ① 归档 | 核心结论旁标 E0–E4、depth；摘要未述不补齐 | 归档笔记增加证据层级 |
| ①-b 框架卡 | 快速卡增加“主张类型/E 级/范围锁”；展开卡做证据—结论对照 | 每篇可看出结论是否越界 |
| ①-c 架构卡 | 标每段锚点与功能；识别可删背景、重复结论与重复限缩 | 主线删除清单 |
| ② 语言提取 | 证据句与结论句成对提取；标 F/I/H，不只摘 hedge | 真人证据校准条目 |
| ④ 初稿 | 稿首写主线 Q/G/A/F/C；允许暴露双向强度错误，不设 hedge 配额 | 可诊断初稿 |
| ⑤ 诊断 | 先跑逐主张审查，再做文体比较；双向登记“过强/过弱/范围错位/无据” | `证据校准与主线审查表` |
| ⑥ 修订 | rev1 先修证据和主线，rev2 再修语言；不得为指标改变证据强度 | 两轮独立 diff |
| ⑦ 沉淀 | 记录过强、过弱、无据断言、离线段、重复免责各计数与实例 | 周度进化指标 |

每日最低完成量：

- 全部文献完成快速 E 级与范围锁；
- ≥3 篇完成至少一条完整“证据句 → 结论句”链；
- 训练稿完成逐段五问删除测试；
- 至少 1 个过强和 1 个过弱候选接受人工核查；没有则记 0，不凑数；
- 重复免责声明只保留必要版本。

## 八、周课接入

### ⑧ 前沿快报

每张重要文献卡在“⑤证据与结论”中固定写：

`主张类型｜E 级｜关键证据｜结论原句｜本报告改写｜范围锁｜F/I/H`

“⑥边界”只写会影响结论解释的缺口，不重复 M7，不写通用展望。热点总览按“证据已到哪一步 → 可以做什么判断 → 还缺什么”组织，不以篇数代替成熟度。

### ⑨ IMRAD 与 ⑨-b 叙事论证

- 在 2 篇深拆中各选 ≥3 条承重结论，建立 Claim Ledger；
- 多条文献比较时按主张类型分层，不把 RCT、MR、单细胞、计算筛选放在同一“证据等级”栏简单排序；
- 记录真人如何把事实与解释相邻放置，以及何处直接下判断；
- 识别样本自身的过强结论，不能只选优点。

### ⑩ 模板升版与周度进化

每周只沉淀经样本支持的新规则；记录：

- 过强结论数、过弱结论数、范围锁缺失数；
- 无据推断数、无标记猜测数；
- 删除的离线段数、重复背景/结果/限缩数；
- 保留的必要边界数及各自影响的 claim。

指标用于发现复发，不设“每周必须改出 N 处”的配额。

## 九、真实稿件与交付前验收

真实稿件固定顺序：

1. 写 Q/G/A/F/C 主线；
2. 建 Claim Ledger，逐条核原文和证据；
3. 删除离线段与重复内容；
4. 合并重复限缩，保留真实边界；
5. 再做 C4 三步和语言润色。

交付前必须全绿：

- [ ] 每条承重结论均有 PMID/数据/图表定位；
- [ ] 事实无多余 hedge，推断有依据，猜测有身份与可测出口；
- [ ] 关联未写因果，必要性未写充分性，内部验证未写临床预测；
- [ ] 对象、比较、终点、时间四锁无越界；
- [ ] 明确结论没有被重复免责声明抵消；
- [ ] 每段都能回指主线，删除测试无“无锚点 + 无新增信息”段；
- [ ] 同一背景、结果和限缩未无功能重复；
- [ ] 强制合规与训练警示完整保留。

配套模板：`references/templates/证据校准与主线审查模板.md`。机检脚本 `scripts/claim_audit.py` 只负责定位候选句，E 级、支撑度与最终表述必须人工裁定。
