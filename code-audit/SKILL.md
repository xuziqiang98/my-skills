---
name: code-audit
description: 基于LSP的智能代码安全审计Skill。利用OpenCode内置LSP进行代码理解、符号追踪、数据流分析，Agent自主识别项目特点并执行多维度安全审计（污点分析、认证授权、业务逻辑、敏感信息等），输出可验证的漏洞报告与PoC。适用于任何编程语言和项目类型。
---

# code-audit

> **核心哲学**：不依赖预定义规则匹配，而是指导 Agent 如何利用 LSP 智能理解代码、自主发现漏洞。项目类型无关的通用安全审计。

---

## 参考文件

本 Skill 附带参考文档，**按需读取**（不要一次性全部加载）：

| 文件 | 内容 | 何时读取 |
|------|------|----------|
| `references/vuln_taxonomy.md` | 漏洞分类、审计要点、严重性矩阵、Sanitizer 目录指南 | Phase 2（Sink 发现）时读取 |
| `references/finding_template.md` | 单条漏洞报告模板（含数据流分析、evidence_score 评分标准） | Phase 4（漏洞验证）时读取 |
| `references/report_template.md` | 完整安全审计报告模板 | Phase 7（报告生成）时读取 |
| `references/evolution_learned.md` | 用户经验沉淀：通用偏好、修复经验 | **始终读取** |
| `references/web_audit_checks.md` | Web 应用专用检查清单（CSRF、IDOR、时序攻击等） | **条件读取** — 仅当 Phase 0 识别为 Web 项目时 |
| `references/structured_schemas.md` | 结构化文档 JSON Schema 契约（脚本写入） | 所有结构化文档写入前读取 |

---

## 1) Skill 概述

### 适用范围（所有项目类型）

| 类别 | 示例 |
|------|------|
| **Web 应用** | HTTP API、WebSocket、GraphQL、微服务 |
| **CLI 工具** | 命令行工具、脚本、构建脚本 |
| **桌面应用** | Electron、Qt、Tkinter、Cocoa |
| **移动应用** | iOS (Swift/Obj-C)、Android (Kotlin/Java)、Flutter、React Native |
| **后端服务** | RPC、gRPC、消息队列消费者、Worker |
| **库/SDK** | 通用库、框架、工具包 |
| **智能合约** | Solidity、Rust (Solana)、Move |
| **嵌入式/系统** | C/C++、Rust、汇编、驱动 |
| **IaC** | Terraform、Pulumi、Helm、Kubernetes YAML |
| **前端** | React、Vue、Angular、Svelte |

### 核心目标

- **LSP 驱动的代码理解**：利用符号跳转、引用查找、类型分析理解代码结构
- **Agent 自主判断**：根据项目特点自主识别 source、sink、sanitizer，不依赖规则库
- **项目类型无关**：不预设项目类型，Agent 根据代码自行判断
- **多维度安全审计**：覆盖污点分析、认证授权、业务逻辑、敏感信息、供应链等
- **可验证的漏洞报告**：提供完整的调用链、触发条件、可复现 PoC
- **攻击链组合**：发现单点漏洞间的组合利用路径
---

## 2) 触发条件

### Triggers

- 用户要求"做一次代码审计"、"安全审计"、"安全检测"
- 用户要求"审计代码漏洞"、"找出安全问题"
- 用户要求"LSP 审计"、"智能审计"
- 用户要求"审计认证/授权/越权"（指定维度）
- 用户要求"生成漏洞报告"、"输出安全发现"
- 用户要求"审计智能合约"、"审计嵌入式代码"、"审计 IaC"

### Anti-triggers

- 用户只需要单文件 lint/格式化检查
- 用户要求动态渗透测试（非静态审计范畴）
- 用户要求实时漏洞扫描（需要网络访问）

---

## 3) 输入参数

### 必选/默认参数

- `repo_root`: 审计仓库根目录，默认 `.`
- `focus_paths`: 可选，聚焦扫描的目录/文件
- `audit_dimensions`: 审计维度，默认全维度
- `depth`: 追踪深度，默认 `3`

### 可选参数

- `target_languages`: 目标语言，默认自动检测
- `output_format`: 输出格式，`markdown`（默认）/ `json`
- `max_sources`: 最大分析入口数，默认不限（大型项目建议设置以控制预算）

---

## 4) 输出产物

### 工作目录

所有中间结果和最终报告写入 `{repo_root}/out/` 目录。Agent 在 Phase 0 启动时创建该目录。
默认参数 `repo_root='.'` 时，`out/` 位于当前工作目录。

### 产物清单

| 阶段 | 文件 | 说明 |
|------|------|------|
| Phase 0 | `out/project_summary.md` | 项目审计概览（项目类型、技术栈、架构模式） |
| Phase 1 | `out/source_index.md` | 入口点清单 + 风险优先级排序 |
| Phase 2 | `out/sink_index.md` | 敏感操作清单 + Sanitizer 目录 |
| Phase 2 | `out/defense_catalog.md` | 全局防御机制目录 |
| **持续更新** | **`out/progress.md`** | **进度追踪（每完成一个入口点更新）** |
| Phase 3-4 | `out/per_source/S{N}_analysis.md` | 逐源深入分析结果 |
| Phase 5 | `out/findings.md` | 漏洞发现汇总（含 evidence_score） |
| Phase 5 | `out/interaction_matrix.md` | 交互矩阵分析 |
| Phase 6 | `out/attack_chains.md` | 攻击链组合 |
| Phase 7 | `out/report.md` | 综合安全审计报告 |

### 文档写入分工（MUST）

- **推理文档（智能体直写）**：
  - `out/per_source/S{N}_analysis.md`
  - `out/attack_chains.md`
  - `out/report.md`
- **结构化文档（必须脚本写入）**：
  - `out/project_summary.md`
  - `out/source_index.md`
  - `out/sink_index.md`
  - `out/defense_catalog.md`
  - `out/progress.md`
  - `out/findings.md`
  - `out/interaction_matrix.md`
- **不在本 Skill 写入范围**：`evolution` 相关文件（由 `skill-evolution-manager` 维护）。

### Structured JSON Schema Contract（MUST）

结构化文档写入前，Agent 必须先构造 JSON payload：

```json
{
  "kind": "source_index",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {}
}
```

- `kind` 必须与脚本参数 `--kind` 一致。
- 详细字段定义与示例：`references/structured_schemas.md`。

### 写入执行约束（MUST Use Scripts for Structured Docs）

- **禁止** 智能体直接手工写结构化 Markdown 文件。
- **必须** 调用 `scripts/write_structured_docs.py` 写入结构化文档：

```bash
python scripts/write_structured_docs.py \
  --kind <kind> \
  --input-json <payload.json> \
  --output-dir ./out
```

- 推理文档允许智能体直接写。
---

## 5) 核心流程：混合执行模型

### 设计哲学

**批量发现 + 逐源深入 + 全局聚合**

```
┌─────────────── 批量发现（无状态采集，产出索引） ──────────────┐
│  Phase 0: 项目理解                                            │
│  Phase 1: 入口点发现 → source_index.md                        │
│  Phase 2: Sink发现 + 全局防御目录 → sink_index.md + defense_catalog.md │
└───────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────── 逐源深入（有状态推理，每次聚焦单个入口） ──────┐
│  for each source_point (按风险优先级排序):                     │
│      Phase 3: 数据建模 + 双向数据流追踪（仅限当前入口）       │
│      Phase 4: 漏洞验证 + PoC 生成（仅限当前入口的发现）       │
│  end for                                                      │
└───────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────── 全局聚合（跨源综合分析） ─────────────────────┐
│  Phase 5: 交互矩阵分析（跨源组合效应）                       │
│  Phase 6: 攻击链综合                                          │
│  Phase 7: 报告生成                                            │
└───────────────────────────────────────────────────────────────┘
```

**为什么采用混合模型**：

- **Phase 0-2（批量）**：无状态采集，产出可序列化的索引文件。LLM 不需要在此阶段维护复杂推理状态，批量执行效率高。
- **Phase 3-4（逐源）**：有状态推理，需要 LLM 维持数据流上下文。逐源执行避免注意力漂移，每次只关注一个入口点的完整攻击面。
- **Phase 5-7（全局）**：需要所有入口的发现结果才能进行跨源分析。

**逐源分析时引用全局索引**：Phase 3-4 分析单个入口时，引用 Phase 2 产出的 `sink_index.md` 和 `defense_catalog.md`，而非重新发现 Sink 和防御机制。

---

### Phase 0: 项目理解（使用 LSP）

**目标**：快速理解项目结构、语言、技术栈、项目类型

**执行步骤**：

1. 使用 `glob` 发现项目根目录的关键文件
2. 识别项目类型：
   - 通过文件后缀判断语言
   - 通过配置文件判断框架/技术栈
   - 通过入口文件判断应用类型
3. 使用 `lsp_symbols` 扫描关键文件，获取函数/类/接口列表
4. 识别项目架构模式
5. **条件加载**：若识别为 Web 项目 → 读取 `references/web_audit_checks.md`
6. 构造 `project_summary` payload，并调用脚本写入 `out/project_summary.md`：

```bash
python scripts/write_structured_docs.py \
  --kind project_summary \
  --input-json /tmp/project_summary.json \
  --output-dir ./out
```

**项目类型识别启发式**：

| 特征 | 可能的类型 |
|------|-----------|
| `package.json`, `node_modules` | Node.js/Web 项目 |
| `Cargo.toml`, `Cargo.lock` | Rust 项目 |
| `go.mod`, `go.sum` | Go 项目 |
| `pom.xml`, `build.gradle` | Java 项目 |
| `requirements.txt`, `setup.py` | Python 项目 |
| `*.sol` | 智能合约 |
| `main.tf`, `*.tfvars` | Terraform IaC |
| `CMakeLists.txt`, `Makefile` | C/C++ 项目 |
| `*.xcodeproj`, `Podfile` | iOS/macOS 项目 |

---

### Phase 1: 入口点发现（信任边界识别）

**目标**：识别所有外部输入入口，定义信任边界，产出带风险排序的 `source_index.md`

**Agent 思考方式**：

- "这个函数处理什么类型的输入？"
- "输入来自哪里？可信吗？"
- "是否有边界检查/净化？"

**入口类型（按项目类型）**：

| 项目类型 | 入口类型 |
|----------|----------|
| **Web 应用** | HTTP Handler、Router、Middleware、WebSocket、GraphQL Resolver |
| **CLI 工具** | main()、argparse/click flag、stdin 读取 |
| **桌面/移动** | UI 事件回调、文件选择器、URL Scheme |
| **后端服务** | RPC Handler、gRPC Method、MQ Consumer、Webhook |
| **库/SDK** | 公共 API、插件接口、扩展点 |
| **智能合约** | public 函数、receive/payable 函数 |
| **嵌入式** | 中断处理、硬件中断、IO 操作 |
| **IaC** | provider 配置、resource 定义、variable 输入 |

**输出 `source_index.md` 格式**：

```
| # | 入口点 | 位置 | 数据类型 | 初步风险 | 下游模块 |
|---|--------|------|----------|----------|----------|
| S1 | POST /api/users | user_handler.py:42 | username, email, avatar | 🔴 高 | auth, storage |
| S2 | CLI --config | main.py:15 | file_path | 🟡 中 | config_parser |
| ... | | | | | |
```

**落盘（MANDATORY）**：构造 `source_index` payload 后，调用脚本写入 `out/source_index.md`。


---

### Phase 2: Sink 发现 + 全局防御目录

**目标**：识别所有敏感操作，建立全局 Sanitizer 目录和防御机制目录

> **📖 此阶段读取 `references/vuln_taxonomy.md`**，获取完整的漏洞分类、常见 Sink 列表、审计要点检查清单和 Sanitizer 目录指南。

**Agent 思考方式**：

- "这个函数执行什么敏感操作？"
- "操作需要什么权限？"
- "操作的后果是什么？"

**Sanitizer 目录构建（MANDATORY）**：

在 Sink 扫描过程中，同步构建项目的 Sanitizer 目录：

```
对于每个发现的 Sink：
  1. 反向查找：该 Sink 的输入路径上存在哪些净化/校验函数？
  2. 记录每个 Sanitizer 的：
     - 位置（文件:行号）
     - 净化类型（转义、过滤、白名单、编码）
     - 覆盖的威胁类型（XSS、SQLi、CmdInj...）
     - 已知缺陷（不完整过滤、可绕过等）
  3. 标注未被任何 Sanitizer 保护的 Sink → 高优先级
```

**全局防御机制目录（MANDATORY — NEW）**：

在 Sink 扫描的同时，识别并编录跨入口点的全局防御机制：

```
对于每个防御机制：
  1. 类型：认证中间件 / 授权检查 / 速率限制 / WAF / 输入过滤 / CSRF保护
  2. 覆盖范围：保护了哪些入口/Sink？
  3. 反转风险：该机制能否被攻击者武器化？（见下方防御反转检查）
```

**防御机制反转检查（MANDATORY）**：

在识别到安全机制时，**立即执行反转分析**：

```
对于每个安全机制 M：
  1. M 的触发条件是什么？（如：连续5次登录失败）
  2. 触发条件的输入参数是什么？（如：phone/username）
  3. 攻击者能否控制这些输入参数？
  4. 如果能 → 攻击者可以对任意目标用户触发该机制
  5. 触发后的影响是什么？（如：目标用户被锁定15分钟）
  → 如果 3=是 且 5=负面影响 → 该安全机制可被武器化为 DoS
```

**典型反转模式**：

| 安全机制 | 反转攻击 |
|----------|----------|
| 登录失败锁定（基于用户名/手机号） | 攻击者故意输错密码锁定目标账号 |
| 速率限制（基于用户ID） | 攻击者耗尽目标用户的API配额 |
| 验证码触发（基于IP+用户） | 攻击者使目标用户始终需要验证码 |
| 支付冻结（基于异常行为） | 攻击者模拟异常行为冻结目标账户 |

**输出**：`sink_index.md` + `defense_catalog.md`

**落盘（MANDATORY）**：分别构造 `sink_index` 与 `defense_catalog` payload，并调用脚本写入对应文件。

---

### Phase 3-4: 逐源深入分析（核心迭代循环）

**这是与传统扫描的核心区别。对每个入口点执行完整的深度子流程，而非批量浅扫。**

> **写入约定**：`write_structured/update_structured` 表示“先生成 payload JSON，再调用 `scripts/write_structured_docs.py`”；`write_reasoning` 表示智能体直接写推理文档。

```
源入口列表 = load("source_index.md")  # Phase 1 产出
全局Sink = load("sink_index.md")       # Phase 2 产出
全局防御 = load("defense_catalog.md")  # Phase 2 产出

# 初始化进度文件（结构化：脚本写入）
write_structured("progress", 生成初始进度payload(源入口列表))  # 所有入口状态="⬼ 待分析"

for 当前入口 in 源入口列表 (按风险优先级排序):
    
    # ═══ Phase 3: 数据建模 + 双向数据流追踪 ═══
    
    # 3.1 数据源建模（原 Phase 1.5，现在逐源执行）
    建模(当前入口):
        - 识别数据类型：用户输入 / 文件 / 外部系统 / 环境数据
        - 标注可信度：🔴 完全不可信 / 🟡 部分可信 / 🟢 可信（需验证）
        - 记录持久化：数据是否写入 DB/文件/缓存？
        - 记录下游模块：数据流向哪些模块？

    # 3.2 反向数据流追踪（Sink → Source）
    for 相关Sink in 全局Sink (与当前入口有数据路径的):
        - 用 LSP 追踪完整调用链
        - 对照全局防御目录，检查路径上的 Sanitizer 是否有效
        - 检查 Guard 是否在正确路径？是否可绕过？
        - 检查遗漏的分支和边界条件

    # 3.3 正向数据流追踪（Source → 传播 → 存储 → 后续使用）
    正向追踪(当前入口):
        - 数据是否被持久化？写入前是否净化？
        - 持久化数据在何处被读取？读取时是否当作可信数据？（二次注入）
        - 数据是否跨模块/跨请求传递？（跨请求污染）
        - 数据是否经格式转换后进入不同 Sink？（格式转换逃逸）

    # 3.4 状态完整性检查
    状态检查(当前入口):
        - 该操作是否有前置状态校验？（如 if order.status != '待支付'）
        - 已完成操作能否被重复执行？（幂等性）
        - 状态转换是否只允许合法路径？
        - 重复执行是否造成资金/数据影响？

    # ═══ Phase 4: 漏洞验证 + PoC ═══
    
    # 4.1 验证当前入口发现的所有漏洞
    for 漏洞 in 当前入口.发现:
        - 调用链可复现：用 LSP 确认每跳存在
        - PoC 可触发：给出具体的请求/命令
        - 前置条件明确：需要什么权限/状态
        - 影响范围清晰：能影响什么
        - evidence_score 评分（4维度）
    
    # 4.2 探索关联问题
    探索(当前入口):
        - 该入口附近是否有其他问题？
        - 同一函数是否有多个漏洞？
        - 发现新问题 → 记录到当前入口的分析结果中
    
    # 产出：out/per_source/S{N}_analysis.md（推理文档：智能体直写）
    write_reasoning("out/per_source/S{N}_analysis.md", 当前入口分析结果)
    
    # ███ 更新进度文件（MANDATORY，结构化：脚本写入） ███
    update_structured("progress", 当前入口 = "✅ 已完成", 发现漏洞数=N)

    # 早停条件（可选）
    if 已分析入口数 >= max_sources:
        # 早停时也必须更新 progress.md，将剩余入口标记为 "⏸ 跳过（达到 max_sources 上限）"
        update_structured("progress", 剩余入口 = "⏸ 跳过", 跳过原因="达到 max_sources 上限")
        break

end for
```

> **📖 Phase 4 验证时读取 `references/finding_template.md`**，每个漏洞必须按模板输出，包含数据流逐跳分析、evidence_score 评分。

**`out/progress.md` 格式**：

```markdown
# 审计进度追踪

总入口数: 12 | 已完成: 5 | 跳过: 0 | 待分析: 7

| # | 入口点 | 位置 | 风险 | 状态 | 发现漏洞 | 备注 |
|---|--------|------|------|------|--------|------|
| S1 | POST /api/users | user_handler.py:42 | 🔴 | ✅ 已完成 | 3 | |
| S2 | POST /api/login | auth.py:15 | 🔴 | ✅ 已完成 | 1 | |
| S3 | GET /api/orders | order.py:88 | 🔴 | ▶️ 分析中 | - | |
| S4 | CLI --config | main.py:15 | 🟡 | ⬼ 待分析 | - | |
| ... | | | | | | |
| S12 | healthcheck | health.py:5 | 🟢 | ⏸ 跳过 | 0 | 风险极低，无外部输入 |
```

**状态枚举**：
- `⬼ 待分析` — 还未开始
- `▶️ 分析中` — 当前正在分析
- `✅ 已完成` — 分析完成，结果在 `per_source/S{N}_analysis.md`
- `⏸ 跳过` — 未分析，必须在备注中说明跳过原因

**重点关注的正向追踪模式**：

| 模式 | 说明 | 示例 |
|------|------|------|
| 二次注入 | 输入→存储→读取→Sink，存储时净化但读取时不净化 | SQL二次注入、存储型XSS |
| 跨请求污染 | 请求A写入→请求B读取→Sink | Session 污染、缓存投毒 |
| 格式转换逃逸 | 输入→序列化→反序列化→Sink，格式转换绕过净化 | JSON→XML转换中的实体注入 |
| 延迟触发 | 输入→存储→定时任务/后台Job→Sink | Cron job 命令注入 |

**停止条件**（何时结束单个入口的分析）：

- ✅ 所有相关 Sink 的调用链已完整追踪
- ✅ 正向追踪覆盖了所有持久化路径
- ✅ 所有可能的绕过路径都已检查
- ✅ 相邻代码已检查完毕
- ⚠️ 代码复杂度太高，无法继续
- ⚠️ 需要运行时信息才能继续

---

**完成性校验（进入 Phase 5 前必须执行）**：

```
进度 = load("out/progress.md")
未分析 = 进度 中 状态 == "⬼ 待分析" 的入口
已跳过 = 进度 中 状态 == "⏸ 跳过" 的入口

if 未分析 非空:
    # 禁止无声跳过——必须回去分析 或 显式标记跳过+填写原因
    报错: "以下入口点未分析且未说明原因: {未分析}"

if 已跳过 非空:
    # 检查每个跳过的入口是否有备注原因
    for 入口 in 已跳过:
        assert 入口.备注 非空, "跳过的入口必须说明原因"
    # 允许的跳过原因：
    #   - 风险极低（无外部输入，如 healthcheck）
    #   - 与已分析入口同质（同一 handler 的不同 HTTP method）
    #   - 达到 max_sources 上限
    #   - 上下文窗口不足（需建议用户分批审计）
```

**执行步骤**：
1. 汇总所有逐源分析的漏洞发现，生成 `findings` payload 并调用脚本写入 `out/findings.md`
2. 收集所有安全特性（如 argon2 慢散列、登录锁定等）
3. 按严重性排序，取 Top-20 项
4. 对 Top-20 中的每对 (Vi, Vj) 分析：
   - Vi 是否放大或使能 Vj？
   - Vj 是否放大或使能 Vi？
   - 如果存在交互效应 → 记录为组合漏洞

**关键交互模式**：

| 组合 | 交互效应 | 示例 |
|------|----------|------|
| 数据获取漏洞 × 时间放大器 | 无需 SLEEP 的时序盲注 | SQL注入 × argon2慢散列 |
| IDOR × 缺失 CSRF | 强制受害者操作 | 遍历订单号→篡改地址→CSRF触发受害者付款 |
| 用户枚举 × 无暴破防护 | 完整账号接管链 | 枚举有效用户名→暴力破解密码→登录 |
| IDOR × 缺失状态校验 | 重复资金操作 | 已支付订单可被再次「支付」，每次扣余额 |
| 枚举 × 账号锁定 | 全站拒绝服务 | 枚举所有用户→逐一触发锁定 |

**输出**：`out/interaction_matrix.md` — 已检查的配对数量、发现的交互数量、每个交互的详细描述。

**落盘（MANDATORY）**：构造 `interaction_matrix` payload 后调用脚本写入。

---

### Phase 6: 攻击链综合

**目标**：系统性构造多步攻击链，发现单点分析无法发现的组合利用路径

**规则**：产出所有现实可行的攻击链。如果少于 3 条，必须解释原因（如项目功能简单、漏洞类型单一等），而非强制凑数。

**组合模式**：

| 组合类型 | 示例 |
|----------|------|
| 信息收集 → 权限提升 | 信息泄露 → Token → 越权 |
| 弱入口 → 核心漏洞 | SSRF → 内网探测 → RCE |
| 业务逻辑链 | 条件竞争 → 余额篡改 |
| 供应链 | 依赖漏洞 → 代码执行 |
| 智能合约 | 重入 → 资金被盗 |
| 枚举 → 暴破 → 接管 | 时序枚举用户名 → 暴力破解密码 → 管理员接管 |
| IDOR → CSRF → 资金 | 订单遍历 → 地址篡改 → CSRF强制付款 |
| 漏洞 × 防御反转 | 用户枚举 × 锁定机制 → 全站DoS |

**输出格式**（每条攻击链）：

```
攻击链 #N: [名称]
  步骤1: [漏洞A] → 获得 [中间成果]
  步骤2: [漏洞B] → 利用 [中间成果] 达成 [下一步]
  步骤N: [最终影响]
  涉及漏洞: VULN-XX, VULN-YY
  前置条件: [所需权限/状态]
  最终影响: [具体危害]
  可信度: Confirmed / Likely / Possible
```

---

### Phase 7: 报告生成

**目标**：输出结构化、可操作的安全报告

> **📖 此阶段读取 `references/report_template.md`**，获取完整的报告模板。最终报告必须严格按该模板输出。

**报告验证（重要）**：

> 在输出最终报告前，必须启动 sub-agent 验证报告有效性

**验证清单**：

1. **调用链完整性**：每个漏洞的调用链是否完整？每跳是否有具体的文件:行号？
2. **漏洞真实性**：漏洞描述是否与代码实际情况一致？
3. **修复建议合理性**：建议是否针对实际问题？代码是否与当前项目语言/框架匹配？
4. **遗漏检查**：是否有重要漏洞类型被遗漏？逐源分析是否覆盖了所有高风险入口？
5. **evidence_score 一致性**：评分是否与证据充分度匹配？

---

<!-- EVOLUTION_REFERENCE:START -->
## Evolution Learned Reference

> Evolution data is maintained in `references/evolution_learned.md` by `skill-evolution-manager`.
<!-- EVOLUTION_REFERENCE:END -->
