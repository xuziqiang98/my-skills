# OpenCode SDK Examples

Comprehensive code examples for common OpenCode SDK workflows and patterns.

## Table of Contents

- [Quick Start Examples](#quick-start-examples)
- [Session Management](#session-management)
- [File Operations](#file-operations)
- [Authentication](#authentication)
- [Event Handling](#event-handling)
- [Error Handling](#error-handling)
- [TypeScript Examples](#typescript-examples)
- [Integration Patterns](#integration-patterns)

## Quick Start Examples

### Basic Client Setup

```javascript
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()
console.log("OpenCode client ready")
```

### Connect to Existing Server

```javascript
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({ 
  baseUrl: "http://localhost:4096" 
})
```

### Custom Configuration

```javascript
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode({
  hostname: "127.0.0.1",
  port: 4096,
  config: {
    model: "anthropic/claude-3-5-sonnet-20241022",
  },
})
```

## Session Management

### Create and Use Session

```javascript
const session = await client.session.create({
  body: { title: "My Development Session" }
})

const response = await client.session.prompt({
  path: { id: session.id },
  body: {
    model: { 
      providerID: "anthropic", 
      modelID: "claude-3-5-sonnet-20241022" 
    },
    parts: [{ 
      type: "text", 
      text: "Help me debug this React component" 
    }]
  }
})
```

### List and Manage Sessions

```javascript
const sessions = await client.session.list()

for (const session of sessions.data) {
  console.log(`${session.id}: ${session.title}`)
  
  if (session.title.includes("old")) {
    await client.session.delete({
      path: { id: session.id }
    })
    console.log(`Deleted old session: ${session.id}`)
  }
}
```

### Session with Context Only

```javascript
await client.session.prompt({
  path: { id: session.id },
  body: {
    noReply: true,
    parts: [{ 
      type: "text", 
      text: "You are a React expert. Focus on performance and best practices." 
    }]
  }
})
```

### Command Execution

```javascript
const result = await client.session.command({
  path: { id: session.id },
  body: { command: "/check-file src/components/Button.jsx" }
})
```

## File Operations

### Search Files

```javascript
const jsFiles = await client.find.files({
  query: { 
    query: "*.jsx", 
    type: "file",
    limit: 50 
  }
})

const componentFiles = await client.find.files({
  query: { 
    query: "src/components/*", 
    type: "file" 
  }
})
```

### Search Text in Files

```javascript
const functionMatches = await client.find.text({
  query: { pattern: "export.*function.*Component" }
})

for (const match of functionMatches) {
  console.log(`Found in ${match.path}:`)
  console.log(match.lines)
}
```

### Read File Content

```javascript
const fileContent = await client.file.read({
  query: { path: "src/App.jsx" }
})

if (fileContent.type === "raw") {
  console.log(fileContent.content)
}
```

### Get File Status

```javascript
const fileStatus = await client.file.status()

for (const file of fileStatus) {
  if (file.status === "modified") {
    console.log(`Modified: ${file.path}`)
  }
}
```

## Authentication

### Single Provider Setup

```javascript
await client.auth.set({
  path: { id: "anthropic" },
  body: { 
    type: "api", 
    key: process.env.ANTHROPIC_API_KEY 
  },
})
```

### Multiple Provider Setup

```javascript
const providers = [
  { id: "anthropic", key: process.env.ANTHROPIC_API_KEY },
  { id: "openai", key: process.env.OPENAI_API_KEY },
  { id: "google", key: process.env.GOOGLE_API_KEY }
]

for (const provider of providers) {
  if (provider.key) {
    await client.auth.set({
      path: { id: provider.id },
      body: { type: "api", key: provider.key }
    })
  }
}
```

### Authentication with Validation

```javascript
async function setupAuth(providerId, apiKey) {
  try {
    await client.auth.set({
      path: { id: providerId },
      body: { type: "api", key: apiKey }
    })
    
    const testSession = await client.session.create({
      body: { title: "Auth Test" }
    })
    
    await client.session.delete({
      path: { id: testSession.id }
    })
    
    console.log(`✅ ${providerId} authentication verified`)
  } catch (error) {
    console.error(`❌ ${providerId} setup failed:`, error.message)
  }
}
```

## Event Handling

### Basic Event Listener

```javascript
const events = await client.event.subscribe()

for await (const event of events.stream) {
  console.log(`${event.type}:`, event.properties)
}
```

### Filtered Event Listener

```javascript
const events = await client.event.subscribe()

for await (const event of events.stream) {
  if (["session.created", "message.added"].includes(event.type)) {
    console.log(`🔔 ${event.type}:`, event.properties)
  }
}
```

### Event Handler with Actions

```javascript
const events = await client.event.subscribe()

for await (const event of events.stream) {
  switch (event.type) {
    case "session.created":
      console.log(`🆕 New session: ${event.properties.id}`)
      break
      
    case "file.changed":
      console.log(`📁 File modified: ${event.properties.path}`)
      break
      
    case "message.added":
      console.log(`💬 New message in session: ${event.properties.sessionId}`)
      break
  }
}
```

### Persistent Event Listener

```javascript
async function startEventListener() {
  while (true) {
    try {
      const { client } = await createOpencode()
      const events = await client.event.subscribe()

      for await (const event of events.stream) {
        console.log(`[${new Date().toISOString()}] ${event.type}`)
      }
    } catch (error) {
      console.error("Event listener error:", error.message)
      await new Promise(resolve => setTimeout(resolve, 5000))
    }
  }
}
```

## Error Handling

### Basic Error Handling

```javascript
try {
  const session = await client.session.get({
    path: { id: "invalid-id" }
  })
} catch (error) {
  console.error("Session error:", error.message)
}
```

### Robust Error Handling

```javascript
async function safeSessionOperation(sessionId, operation) {
  try {
    return await operation(sessionId)
  } catch (error) {
    if (error.message.includes("not found")) {
      console.log("Session not found, creating new one...")
      const newSession = await client.session.create({
        body: { title: "Replacement Session" }
      })
      return await operation(newSession.id)
    } else if (error.message.includes("unauthorized")) {
      console.error("Authentication required")
      throw error
    } else {
      console.error("Unexpected error:", error.message)
      throw error
    }
  }
}
```

### Retry Pattern

```javascript
async function retryOperation(operation, maxRetries = 3) {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      if (attempt === maxRetries) {
        throw error
      }
      console.log(`Attempt ${attempt} failed, retrying...`)
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt))
    }
  }
}
```

## TypeScript Examples

### Typed Session Creation

```javascript
import type { Session, Message, Part } from "@opencode-ai/sdk"

const session: Session = await client.session.create({
  body: { title: "Typed Session" }
})

const message = await client.session.prompt({
  path: { id: session.id },
  body: {
    model: { 
      providerID: "anthropic", 
      modelID: "claude-3-5-sonnet-20241022" 
    },
    parts: [{ type: "text", text: "Hello!" }] as Part[]
  }
})
```

### Type-Safe Event Handling

```javascript
interface SessionEvent {
  type: "session.created" | "session.deleted"
  properties: { id: string }
}

interface MessageEvent {
  type: "message.added"
  properties: { sessionId: string; messageId: string }
}

const events = await client.event.subscribe()

for await (const event of events.stream) {
  if (event.type === "session.created") {
    const sessionEvent = event as SessionEvent
    console.log("Session created:", sessionEvent.properties.id)
  }
}
```

## Integration Patterns

### Plugin Pattern

```javascript
class OpenCodePlugin {
  constructor(client) {
    this.client = client
  }
  
  async initialize() {
    await this.client.auth.set({
      path: { id: "anthropic" },
      body: { type: "api", key: process.env.ANTHROPIC_API_KEY }
    })
  }
  
  async createTaskSession(task) {
    const session = await this.client.session.create({
      body: { title: `Task: ${task.name}` }
    })
    
    await this.client.session.prompt({
      path: { id: session.id },
      body: {
        noReply: true,
        parts: [{ 
          type: "text", 
          text: `You are working on task: ${task.description}` 
        }]
      }
    })
    
    return session.id
  }
}
```

### Batch Processing Pattern

```javascript
async function processBatchSessions(sessions) {
  const results = []
  
  for (const sessionConfig of sessions) {
    try {
      const session = await client.session.create({
        body: { title: sessionConfig.title }
      })
      
      const response = await client.session.prompt({
        path: { id: session.id },
        body: {
          model: sessionConfig.model,
          parts: [{ type: "text", text: sessionConfig.prompt }]
        }
      })
      
      results.push({
        sessionId: session.id,
        response: response.parts[0].text,
        success: true
      })
    } catch (error) {
      results.push({
        sessionId: sessionConfig.title,
        error: error.message,
        success: false
      })
    }
  }
  
  return results
}
```

### Configuration Management

```javascript
class OpenCodeManager {
  constructor(config = {}) {
    this.config = {
      hostname: "127.0.0.1",
      port: 4096,
      defaultModel: "anthropic/claude-3-5-sonnet-20241022",
      ...config
    }
    this.client = null
  }
  
  async connect() {
    const { client } = await createOpencode({
      hostname: this.config.hostname,
      port: this.config.port,
      config: { model: this.config.defaultModel }
    })
    this.client = client
    return client
  }
  
  async setupAuthentication(providers) {
    for (const [id, config] of Object.entries(providers)) {
      if (config.apiKey) {
        await this.client.auth.set({
          path: { id },
          body: { type: "api", key: config.apiKey }
        })
      }
    }
  }
}
```

### Monitoring and Analytics

```javascript
class OpenCodeMonitor {
  constructor(client) {
    this.client = client
    this.stats = {
      sessions: 0,
      messages: 0,
      errors: 0,
      startTime: Date.now()
    }
  }
  
  async startMonitoring() {
    const events = await this.client.event.subscribe()
    
    for await (const event of events.stream) {
      this.updateStats(event)
    }
  }
  
  updateStats(event) {
    switch (event.type) {
      case "session.created":
        this.stats.sessions++
        break
      case "message.added":
        this.stats.messages++
        break
      case "error":
        this.stats.errors++
        break
    }
  }
  
  getReport() {
    const duration = Date.now() - this.stats.startTime
    return {
      ...this.stats,
      duration,
      sessionsPerHour: (this.stats.sessions / duration) * 3600000,
      messagesPerHour: (this.stats.messages / duration) * 3600000
    }
  }
}
```

## Common Patterns

### Session Pool Management

```javascript
class SessionPool {
  constructor(client, maxSize = 5) {
    this.client = client
    this.maxSize = maxSize
    this.available = []
    this.inUse = new Set()
  }
  
  async getSession() {
    if (this.available.length > 0) {
      const sessionId = this.available.pop()
      this.inUse.add(sessionId)
      return sessionId
    }
    
    if (this.inUse.size < this.maxSize) {
      const session = await this.client.session.create({
        body: { title: "Pool Session" }
      })
      this.inUse.add(session.id)
      return session.id
    }
    
    throw new Error("Session pool exhausted")
  }
  
  releaseSession(sessionId) {
    if (this.inUse.has(sessionId)) {
      this.inUse.delete(sessionId)
      this.available.push(sessionId)
    }
  }
}
```

### Context Builder

```javascript
class ContextBuilder {
  constructor() {
    this.context = []
  }
  
  addSystemPrompt(prompt) {
    this.context.push({
      type: "text",
      text: `System: ${prompt}`
    })
    return this
  }
  
  addFileContext(filePath, description) {
    this.context.push({
      type: "text",
      text: `File: ${filePath} - ${description}`
    })
    return this
  }
  
  addProjectContext(projectInfo) {
    this.context.push({
      type: "text",
      text: `Project: ${JSON.stringify(projectInfo, null, 2)}`
    })
    return this
  }
  
  build() {
    return this.context
  }
}
```