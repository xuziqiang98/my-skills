---
name: opencode-sdk
description: Comprehensive OpenCode SDK integration toolkit for client creation, session management, file operations, authentication, and real-time events. Use when Claude needs to build integrations with OpenCode server, generate SDK code, create automation scripts, or implement any functionality using the @opencode-ai/sdk package. Includes code generators, API reference, templates, and examples for all SDK workflows.
---

# OpenCode SDK Integration Toolkit

## Overview

Complete toolkit for building integrations and applications with the OpenCode JavaScript/TypeScript SDK. Provides code generation, templates, and comprehensive examples for client setup, session management, file operations, authentication, and real-time event handling.

## Quick Start

### 1. Installation and Basic Setup

```bash
npm install @opencode-ai/sdk
```

**Create a basic client:**
```javascript
import { createOpencode } from "@opencode-ai/sdk"
const { client } = await createOpencode()
```

**Connect to existing server:**
```javascript
import { createOpencodeClient } from "@opencode-ai/sdk"
const client = createOpencodeClient({ 
  baseUrl: "http://localhost:4096" 
})
```

### 2. Common Workflows

- **Session Management**: Create, list, prompt, and manage OpenCode sessions
- **File Operations**: Search, read, and get file status information
- **Authentication**: Set up API keys and credentials
- **Real-time Events**: Listen to server-sent events
- **TUI Control**: Automate terminal user interface interactions

## Core Capabilities

### 1. Client Creation and Configuration

Generate client setup code with proper configuration:

```javascript
// Full configuration example
const { client } = await createOpencode({
  hostname: "127.0.0.1",
  port: 4096,
  config: {
    model: "anthropic/claude-3-5-sonnet-20241022",
  },
})
```

### 2. Session Management

Complete session lifecycle operations:

```javascript
// Create session
const session = await client.session.create({
  body: { title: "My session" }
})

// Send prompt
const result = await client.session.prompt({
  path: { id: session.id },
  body: {
    model: { providerID: "anthropic", modelID: "claude-3-5-sonnet-20241022" },
    parts: [{ type: "text", text: "Hello!" }]
  }
})
```

### 3. File Operations

Search and file system operations:

```javascript
// Search text
const textResults = await client.find.text({
  query: { pattern: "function.*opencode" }
})

// Find files
const files = await client.find.files({
  query: { query: "*.ts", type: "file" }
})

// Read file
const content = await client.file.read({
  query: { path: "src/index.ts" }
})
```

### 4. Authentication Setup

Configure authentication for different providers:

```javascript
await client.auth.set({
  path: { id: "anthropic" },
  body: { type: "api", key: "your-api-key" }
})
```

### 5. Real-time Events

Listen to server-sent events:

```javascript
const events = await client.event.subscribe()
for await (const event of events.stream) {
  console.log("Event:", event.type, event.properties)
}
```

### 6. TUI Automation

Control the terminal interface:

```javascript
await client.tui.appendPrompt({
  body: { text: "Add this to prompt" }
})

await client.tui.showToast({
  body: { message: "Task completed", variant: "success" }
})
```

## Error Handling Patterns

Always wrap SDK calls in try-catch blocks:

```javascript
try {
  await client.session.get({ path: { id: "invalid-id" } })
} catch (error) {
  console.error("Failed to get session:", error.message)
}
```

## Integration Templates

Use the templates in `assets/` for different integration types:
- `basic_client/` - Minimal client setup
- `integration_template/` - Full integration project

## Type Safety

Import TypeScript definitions:

```javascript
import type { Session, Message, Part } from "@opencode-ai/sdk"
```

All API methods are fully typed for better development experience.

## Resources

### scripts/
Code generators and utilities for SDK integration:

- `setup_client.js` - Generate client creation code with configuration
- `session_manager.js` - Session management helpers and patterns
- `auth_setup.js` - Authentication setup utilities
- `event_listener.js` - Event handling patterns and generators

### references/
Comprehensive documentation and guides:

- `api_reference.md` - Complete API method reference with examples
- `examples.md` - Code examples for common workflows and patterns
- `types.md` - TypeScript type definitions and usage patterns
- `error_handling.md` - Error patterns, debugging, and solutions

### assets/
Templates and boilerplate for integration projects:

- `basic_client/` - Minimal client setup template
- `integration_template/` - Full integration project structure
- `config_examples/` - Configuration examples for different use cases

### When to Use Each Resource

**Use scripts when**: You need to generate code, automate setup, or create SDK utilities
**Use references when**: You need API details, examples, or implementation guidance
**Use assets when**: You need project templates, boilerplate code, or configuration files
