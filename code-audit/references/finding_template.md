# 单条漏洞发现模板（详细版）

> **核心要求**：不是只列出"有漏洞"，而是要能回答"漏洞是怎么形成的"和"如何触发"

---

```markdown
## [F-XXX] 漏洞标题

- **严重性**: Critical / High / Medium / Low
- **类型**: 漏洞分类
- **状态**: Confirmed / Likely / Possible
- **置信度**: XX%

---

### 摘要

一句话描述漏洞本质

---

### 一、数据流逐跳分析（必须详细）

```
Source → H1 → H2 → H3 → Sink
```

#### 第1跳：入口
- **位置**：`api/handler.go:42`
- **变量**：`user_input = request.Body.cmd`
- **处理**：直接赋值，未过滤
- **安全性**：用户可控 ❌
- **重要性**：外部输入入口

#### 第2跳：传递
- **位置**：`service/parser.go:25`
- **变量**：`cmd = parseCommand(user_input)`
- **处理**：字符串拼接 `cmd = "run " + user_input`
- **安全性**：未净化 ❌
- **重要性**：数据传递

#### 第3跳：Sink
- **位置**：`core/exec.go:118`
- **变量**：`exec.Command(cmd, shell=True)`
- **处理**：系统命令执行
- **安全性**：危险操作 ⚠️
- **重要性**：最终执行点

---

### 二、Sanitizer / Guard 分析

#### Sanitizer 检查
- **位置**：`utils/sanitize.go:30`
- **函数**：`sanitize(cmd string) string`
- **逻辑**：过滤了 `;` `&` `|` 等字符
- **评估**：❌ 可绕过
- **原因**：未过滤 `$(...)` 反引号 `$()` 等

#### Guard 检查
- **位置**：`middleware/auth.go:20`
- **函数**：`requireAdmin()`
- **逻辑**：检查 `ctx.IsAdmin`
- **评估**：⚠️ 路径不覆盖
- **原因**：当前 endpoint 未注册此中间件

---

### 三、触发条件

| 条件 | 值 |
|------|-----|
| 需要认证 | 否 |
| 需要特殊权限 | 否 |
| 网络可达 | 是 |
| Content-Type | application/json |
| 其他 | 无 |

---

### 四、PoC（可选）

> 注意：如果难以给出具体 PoC（如嵌入式、智能合约、业务逻辑、越权类），可以标注"需运行时验证"或省略此部分。

如果能提供 PoC：

#### 请求

### 四、PoC（必须具体可验证）

#### 请求
```http
POST /api/run HTTP/1.1
Host: target.com
Content-Type: application/json
Authorization: Bearer <token>

{"cmd": "cat /etc/passwd"}
```

#### 预期响应
```
root:x:0:0:root:/root:/bin/bash
daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin
bin:x:2:2:bin:/bin:/usr/sbin/nologin
...
```

#### 验证方式
```bash
# 本地验证
curl -X POST http://localhost:8080/api/run \
  -H "Content-Type: application/json" \
  -d '{"cmd": "whoami"}'
```

---

### 五、影响分析

#### 技术影响
- 攻击者可执行任意系统命令
- 获取服务器 root 权限
- 读取任意文件
- 横向移动

#### 业务影响
- 数据泄露
- 服务完全控制
- 法律合规风险

---

### 六、修复建议

#### 立即修复
```go
// 修复前（危险）
exec.Command("sh", "-c", cmd)

// 修复后（安全）
// 方案1：参数化，不使用 shell
exec.Command("ls", "-la", userArg)

// 方案2：白名单
allowedCmds := map[string]bool{"ls": true, "cat": true}
if !allowedCmds[cmd] {
    return error("命令不允许")
}
```

#### 长期改进
1. 建立命令执行白名单机制
2. 添加操作审计日志
3. 引入 SAST 扫描

---

### 七、验证状态

- [x] **已验证** - 调用链完整，每步可定位
- [x] **PoC 可触发** - 本地测试成功
- [ ] **待验证** - 需要目标环境测试

---

### 八、假设与不确定

- ✅ 确定：外部输入未过滤直接传入命令
- ✅ 确定：shell=True 启用
- ⚠️ 不确定：目标是否有 WAF 拦截
- ⚠️ 不确定：网络可达性

---

### 九、关联发现

- **关联漏洞**：F-002（认证缺失）- 同一 endpoint
- **攻击链**：CHAIN-01 → 可组合利用
- **同函数问题**：F-005 - 同一 sanitize 函数可绕过

---

### 十、参考

- CWE-78: OS Command Injection
- OWASP: Command Injection
- CVSS: 9.8 (Critical)
```
