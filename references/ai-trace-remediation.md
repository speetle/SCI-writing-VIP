# AI 痕迹三步处理协议

> 先生 2026-10-18 指定。三步**顺序固定**：先删空话 → 再统一术语 → 最后核事实。
> 顺序颠倒会白做：句子层面改了词，术语仍漂移；事实仍有幻觉，文字再干净也是废稿。

---

## 第一步：排查“太像标准答案”的段落

### 识别信号（命中 ≥2 条即进入重写）

| # | 信号 | 机器/人工判据 |
|---|---|---|
| 1 | **可删除性**：整段删掉，文章信息量几乎不变 | 删除测试 |
| 2 | **漂亮话密度**：形容词/副词/连接词占比高，实词少 | 抽掉修饰后剩余字数 < 原段 40% |
| 3 | **结构对称**：每段都是“主题句 + 三点支撑 + 小结”，段长接近 | 段长 SD / 均值 < 0.15 |
| 4 | **可预测性**：读完第一句能猜出整段 | 同行盲猜测试 |
| 5 | **无主语论断**：`It is important to note that...` / `There is growing evidence...` | 正则命中 |
| 6 | **万能结论**：换成任何同领域研究都成立 | 替换对象后句子仍通顺 = 不合格 |

### 删除测试（判定动作，不是修辞）

1. 删掉全部形容词、副词、评价性从句、升华句；
2. 数剩下的**有效信息句**（含数字、对象、条件、机制、判断）；
3. **剩 ≤2 句 → 整段重写**；剩 3 句以上 → 保留骨架，只补证据。

### 重写公式（三要素，缺一不合格）

```
具体结果（数字/方向/对象）
  + 依据（图号 / 统计量 / 引用 PMID）
  + 个人判断（这说明什么、边界在哪）
```

**“个人判断”不是主观感受**，是作者对证据的解释强度：`这提示 X 是限速步骤，但本实验无法区分 X 与 Y 的先后`。

### 改写示例（英文）

| 原句（AI 腔） | 改写（三要素） |
|---|---|
| `X plays a crucial role in the progression of Y, and understanding this mechanism is of great importance.` | `X depletion reduced tumour volume by 48% (P = 0.004, n = 8 per group; Fig. 3C), indicating that X sustains growth in this model; whether it acts upstream of Y remains untested.` |
| `Our comprehensive analysis provides valuable insights into the molecular landscape of Z.` | `Of 1,204 differentially expressed genes, 62 clustered in the IL-6/JAK/STAT3 module (FDR < 0.01; Fig. 2A), consistent with a cytokine-driven programme rather than a cell-cycle effect.` |
| `These findings shed light on the potential mechanisms underlying A.` | `The rescue of the phenotype by wild-type X, but not by the catalytically dead mutant, places X activity upstream of A (Fig. 5D).` |
| `It is worth noting that the results were significant.` | `The effect persisted after adjustment for age, sex and stage (HR 1.42, 95% CI 1.11–1.82; Table 2).` |

### 段级验收
- [ ] 每段 ≥1 个**不可替换**的具体信息（数字/对象/条件/机制）
- [ ] 每段至少 1 句能被引用（reviewer 会抄进评审意见的那种）
- [ ] 删除全部 `plays a role` / `provides insight` / `sheds light` / `is important`

---

## 第二步：术语一致性（防研究对象偏移）

### 为什么这是 AI 特有的病
模型为“避免重复”会主动同义替换。替换在文学里是优点，在方法学里是**研究对象被改写**：

| 替换 | 实际后果 |
|---|---|
| `overall survival` → `survival outcomes` | 终点从 OS 变成 OS+PFS 混合 |
| `knockdown` → `silencing` | 干预强度从部分降低变成完全沉默 |
| `patients with stage II–III` → `early-stage patients` | 入组人群被扩宽 |
| `MRG2` → `MRG-2` / `Mrg2` | 检索不到、审稿人质疑基因命名规范 |
| `12-week follow-up` → `short-term follow-up` | 时间窗丢失 |
| `P = 0.04` → `significantly` | 数值被定性词替代 |

### 操作：建“核心术语表”（写作前定，交付前核）

| 术语 | 首次定义位置 | 全文统一写法 | 禁止变体 | 备注 |
|---|---|---|---|---|
| 主变量 | Abstract 第 1 句 | `X`（斜体，基因）/ `X`（正体，蛋白） | `X-α`、`Xα` | 人与小鼠大小写不同 |
| 干预 | Methods 2.1 | `shRNA-mediated knockdown` | `silencing`、`inhibition` | 与 siRNA 区分 |
| 主要终点 | Methods 2.5 | `overall survival (OS)` | `survival`、`survival rate` | 须与统计节一致 |
| 统计口径 | Methods 2.6 | `two-tailed Mann–Whitney U test` | `nonparametric test` | 检验名不得泛化 |

### 五类高危替换（必须人工逐条核）

1. **研究对象**：人群/模型/细胞系/物种名
2. **干预强度**：敲除 / 敲低 / 抑制 / 中和，四者不可互换
3. **终点与指标**：OS / PFS / DFS / ORR；AUC / sensitivity
4. **时间窗与剂量**：`12 weeks` / `3 months`；`10 mg/kg` / `10 mg kg−1`
5. **统计口径**：检验方法、校正方式、效应量类型

### 机器检测

```bash
python3 <skill>/scripts/term_consistency.py --manuscript <稿>.md --out <术语一致性报告>.md
```

输出四类：

| 类别 | 含义 | 处置 |
|---|---|---|
| `VARIANT` | 同一实体的多种写法（大小写/连字符/单复数） | 统一为首次定义写法 |
| `ACRONYM_UNDEF` | 缩写首现未定义，或定义后仍用全称混排 | 补定义或统一 |
| `UNIT_FORM` | 单位/统计写法不一致（`5mg/kg` vs `5 mg/kg`；`P` vs `p`） | 按期刊格式统一 |
| `NUMBER_FORM` | 小数位/千分位/百分号写法不一致 | 统一小数位 |

**脚本只给候选，最终判定必须人工**——领域同形词（如 `lead`、`stage`）会误报。

### 通过判据
- [ ] 术语表每一行在全文只有一种写法
- [ ] 缩写首现定义、此后不再出现全称（除图注可重复一次）
- [ ] 五类高危替换 0 命中
- [ ] 同一数字在 Abstract / Results / 图注 / Discussion 完全一致（含小数位）

---

## 第三步：幻觉排查（引用与结论）

### 三类幻觉

| 型 | 表现 | 检测 | 严重度 |
|---|---|---|---|
| H1 文献不存在 | PMID/DOI 编造，或存在但题名不符 | `ref_verify.py` 存在性核查 | 致命（撤稿级） |
| H2 文献不支持该句 | 文献真实，但结论方向/对象/条件不符 | **必须读原文摘要/全文** | 致命 |
| H3 结论被放大或过度保守 | 相关写成因果；体外写成体内；单模型写成普适；或数据很强却写 `may` | 强度校准表 | 高 |

### 操作流程

```bash
# 1) 抽取 + 存在性核查（PubMed esummary，无需 key）
python3 <skill>/scripts/ref_verify.py --manuscript <稿>.md --out <引用核验>.md

# 2) 逐条读原文（H2 只能人工判定）
#    有 PMCID → scripts/fetch_pmc_fulltext.py --pmcid <PMC…> --dump-md
#    无全文   → 至少读摘要，并在核验表中标注 "abstract-only"
```

### 核验表（每条引用一行）

| # | 引用句（原句） | PMID/DOI | 原文关键句 | 判定 | 处置 |
|---|---|---|---|---|---|
| 1 | 抄录 | 12345678 | 抄录原文 | 支持 / 部分支持 / 不支持 / 反向支持 | 保留 / 降强度 / 换文献 / 删除 |

判定标准：

- **支持**：原文结论方向、对象、条件与引用句一致
- **部分支持**：方向一致但对象或条件不同 → 引用句必须写出限定（`in mice`、`in vitro`）
- **不支持**：删除或替换文献
- **反向支持**：原文结论相反 → 改为对比句（`In contrast to <文献>, ...`），这反而是加分项

### H3 强度校准（双向）

| 证据形态 | 允许的最强表述 | 禁止 |
|---|---|---|
| 观察性关联 | `was associated with` / `co-varied with` | `caused` / `drives` / `leads to` |
| 体外单一细胞系 | `in <cell line>` 限定后可用 `reduced` | 无限定的普适表述 |
| 单一动物模型 | `in <model>` + 边界句 | `in humans` 暗示 |
| 敲低/回补 | `is required for` / `sustains` | `is sufficient for`（未做过表达） |
| 数据强但样本小 | 给效应量与 CI，照写方向 | 用 `may` / `potentially` 连环弱化 |

**过度保守同样是缺陷**：`may potentially suggest that X could perhaps be associated with Y` 会让审稿人质疑作者不信任自己的数据。一个 hedge 足够。

### 通过判据
- [ ] 每条引用都有 PMID/DOI，且 `ref_verify.py` 显示存在
- [ ] 每条引用都读过原文（至少摘要），核验表判定列无空白
- [ ] 不支持 / 反向支持项 0 条（或已改为对比句）
- [ ] H3 校准：无“相关写因果”、无“体外写体内”、无连续双 hedge

---

## 与流程的挂接

| 环节 | 用哪一步 | 产出 |
|---|---|---|
| 日课 ⑤ 诊断 | 第一步 + 第二步 | 段落重写清单、术语漂移清单 |
| 日课 ⑥ 两轮修订 | 三步全跑 | rev2 必须附三步检查记录 |
| 复用模式（真实稿件） | 三步全跑，顺序不变 | `AI痕迹三步报告.md` 随稿交付 |
| 投稿前 | 第二步 + 第三步 | 术语表 + 引用核验表 |

**报告格式**（固定四块）：① 重写段落（原句 → 新句 → 三要素拆解）；② 术语表与变体清单；③ 引用核验表；④ 强度校准改动（原表述 → 校准后 → 依据）。
