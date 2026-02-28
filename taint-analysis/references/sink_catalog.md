# 通用 Sink 目录（sink_catalog）

目标：给出跨语言可复用的高价值 sink 分类与典型模式，避免写成语言手册。

## 1. 命令执行 / 进程启动

- 风险：RCE、系统命令注入
- 典型模式：拼接字符串后执行、`shell=True`
- 示例 API：
  - Python：`os.system` `subprocess.run(..., shell=True)`
  - JavaScript/Node：`child_process.exec` `spawn("sh", ...)`
  - Go：`exec.Command(...).Run()`
  - Java：`Runtime.getRuntime().exec` `ProcessBuilder`
  - C/C++：`system` `popen`
  - Rust：`std::process::Command`

## 2. 动态执行 / Eval

- 风险：代码注入、模板逃逸
- 示例 API：
  - Python：`eval` `exec`
  - JavaScript：`eval` `new Function`
  - Java：`ScriptEngineManager`

## 3. SQL 原生执行

- 风险：SQL 注入
- 典型模式：字符串拼接查询、非参数化调用
- 示例 API：
  - Python：`cursor.execute(f"...")`
  - JavaScript：`sequelize.query(raw)`
  - Go：`db.Query(fmt.Sprintf(...))`
  - Java：`Statement.executeQuery`

## 4. 模板渲染

- 风险：SSTI、XSS 扩展链
- 示例 API：
  - Python：`render_template_string` `jinja2.Template`
  - JavaScript：`handlebars.compile` `ejs.render`
  - Go：`template.Execute`

## 5. 反序列化

- 风险：类型混淆、对象注入、RCE
- 示例 API：
  - Python：`pickle.loads` `yaml.load`
  - Java：`ObjectInputStream.readObject`
  - Go：`gob.NewDecoder(...).Decode`
  - Rust：`serde` 自定义反序列化入口

## 6. 文件写入 / 路径拼接

- 风险：目录穿越、覆盖敏感文件、持久化投毒
- 示例 API：
  - Python：`open(path, "w")`
  - JavaScript：`fs.writeFile` `path.join`
  - Go：`os.WriteFile` `filepath.Join`
  - Java：`Files.write`

## 7. 外联请求 / SSRF 面

- 风险：内网探测、元数据窃取
- 示例 API：
  - Python：`requests.get/post` `urllib.request.urlopen`
  - JavaScript：`fetch` `axios.get/post`
  - Go：`http.Get` `client.Do`
  - Java：`HttpClient.send`

## 8. 格式化与内存边界（Native）

- 风险：缓冲区溢出、格式化字符串漏洞
- 示例 API：
  - C/C++：`strcpy` `sprintf` `gets` `memcpy`
  - Rust：`unsafe` 边界拷贝

## 9. 危险配置

- 风险：认证绕过、TLS 降级、跨域放开
- 典型模式：`verify=False` `InsecureSkipVerify=true` `permitAll`

## 建议优先级

1. 先扫 `命令执行 / 反序列化 / SQL / 越权相关 sink`
2. 再扫 `文件写入 / 模板 / 外联请求`
3. 最后补 `危险配置 / native 边界`
