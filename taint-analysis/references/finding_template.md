# 单条漏洞记录模板（finding_template）

```markdown
## [ID] 标题

- 严重性: critical/high/medium/low
- 状态: Confirmed/Likely/Possible
- evidence_score: 0-100
- TaintKind: cmd/path/query/template/ssrf/deser/memory/authz

### 影响
- 描述业务与技术影响（数据泄露、越权、RCE、破坏完整性等）

### 证据链
- Source: `文件:行号` | `片段`
- Sink: `文件:行号` | `片段`
- 函数栈: `A -> B -> C`
- 变量链: `x -> y -> z`
- Guard 判断: `存在/缺失/不确定`（写明条件）
- Sanitizer 判断: `有效/无效/不确定`（写明原因）
- 关键证据片段:
  - [source] ...
  - [call] ...
  - [sink] ...

### 静态可利用性
- 利用前置条件：
- 主要障碍：
- 结论：

### 修复建议
- 立即修复：
- 中期治理：
- 长期防护：

### 测试点
- 安全单测：
- 回归用例：
- 负向测试：

### 假设与不确定性
- 假设：
- 不确定点：
```
