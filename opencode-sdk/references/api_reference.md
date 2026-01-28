# OpenCode SDK API Reference

Complete reference documentation for the OpenCode JavaScript/TypeScript SDK API methods, types, and usage patterns.

## Table of Contents

- [Client Creation](#client-creation)
- [Global API](#global-api)
- [Sessions API](#sessions-api)
- [Files API](#files-api)
- [Authentication API](#authentication-api)
- [TUI API](#tui-api)
- [Events API](#events-api)
- [App API](#app-api)
- [Project API](#project-api)
- [Path API](#path-api)
- [Config API](#config-api)
- [Type Definitions](#type-definitions)

## Client Creation

### createOpencode(options)

Creates both a server instance and client connection.

**Parameters:**
- `hostname` (string): Server hostname, default "127.0.0.1"
- `port` (number): Server port, default 4096
- `signal` (AbortSignal): Cancellation signal
- `timeout` (number): Server start timeout in ms, default 5000
- `config` (Config): Configuration object

**Returns:** `{ client, server }`

**Example:**
```javascript
const { client, server } = await createOpencode({
  hostname: "127.0.0.1",
  port: 4096,
  config: {
    model: "anthropic/claude-3-5-sonnet-20241022"
  }
})
```

### createOpencodeClient(options)

Creates client-only connection to existing server.

**Parameters:**
- `baseUrl` (string): Server URL, default "http://localhost:4096"
- `fetch` (function): Custom fetch implementation
- `parseAs` (string): Response parsing, default "auto"
- `responseStyle` (string): "data" or "fields", default "fields"
- `throwOnError` (boolean): Throw errors, default false

**Returns:** `Client`

**Example:**
```javascript
const client = createOpencodeClient({
  baseUrl: "http://localhost:4096"
})
```

## Global API

### client.global.health()

Check server health and version.

**Returns:** `{ healthy: boolean, version: string }`

```javascript
const health = await client.global.health()
console.log("Server version:", health.data.version)
```

## Sessions API

### Session Management

#### client.session.create(body)

Create a new session.

**Parameters:**
- `body.title` (string): Session title

**Returns:** `Session`

```javascript
const session = await client.session.create({
  body: { title: "My Session" }
})
```

#### client.session.list()

List all sessions.

**Returns:** `Session[]`

```javascript
const sessions = await client.session.list()
for (const session of sessions.data) {
  console.log(session.id, session.title)
}
```

#### client.session.get(path)

Get session details.

**Parameters:**
- `path.id` (string): Session ID

**Returns:** `Session`

```javascript
const session = await client.session.get({
  path: { id: "session-id" }
})
```

#### client.session.update(path, body)

Update session properties.

**Parameters:**
- `path.id` (string): Session ID
- `body.title` (string): New title

**Returns:** `Session`

```javascript
const session = await client.session.update({
  path: { id: "session-id" },
  body: { title: "New Title" }
})
```

#### client.session.delete(path)

Delete a session.

**Parameters:**
- `path.id` (string): Session ID

**Returns:** `boolean`

```javascript
const success = await client.session.delete({
  path: { id: "session-id" }
})
```

### Session Operations

#### client.session.prompt(path, body)

Send a prompt message to session.

**Parameters:**
- `path.id` (string): Session ID
- `body.model` (Model): Model configuration
- `body.parts` (Part[]): Message parts
- `body.noReply` (boolean): Context only, no AI response

**Returns:** `AssistantMessage` (unless noReply=true)

```javascript
const response = await client.session.prompt({
  path: { id: "session-id" },
  body: {
    model: { 
      providerID: "anthropic", 
      modelID: "claude-3-5-sonnet-20241022" 
    },
    parts: [{ type: "text", text: "Hello!" }]
  }
})
```

#### client.session.command(path, body)

Send a command to session.

**Parameters:**
- `path.id` (string): Session ID
- `body.command` (string): Command string

**Returns:** `AssistantMessage`

```javascript
const result = await client.session.command({
  path: { id: "session-id" },
  body: { command: "/check-file src/main.js" }
})
```

#### client.session.shell(path, body)

Execute shell command in session.

**Parameters:**
- `path.id` (string): Session ID
- `body.command` (string): Shell command

**Returns:** `AssistantMessage`

```javascript
const result = await client.session.shell({
  path: { id: "session-id" },
  body: { command: "ls -la" }
})
```

### Session History

#### client.session.messages(path)

Get message history for session.

**Parameters:**
- `path.id` (string): Session ID

**Returns:** `{ info: Message, parts: Part[] }[]`

```javascript
const messages = await client.session.messages({
  path: { id: "session-id" }
})
```

#### client.session.message(path)

Get specific message details.

**Parameters:**
- `path.id` (string): Session ID
- `path.messageId` (string): Message ID

**Returns:** `{ info: Message, parts: Part[] }`

## Files API

### Search Operations

#### client.find.text(query)

Search for text in files.

**Parameters:**
- `query.pattern` (string): Search pattern
- `query.path` (string): Search path (optional)

**Returns:** Array of matches with path, lines, line_number

```javascript
const results = await client.find.text({
  query: { pattern: "function.*opencode" }
})
```

#### client.find.files(query)

Find files by name pattern.

**Parameters:**
- `query.query` (string): File pattern
- `query.type` (string): "file" or "directory"
- `query.directory` (string): Override search directory
- `query.limit` (number): Max results (1-200)

**Returns:** `string[]`

```javascript
const files = await client.find.files({
  query: { query: "*.js", type: "file" }
})
```

#### client.find.symbols(query)

Find workspace symbols.

**Parameters:**
- `query.query` (string): Symbol name

**Returns:** `Symbol[]`

```javascript
const symbols = await client.find.symbols({
  query: { query: "createOpencode" }
})
```

### File Operations

#### client.file.read(query)

Read file contents.

**Parameters:**
- `query.path` (string): File path

**Returns:** `{ type: "raw" | "patch", content: string }`

```javascript
const file = await client.file.read({
  query: { path: "src/index.js" }
})
console.log(file.content)
```

#### client.file.status(query?)

Get file status for tracked files.

**Parameters:**
- `query` (object, optional): File filters

**Returns:** `File[]`

```javascript
const status = await client.file.status()
```

## Authentication API

### client.auth.set(path, body)

Set authentication credentials.

**Parameters:**
- `path.id` (string): Provider ID
- `body.type` (string): Credential type ("api")
- `body.key` (string): API key

**Returns:** `boolean`

```javascript
await client.auth.set({
  path: { id: "anthropic" },
  body: { type: "api", key: "api-key-here" }
})
```

## TUI API

### client.tui.appendPrompt(body)

Append text to the TUI prompt.

**Parameters:**
- `body.text` (string): Text to append

**Returns:** `boolean`

```javascript
await client.tui.appendPrompt({
  body: { text: "Additional prompt text" }
})
```

### client.tui.submitPrompt()

Submit the current prompt.

**Returns:** `boolean`

```javascript
await client.tui.submitPrompt()
```

### client.tui.clearPrompt()

Clear the prompt input.

**Returns:** `boolean`

```javascript
await client.tui.clearPrompt()
```

### client.tui.showToast(body)

Show toast notification.

**Parameters:**
- `body.message` (string): Toast message
- `body.variant` (string): "success", "error", "info", "warning"

**Returns:** `boolean`

```javascript
await client.tui.showToast({
  body: { message: "Task completed", variant: "success" }
})
```

### Other TUI Methods

- `tui.openHelp()`: Open help dialog
- `tui.openSessions()`: Open session selector
- `tui.openThemes()`: Open theme selector
- `tui.openModels()`: Open model selector
- `tui.executeCommand(body)`: Execute command

## Events API

### client.event.subscribe()

Subscribe to server-sent events.

**Returns:** Event stream

```javascript
const events = await client.event.subscribe()
for await (const event of events.stream) {
  console.log(event.type, event.properties)
}
```

## App API

### client.app.log(body)

Write application log entry.

**Parameters:**
- `body.service` (string): Service name
- `body.level` (string): Log level ("info", "warn", "error")
- `body.message` (string): Log message

**Returns:** `boolean`

```javascript
await client.app.log({
  body: {
    service: "my-app",
    level: "info",
    message: "Operation completed"
  }
})
```

### client.app.agents()

List available agents.

**Returns:** `Agent[]`

```javascript
const agents = await client.app.agents()
```

## Project API

### client.project.list()

List all projects.

**Returns:** `Project[]`

```javascript
const projects = await client.project.list()
```

### client.project.current()

Get current project.

**Returns:** `Project`

```javascript
const current = await client.project.current()
```

## Path API

### client.path.get()

Get current path information.

**Returns:** `Path`

```javascript
const pathInfo = await client.path.get()
```

## Config API

### client.config.get()

Get configuration information.

**Returns:** `Config`

```javascript
const config = await client.config.get()
```

### client.config.providers()

List providers and default models.

**Returns:** `{ providers: Provider[], default: { [key]: string } }`

```javascript
const { providers, default: defaults } = await client.config.providers()
```

## Type Definitions

### Session

```typescript
interface Session {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  messages: Message[]
  // ... other properties
}
```

### Message

```typescript
interface Message {
  id: string
  role: "user" | "assistant" | "system"
  createdAt: string
  content?: string
  // ... other properties
}
```

### Part

```typescript
interface Part {
  type: "text" | "image" | "file"
  text?: string
  // ... other properties based on type
}
```

### Model

```typescript
interface Model {
  providerID: string
  modelID: string
}
```

## Error Handling

All SDK methods can throw errors. Always wrap in try-catch:

```javascript
try {
  const session = await client.session.get({ path: { id: session.id } })
} catch (error) {
  console.error("Session error:", error.message)
}
```

Common error types:
- Network/connection errors
- Invalid session ID
- Authentication failures
- Invalid parameters