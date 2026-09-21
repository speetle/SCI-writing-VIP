# AI 味负面清单与机检流程

## 一、为什么需要前置负面清单

AI 味不是「用词问题」，而是**信息密度与推理方式的问题**：机器写作倾向于用连接词和形容词替代实际论证。因此治理顺序是：先删空话 → 再补论证 → 最后才考虑换词。

## 二、负面清单（写作时默认禁用）

### 1. 套话开头（Delayed-start）
- ✗ `In recent years, X has attracted increasing attention.`
- ✗ `With the rapid development of ...`
- ✗ `X plays an increasingly important role in ...`
- ✓ 直接从具体事实/数字切入：`Between 2015 and 2024, the number of Y increased from A to B.`

### 2. 空洞强调（Empty emphasis）
`plays a crucial role` / `it is worth noting that` / `delve into` / `pave the way for` / `shed light on` / `holds great promise` / `a growing body of evidence`

### 3. 机械连接（Mechanical connectives）
- 相邻两句连用 moreover / furthermore / additionally
- 段落开头一律用 `Furthermore,`
- ✓ 改用**逻辑承接**：`This increase translated into ...` / `Because X, Y ...` / `Consistent with this, ...`

### 4. 伪并列排比
把非并列内容写成 `First..., Second..., Third...`。若三句之间是递进或从属关系，应当用连接性叙述而非编号。

### 5. 无信息量形容词
`novel`（非首创不用）、`significant`（非统计学意义不用）、`comprehensive`、`robust`（未做稳健性检验不用）、`cutting-edge`、`state-of-the-art`（无基准对比不用）、`dramatic`、`profound`

### 6. 同义反复
把结论换个说法再说一遍：`In summary, our findings suggest that X is associated with Y, indicating that X may be related to Y.`

### 7. 过度 hedge
`may potentially suggest that it could be considered to perhaps ...`

### 8. 结尾升华
`This study provides valuable insights and lays a solid foundation for future research.`
→ ✓ 改为具体、可执行的下一步：`Whether Z holds in A requires a prospective cohort with B.`

### 9. 中译英痕迹
`study on X` / `research about X` / `the reason is because` / `it is well known that` / 滥用被动且无施动者

### 10. 列表化滥用
把本应成段的论证拆成 bullet。论文正文中 bullet 仅用于并列的材料/方法清单。

### 11. 三段式对称段落
每段长度几乎一致、每段结构相同（主题句+三支撑+小结）——真人写作段落长度天然不均。

### 12. 无来源的量化
任何百分比、倍数、样本量必须有 PMID / accession / 统计输出出处。

## 三、机检流程（每稿交付前强制）

```
1. 自查         → 逐条过 §二 的 12 条，命中即改
2. 机器检测     → 加载去 AI 味技能（中文：qu-aiwei-zh；英文：humanizer / libai-skill）
3. 记录         → 检测得分写入本周 EVOLUTION_LEDGER
4. 对照         → 命中项写入 ERROR_DO_NOT_REPEAT，必须给「错误句 → 修正句」
5. 复查         → 下一稿起草前，先读上周 ERROR_DO_NOT_REPEAT 全部条目
```

## 四、英文专用补充检查（Chinese-English 痕迹）

- [ ] 冠词使用：`a/the` 是否符合英语学术惯例（首次提及用 a，特指用 the）
- [ ] 时态一致：方法用过去时、结论用现在时、普遍事实用现在时
- [ ] 单复数：`data are`（学术惯例）vs `data is`
- [ ] 悬垂修饰语：分词短语的主语是否与主句主语一致
- [ ] 平行结构：列表项语法形式是否一致
- [ ] 避免 `etc.` 在正式正文中出现

## 五、正向替代库（Prompt Bank）

| 想表达 | 别写 | 改写成 |
|---|---|---|
| 强调重要性 | plays a crucial role | 给出该变量对结果的**具体效应量** |
| 承认前人工作 | Many studies have shown... | `X was shown to Y in <specific model>; however, Z was not examined.` |
| 提出缺口 | Few studies have... | `Whether <本研究的可检验命题> remains untested.` |
| 说明结果显著 | significantly increased | `increased by 42% (P = 0.003)` |
| 总结意义 | provides new insights | `identifies <具体对象> as a candidate <具体用途>` |
| 表达不确定 | may potentially suggest | `is consistent with` |
