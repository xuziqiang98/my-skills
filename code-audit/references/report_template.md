# 安全审计报告模板

## 报告元信息

```yaml
报告标题: [项目名称] 安全审计报告
审计时间: YYYY-MM-DD
审计范围: [repo_root] / [focus_paths]
审计方法: LSP 驱动智能代码审计
审计维度: [taint|auth|logic|crypto|info]
审计人员: [Agent Name]
项目版本: [commit/tag]
```

---

## 1. 审计概览

### 1.1 项目信息

| 项目 | 信息 |
|------|------|
| 项目名称 | [项目名] |
| 仓库地址 | [repo] |
| 主要语言 | [Python/JavaScript/Go/etc] |
| 框架 | [Django/Express/ Gin/etc] |
| 代码规模 | [文件数/行数] |

### 1.2 审计统计

| 指标 | 数量 |
|------|------|
| 审计文件数 | N |
| 发现漏洞数 | N |
| Critical | N |
| High | N |
| Medium | N |
| Low | N |
| 攻击链数 | N |

### 1.3 审计范围

- **审计维度**：污点分析、认证授权、业务逻辑、敏感信息
- **信任边界**：HTTP 处理器、CLI 入口、配置文件
- **重点关注**：用户输入处理、权限检查、敏感操作

---

## 2. 审计方法

### 2.1 技术方法

1. **LSP 驱动代码理解**
   - 使用 `lsp_symbols` 理解项目结构
   - 使用 `lsp_goto_definition` 追踪数据流
   - 使用 `lsp_find_references` 构建调用图

2. **双向数据流追踪**
   - 反向追踪（Sensitive Sink → Source）
   - 正向追踪（Entry Point → Sensitive Operation）

3. **多维度安全检查**
   - 污点传播分析
   - 认证授权审计
   - 业务逻辑分析
   - 敏感信息扫描

### 2.2 审计流程

```
Phase 0: 项目理解 → LSP 符号扫描
Phase 1: 入口点发现 → 信任边界识别
Phase 2: 敏感操作识别 → Sink 发现
Phase 3: 数据流追踪 → 双向追踪
Phase 4: 认证授权分析 → 权限检查
Phase 5: 业务逻辑审计 → 逻辑漏洞
Phase 6: 漏洞验证 → PoC 生成
Phase 7: 攻击链组合 → 组合利用
Phase 8: 报告生成 → 结构化输出
```

### 2.3 假设与局限

- 假设代码仓库代表主要执行路径
- 未包含运行时动态分析
- 静态分析可能存在漏报/误报
- 业务逻辑漏洞需要人工复核

---

## 3. 发现列表

### 3.1 Critical

#### F-001: [漏洞标题]

- **类型**: 命令注入
- **位置**: `src/handler.go:50`
- **函数**: `execUserCommand(cmd string)`
- **置信度**: 95%

**摘要**：
用户输入直接拼接到系统命令执行，未经过滤。

**完整调用链**：
```
source: api/handler.go:20 | userInput = request.Body.cmd
  → api/handler.go:25 | cmd = parseCommand(userInput)
    → core/executor.go:50 | exec.Command(cmd)
```

**PoC**：
```http
POST /api/exec HTTP/1.1
Host: target.com
Content-Type: application/json

{"cmd": "cat /etc/passwd"}
```

**影响**：
攻击者可执行任意系统命令，获取服务器完全控制权。

**修复建议**：
1. 立即修复：使用参数化执行，避免字符串拼接
2. 长期：建立命令执行白名单，仅允许预定义命令

**验证状态**: ✅ 已验证

---

### 3.2 High

#### F-004: [漏洞标题]

...

---

### 3.3 Medium

#### F-007: [漏洞标题]

...

---

### 3.4 Low

#### F-010: [漏洞标题]

...

---

## 4. 攻击链分析

### 4.1 攻击链 1：信息收集 → 权限提升

**前置条件**：
- SSRF 可探测内网服务
- 获取到内部凭据

**攻击步骤**：
1. 利用 SSRF 探测元数据服务 (F-003)
2. 获取临时凭据
3. 利用认证绕过访问管理后台 (F-001)
4. 利用越权漏洞执行管理操作 (F-005)

**影响**：
从外部获取到内部系统完全控制权。

---

### 4.2 攻击链 2：越权操作 → 数据泄露

**前置条件**：
- 用户 ID 可预测
- 缺少租户隔离

**攻击步骤**：
1. 注册普通用户
2. 修改用户 ID 为其他用户 ID
3. 利用越权漏洞访问他人数据 (F-006)
4. 批量导出敏感数据

**影响**：
跨租户数据泄露，违反隐私合规。

---

## 5. 修复建议

### 5.1 立即修复（Critical/High）

| 漏洞 | 建议 | 优先级 |
|------|------|--------|
| F-001 命令注入 | 参数化执行 | P0 |
| F-002 SQL 注入 | 使用参数化查询 | P0 |
| F-003 认证绕过 | 检查认证中间件应用 | P1 |

### 5.2 中期改进（Medium）

| 漏洞 | 建议 | 优先级 |
|------|------|--------|
| F-007 XSS | 输出转义 | P2 |
| F-008 日志泄露 | 过滤敏感字段 | P2 |

### 5.3 长期安全建设

1. **安全开发生命周期 (SDL)**
   - 集成 SAST 到 CI/CD
   - 建立代码安全审查流程

2. **安全测试**
   - 自动化安全测试
   - 定期渗透测试

3. **安全监控**
   - 部署 WAF/IPS
   - 安全事件响应

---

## 6. 附录

### A. 审计产物清单

- `out/entry_points.md` - 入口点清单
- `out/sensitive_operations.md` - 敏感操作清单
- `out/flows_traced.md` - 数据流追踪结果
- `out/authz_analysis.md` - 认证授权分析
- `out/findings.md` - 漏洞发现清单
- `out/attack_chains.md` - 攻击链组合

### B. 工具与方法

- **LSP 工具**: lsp_symbols, lsp_goto_definition, lsp_find_references
- **搜索工具**: grep, ast_grep_search
- **静态分析**: 代码理解 + 数据流追踪

### C. 审计人员

- **Agent**: code-audit v1.0
- **执行时间**: [start_time] - [end_time]
- **审计模式**: 完全自动化 + 人工复核建议
