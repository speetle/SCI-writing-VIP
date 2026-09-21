# 打包与发布指南

> 本文说明如何把本技能分发出去：GitHub 开源、腾讯 SkillHub（国内技能市场）、以及 WorkBuddy 应用内市场。
>
> ⚠️ 各平台的发布入口与审核政策会变动。本文记录的是 2026-09 的公开流程，**执行前请以平台官网当前说明为准**。

---

## 一、发布前必做：脱敏与规范检查

### 1.1 脱敏检查

技能包里**不能**包含：

- 个人绝对路径（`/Users/<name>/...`、`C:\Users\<name>\...`）
- 真实姓名、单位、邮箱、学生姓名等个人身份信息
- 文献池数据、IF 指标表、生成的 Word/PDF、任何缓存目录
- API key、token、cookie

自检命令（在技能根目录执行）：

```bash
# 个人路径
grep -rnE "/Users/[a-zA-Z0-9_.-]+|C:\\\\Users" . --include="*.md" --include="*.py" || echo "✅ 无个人路径"

# 真实姓名（按需替换）
grep -rn "你的姓名\|你的单位" . || echo "✅ 无身份信息"

# 敏感信息
grep -rniE "api[_-]?key|token|password|secret" . --include="*.md" --include="*.py" || echo "✅ 无凭据"

# 不应打包的数据目录
find . -type d \( -name "_cache" -o -name "_pool" -o -name "_verify" -o -name "dist" \) | grep . && echo "⚠️ 发现数据目录，打包前删除" || echo "✅ 无数据目录"
```

### 1.2 元数据规范（重要）

Agent 的技能自动发现**只识别 frontmatter 白名单键**：

| 键 | 必填 | 说明 |
|---|---|---|
| `name` | ✅ | 技能名，建议与目录名一致 |
| `description` | ✅ | **超过 1024 字符会被静默丢弃**，务必控制长度 |
| `when_to_use` | 建议 | 触发场景与关键词，显著提升被正确调用的概率 |
| `license` | 建议 | 如 `MIT` |
| `metadata` | 可选 | 如 `emoji`、`requires.bins`、`requires.python` |
| `agent_created` | ✅ | 必须为 `true`，否则后续无法用技能管理工具修改 |

**常见致命错误**：把 `version` / `author` / `category` / `tags` 等键直接写在 frontmatter 顶层。这些键不在白名单内，会导致自动发现失败。正确做法是移到正文的「元数据归档」区块，或放进 `metadata` 下。

校验：

```bash
python3 - <<'PY'
import re,sys
t=open('SKILL.md',encoding='utf-8').read()
m=re.match(r'^---\n(.*?)\n---\n', t, re.S)
if not m: sys.exit('❌ 缺少 frontmatter')
fm=m.group(1)
d=re.search(r'^description:\s*(.*?)(?=^\w+:|\Z)', fm, re.S|re.M)
n=len(d.group(1).strip()) if d else 0
print('description 字符数:', n, '✅' if n<=1024 else '❌ 超过 1024，会被丢弃')
for k in ('name','description','agent_created'):
    print(('✅' if re.search(r'^%s:'%k, fm, re.M) else '❌ 缺少'), k)
PY
```

### 1.3 安全自检

技能会执行 Python 脚本并访问网络（NCBI E-utilities、期刊指标站、OpenAlex）。发布前请确认：

- 所有网络请求的目标域名在 `SKILL.md` 或 README 中明示
- 脚本不做高危系统操作（无 `rm -rf`、无写入用户家目录之外的位置）
- 无硬编码凭据
- 脚本可在无网络的降级场景下给出明确错误而非静默失败

---

## 二、打包

技能包结构（`SKILL.md` 必须在**压缩包的根目录**）：

```
SCI-writing-VIP/
├── SKILL.md          ← 必须存在，且带合规 frontmatter
├── README.md
├── LICENSE
├── CHANGELOG.md
├── .gitignore
├── docs/PUBLISH.md
├── references/
└── scripts/
```

打包命令：

```bash
cd <包含 SCI-writing-VIP 目录的父目录>
zip -r SCI-writing-VIP-v2.0.0.zip SCI-writing-VIP \
  -x "*/_cache/*" "*/_pool/*" "*/__pycache__/*" "*.pyc" "*.docx" "*.csv" ".DS_Store"
unzip -l SCI-writing-VIP-v2.0.0.zip | head -20   # 确认 SKILL.md 在根
```

---

## 三、发布到 GitHub（全球可见）

### 3.1 建仓

```bash
cd SCI-writing-VIP
git init
git branch -M main
git add .
git commit -m "feat: SCI-writing-VIP v2.0.0 — 双层节奏的 SCI 写作进化训练技能"
git remote add origin https://github.com/<your-name>/SCI-writing-VIP.git
git push -u origin main
```

### 3.2 让仓库更容易被发现

- **仓库简介（About）**写清一句话定位：
  > Self-iterating SCI writing assistant. Trains writing craft on real PubMed literature with quantified anti-AI-tone diagnostics. 生物医学/生信 SCI 写作进化训练技能。
- **Topics**：`agent-skills` `skill` `sci-writing` `academic-writing` `bioinformatics` `pubmed` `research-tools` `ai-writing` `workbuddy`
- **打 Tag 发 Release**，把 zip 作为 release asset 上传，便于他人直接下载：
  ```bash
  git tag -a v2.0.0 -m "v2.0.0"
  git push origin v2.0.0
  gh release create v2.0.0 SCI-writing-VIP-v2.0.0.zip --notes-file CHANGELOG.md
  ```
- **README 首屏给出安装命令**，不要让读者翻到第三屏才找到怎么装。

---

## 四、发布到腾讯 SkillHub（国内分发）

SkillHub 是腾讯的技能市场（`skillhub.tencent.com` / `skillhub.cn`），也是 WorkBuddy 应用内技能市场的主要来源。

### 4.1 前置

- 注册并登录账号
- **完成实名认证**（国内发布强制）
- 平台会对每个技能执行**三线并行安全审核**：内容合规过滤 → 科恩实验室深度漏洞扫描 → 云鼎实验室 AI 模型安全评估。全部通过才自动上架，任一不通过即拒绝。

### 4.2 方式 A：网页上传

1. 进入官网 → 技能发布页面
2. 填写技能信息：名称、版本（语义化 `x.y.z`）、分类、标签、支持平台
3. 上传 zip 包（结构见 §二）
4. 提交审核 → 等待审核结果

### 4.3 方式 B：CLI

```bash
# 登录（OAuth，凭据存到 ~/.skillhub/auth.json）
skillhub login

# 初始化（若从零开始）
skillhub init --name SCI-writing-VIP --category 效率工具

# 推送文件（先进入草稿状态，不会立即上架）
skillhub push

# 提交发布（触发安全审核，通过后自动上架）
skillhub publish
```

**可见性**可通过 `--visibility` 控制：`public`（公开）／`unlisted`（不在列表展示）／`private`（私有）／`org`（组织内可见）。

### 4.4 提高过审与下载量的建议

- **命名避免重名**，建议 `作者名-技能功能` 形式
- **description 写清用途 + 触发词 + 使用示例**，长度控制在 1024 字符内
- **脚本最小权限**，不做高危系统操作，不硬编码密钥
- **README 给出完整安装与首次运行示例**
- 明确声明外部依赖（Python 版本、`python-docx`）

---

## 五、发布到 WorkBuddy 应用内市场

WorkBuddy 的推荐市场（BuiltinMarket）与 SkillHub 打通：

1. 先在 SkillHub 完成上架（见 §四）
2. 打开 WorkBuddy → 左侧【技能管理】/【专家 → 技能市场】
3. 搜索技能名，一键安装

用户也可以不走市场，直接在对话里说「安装 SCI-writing-VIP 技能」由技能安装器完成。

> 若你是**企业版**用户，除个人 SkillHub 外还有企业专区通道，流程与个人发布不同（需企业管理员开通），请以企业控制台说明为准。

---

## 六、发布到 ClawHub（全球技能社区，可选）

若同时希望面向海外用户分发：

1. 访问 ClawHub（`clawhub.ai`），用 GitHub 账号登录
2. `Publish Skill` → 上传 zip 包 → 填写元数据
3. 提交前先在本地校验格式（如有 `clawhub validate` 命令则运行）
4. 在真实环境中实测技能能正常触发与运行

> **注意**：腾讯 SkillHub 与 ClawHub **不会自动互相同步**。若要两边都有，需分别提交。

---

## 七、版本与更新

- 遵循**语义化版本**：新增功能 → minor；破坏性变更（如目录结构、脚本参数改名）→ major；修错 → patch。
- 每次发布更新 `CHANGELOG.md`，平台会展示版本历史，且支持回滚。
- 更新流程与首次发布相同（`push` → `publish`），版本号必须递增，否则平台会拒绝。

---

## 八、发布前最终检查清单

- [ ] `SKILL.md` frontmatter 只含白名单键，`description` ≤ 1024 字符，含 `agent_created: true`
- [ ] 无个人路径、无真实身份信息、无凭据
- [ ] 未打包任何文献数据、IF 表、缓存目录、生成的 Word/PDF
- [ ] `SKILL.md` 与 README 中的脚本路径为相对路径或占位符
- [ ] 依赖已声明（Python 3.9+，仅 `report_md_to_docx.py` 需 `python-docx`）
- [ ] 脚本在**干净环境**中实测可跑（至少验证 `--help` 与一条端到端最小流程）
- [ ] `LICENSE` 存在且与平台填写的许可一致
- [ ] `CHANGELOG.md` 记录了本次版本变更
- [ ] 已用用户视角走一遍：一个从没接触过的人，能否按 README 在 10 分钟内跑起来
