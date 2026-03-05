# Structured Docs JSON Schemas

> 本文件定义 `scripts/write_structured_docs.py` 的输入契约。  
> 所有结构化文档必须先构造 JSON，再调用脚本落盘，不允许手工直接写 Markdown。

---

## 1) 通用包络（所有 kind 必填）

```json
{
  "kind": "source_index",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {}
}
```

字段约束：
- `kind`: 必须与 CLI `--kind` 一致。
- `version`: 当前固定字符串 `"1.0"`。
- `generated_at`: ISO-8601 时间字符串。
- `data`: 对应 kind 的对象。

CLI:

```bash
python scripts/write_structured_docs.py \
  --kind <kind> \
  --input-json <payload.json> \
  --output-dir ./out
```

---

## 2) kind -> 输出文件映射

| kind | 输出文件 |
|------|----------|
| `project_summary` | `out/project_summary.md` |
| `source_index` | `out/source_index.md` |
| `sink_index` | `out/sink_index.md` |
| `defense_catalog` | `out/defense_catalog.md` |
| `progress` | `out/progress.md` |
| `findings` | `out/findings.md` |
| `interaction_matrix` | `out/interaction_matrix.md` |

---

## 3) Schema Definitions

### 3.1 `project_summary`

```json
{
  "kind": "project_summary",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {
    "project_name": "demo",
    "repo_root": ".",
    "project_types": ["Web 应用"],
    "languages": ["Python"],
    "frameworks": ["Django"],
    "architecture_patterns": ["Monolith"],
    "key_entrypoints": ["POST /api/login"],
    "security_focus": ["认证授权", "业务逻辑"],
    "assumptions": ["只做静态审计"]
  }
}
```

必填：
- `project_name` `repo_root`
- `project_types` `languages`

可选：
- `frameworks` `architecture_patterns` `key_entrypoints` `security_focus` `assumptions`（均为字符串数组）

---

### 3.2 `source_index`

```json
{
  "kind": "source_index",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {
    "sources": [
      {
        "id": "S1",
        "entry_point": "POST /api/login",
        "location": "auth.py:42",
        "data_types": ["username", "password"],
        "risk": "high",
        "downstream_modules": ["auth", "session"],
        "notes": ""
      }
    ]
  }
}
```

`sources[]` 必填字段：
- `id` `entry_point` `location`
- `data_types`（string[]）
- `risk`（`critical|high|medium|low`）

可选：
- `downstream_modules`（string[]）
- `notes`（string）

---

### 3.3 `sink_index`

```json
{
  "kind": "sink_index",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {
    "sinks": [
      {
        "id": "K1",
        "sink": "cursor.execute",
        "location": "db.py:88",
        "sink_type": "SQL 执行",
        "required_privilege": "user",
        "impact": "数据泄露",
        "sanitizers": ["parametrize_query"],
        "notes": ""
      }
    ]
  }
}
```

`sinks[]` 必填字段：
- `id` `sink` `location`
- `sink_type` `required_privilege` `impact`

可选：
- `sanitizers`（string[]）
- `notes`（string）

---

### 3.4 `defense_catalog`

```json
{
  "kind": "defense_catalog",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {
    "defenses": [
      {
        "id": "D1",
        "defense": "rate_limit",
        "defense_type": "速率限制",
        "location": "middleware.py:15",
        "coverage": ["POST /api/login"],
        "reversal_risk": "medium",
        "notes": "可被用户名维度滥用"
      }
    ]
  }
}
```

`defenses[]` 必填字段：
- `id` `defense` `defense_type` `location`
- `coverage`（string[]）
- `reversal_risk`（`low|medium|high`）

可选：
- `notes`（string）

---

### 3.5 `progress`

```json
{
  "kind": "progress",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {
    "total_sources": 2,
    "completed": 1,
    "skipped": 0,
    "pending": 1,
    "items": [
      {
        "id": "S1",
        "entry_point": "POST /api/login",
        "location": "auth.py:42",
        "risk": "high",
        "status": "completed",
        "findings_count": 2,
        "notes": ""
      }
    ]
  }
}
```

`items[]` 必填字段：
- `id` `entry_point` `location`
- `risk`（`critical|high|medium|low`）
- `status`（`pending|in_progress|completed|skipped`）

可选：
- `findings_count`（int >= 0）
- `notes`（string）
- 顶层统计：`total_sources` `completed` `skipped` `pending`（int >= 0，可缺省，脚本会从 `items` 推断）

---

### 3.6 `findings`

```json
{
  "kind": "findings",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {
    "findings": [
      {
        "id": "F-001",
        "title": "SQL 注入",
        "severity": "critical",
        "status": "confirmed",
        "evidence_score": 95,
        "type": "注入",
        "location": "auth.py:42",
        "source": "POST /api/login",
        "sink": "cursor.execute",
        "summary": "拼接 SQL 执行"
      }
    ]
  }
}
```

`findings[]` 必填字段：
- `id` `title`
- `severity`（`critical|high|medium|low`）
- `status`（`confirmed|likely|possible`）
- `evidence_score`（int, 0-100）
- `type` `location` `summary`

可选：
- `source` `sink`（string）

---

### 3.7 `interaction_matrix`

```json
{
  "kind": "interaction_matrix",
  "version": "1.0",
  "generated_at": "2026-03-04T10:30:00Z",
  "data": {
    "pairs_checked": 12,
    "interactions_found": 2,
    "interactions": [
      {
        "id": "I-01",
        "vulnerability_a": "F-001",
        "vulnerability_b": "F-003",
        "effect": "时序盲注放大",
        "description": "SQL 注入与慢散列组合导致明显时间差",
        "severity": "high",
        "chainable": true
      }
    ]
  }
}
```

必填：
- `pairs_checked`（int >= 0）
- `interactions`（array）

`interactions[]` 必填字段：
- `id` `vulnerability_a` `vulnerability_b`
- `effect` `description`
- `severity`（`critical|high|medium|low`）
- `chainable`（bool）

可选：
- `interactions_found`（int >= 0；缺省时由脚本按数组长度推断）
