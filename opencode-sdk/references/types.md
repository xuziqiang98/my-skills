# OpenCode SDK TypeScript Types

Complete TypeScript type definitions and usage patterns for the OpenCode SDK.

## Table of Contents

- [Core Types](#core-types)
- [Session Types](#session-types)
- [Message Types](#message-types)
- [File Types](#file-types)
- [Authentication Types](#authentication-types)
- [Event Types](#event-types)
- [Configuration Types](#configuration-types)
- [API Response Types](#api-response-types)
- [Usage Patterns](#usage-patterns)

## Core Types

### Client

```typescript
interface Client {
  // Global API
  global: GlobalAPI
  
  // Session API
  session: SessionAPI
  
  // File operations
  find: FindAPI
  file: FileAPI
  
  // Authentication
  auth: AuthAPI
  
  // TUI control
  tui: TUIAPI
  
  // Events
  event: EventAPI
  
  // App management
  app: AppAPI
  
  // Project operations
  project: ProjectAPI
  
  // Path operations
  path: PathAPI
  
  // Configuration
  config: ConfigAPI
}
```

### Model Configuration

```typescript
interface Model {
  providerID: string
  modelID: string
}

interface ModelConfig {
  model?: string
  provider?: string
  temperature?: number
  maxTokens?: number
}
```

## Session Types

### Session

```typescript
interface Session {
  id: string
  title: string
  createdAt: string
  updatedAt: string
  status: "active" | "completed" | "aborted"
  messageCount: number
  lastActivity: string
  metadata?: Record<string, any>
}
```

### Session Creation

```typescript
interface CreateSessionRequest {
  body: {
    title: string
    metadata?: Record<string, any>
  }
}

interface CreateSessionResponse {
  data: Session
}
```

### Session Update

```typescript
interface UpdateSessionRequest {
  path: { id: string }
  body: {
    title?: string
    metadata?: Record<string, any>
  }
}
```

## Message Types

### Message

```typescript
interface Message {
  id: string
  sessionId: string
  role: "user" | "assistant" | "system"
  createdAt: string
  content?: string
  parts: Part[]
  metadata?: Record<string, any>
}
```

### Part

```typescript
type Part = TextPart | ImagePart | FilePart

interface TextPart {
  type: "text"
  text: string
}

interface ImagePart {
  type: "image"
  image: string // Base64 or URL
  alt?: string
}

interface FilePart {
  type: "file"
  file: string // File path or reference
  filename?: string
}
```

### Message Creation

```typescript
interface CreateMessageRequest {
  path: { id: string }
  body: {
    model?: Model
    parts: Part[]
    noReply?: boolean
  }
}

interface CreateMessageResponse {
  data: AssistantMessage
}
```

### Assistant Message

```typescript
interface AssistantMessage extends Message {
  role: "assistant"
  usage?: {
    inputTokens: number
    outputTokens: number
    totalTokens: number
  }
}
```

## File Types

### File Search

```typescript
interface FileSearchRequest {
  query: {
    query: string
    type?: "file" | "directory"
    directory?: string
    limit?: number
  }
}

interface FileSearchResponse {
  data: string[]
}
```

### Text Search

```typescript
interface TextSearchRequest {
  query: {
    pattern: string
    path?: string
  }
}

interface TextSearchResponse {
  data: Array<{
    path: string
    lines: string[]
    lineNumber: number
    absoluteOffset: number
    submatches: Array<{
      match: string
      start: number
      end: number
    }>
  }>
}
```

### Symbol Search

```typescript
interface SymbolSearchRequest {
  query: {
    query: string
  }
}

interface Symbol {
  name: string
  kind: string
  location: {
    path: string
    range: {
      start: { line: number; character: number }
      end: { line: number; character: number }
    }
  }
}

interface SymbolSearchResponse {
  data: Symbol[]
}
```

### File Operations

```typescript
interface FileReadRequest {
  query: {
    path: string
  }
}

interface FileReadResponse {
  data: {
    type: "raw" | "patch"
    content: string
  }
}

interface FileStatus {
  path: string
  status: "untracked" | "modified" | "added" | "deleted" | "renamed"
  changes?: number
}

interface FileStatusResponse {
  data: FileStatus[]
}
```

## Authentication Types

### Auth Request

```typescript
interface AuthSetRequest {
  path: { id: string }
  body: {
    type: "api" | "oauth"
    key?: string
    token?: string
    [key: string]: any
  }
}

interface AuthSetResponse {
  data: boolean
}
```

### Provider

```typescript
interface Provider {
  id: string
  name: string
  models: Model[]
  capabilities: string[]
}
```

## Event Types

### Event Stream

```typescript
interface EventStream {
  stream: AsyncIterable<Event>
}

interface Event {
  type: string
  properties: Record<string, any>
  timestamp: string
}
```

### Common Event Types

```typescript
interface SessionCreatedEvent extends Event {
  type: "session.created"
  properties: {
    id: string
    title: string
  }
}

interface SessionDeletedEvent extends Event {
  type: "session.deleted"
  properties: {
    id: string
  }
}

interface MessageAddedEvent extends Event {
  type: "message.added"
  properties: {
    sessionId: string
    messageId: string
    role: string
  }
}

interface FileChangedEvent extends Event {
  type: "file.changed"
  properties: {
    path: string
    status: string
  }
}
```

## Configuration Types

### Config

```typescript
interface Config {
  model?: string
  provider?: string
  temperature?: number
  maxTokens?: number
  systemPrompt?: string
  tools?: string[]
  permissions?: string[]
  [key: string]: any
}
```

### Provider Config

```typescript
interface ProviderConfig {
  providers: Provider[]
  default: {
    [providerId: string]: string
  }
}
```

### Project Config

```typescript
interface Project {
  id: string
  name: string
  path: string
  config?: Config
  createdAt: string
  updatedAt: string
}
```

## API Response Types

### Standard Response

```typescript
interface APIResponse<T> {
  data: T
  success: boolean
  error?: string
  metadata?: Record<string, any>
}
```

### List Response

```typescript
interface ListResponse<T> {
  data: T[]
  total: number
  page?: number
  limit?: number
}
```

### Error Response

```typescript
interface ErrorResponse {
  error: {
    code: string
    message: string
    details?: Record<string, any>
  }
  success: false
}
```

## Usage Patterns

### Type-Safe Client Creation

```typescript
import { createOpencode, type Client, type Config } from "@opencode-ai/sdk"

async function createTypedClient(config: Config): Promise<Client> {
  const { client } = await createOpencode({
    config
  })
  return client
}
```

### Type-Safe Session Management

```typescript
import type { 
  Session, 
  CreateSessionRequest, 
  CreateMessageRequest,
  AssistantMessage 
} from "@opencode-ai/sdk"

async function createTypedSession(
  client: Client,
  title: string
): Promise<Session> {
  const request: CreateSessionRequest = {
    body: { title }
  }
  
  const response = await client.session.create(request)
  return response.data
}

async function sendTypedMessage(
  client: Client,
  sessionId: string,
  text: string
): Promise<AssistantMessage> {
  const request: CreateMessageRequest = {
    path: { id: sessionId },
    body: {
      parts: [{ type: "text", text }]
    }
  }
  
  const response = await client.session.prompt(request)
  return response.data
}
```

### Type-Safe Event Handling

```typescript
import type { EventStream, SessionCreatedEvent, MessageAddedEvent } from "@opencode-ai/sdk"

async function handleTypedEvents(client: Client): Promise<void> {
  const events: EventStream = await client.event.subscribe()
  
  for await (const event of events.stream) {
    switch (event.type) {
      case "session.created":
        const sessionEvent = event as SessionCreatedEvent
        console.log("Session created:", sessionEvent.properties.id)
        break
        
      case "message.added":
        const messageEvent = event as MessageAddedEvent
        console.log("Message added:", messageEvent.properties.messageId)
        break
    }
  }
}
```

### Generic Type Helpers

```typescript
// Helper for API responses
type APIResult<T> = Promise<{
  data: T
  success: boolean
  error?: string
}>

// Helper for creating typed requests
function createRequest<T>(body: T): { body: T } {
  return { body }
}

function createPathRequest<T>(path: T, body?: any): { path: T; body?: any } {
  return { path, body }
}

// Helper for type-safe event handling
type EventHandler<T extends Event> = (event: T) => void | Promise<void>

interface TypedEventHandlers {
  "session.created": EventHandler<SessionCreatedEvent>
  "session.deleted": EventHandler<SessionDeletedEvent>
  "message.added": EventHandler<MessageAddedEvent>
  "file.changed": EventHandler<FileChangedEvent>
}
```

### Custom Type Extensions

```typescript
// Extend with custom metadata
interface CustomSession extends Session {
  customData: {
    project: string
    environment: "dev" | "staging" | "prod"
    tags: string[]
  }
}

// Custom event types
interface CustomEvent extends Event {
  type: "custom.action"
  properties: {
    action: string
    userId: string
    timestamp: string
  }
}

// Type guards
function isCustomEvent(event: Event): event is CustomEvent {
  return event.type === "custom.action"
}

function isAssistantMessage(message: Message): message is AssistantMessage {
  return message.role === "assistant"
}
```

### Error Type Handling

```typescript
// Custom error types
class OpenCodeError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: Record<string, any>
  ) {
    super(message)
    this.name = "OpenCodeError"
  }
}

class SessionNotFoundError extends OpenCodeError {
  constructor(sessionId: string) {
    super(`Session not found: ${sessionId}`, "SESSION_NOT_FOUND")
    this.name = "SessionNotFoundError"
  }
}

class AuthenticationError extends OpenCodeError {
  constructor(provider: string) {
    super(`Authentication failed for provider: ${provider}`, "AUTH_ERROR")
    this.name = "AuthenticationError"
  }
}

// Type-safe error handling
async function handleAPICall<T>(
  operation: () => Promise<T>
): Promise<T> {
  try {
    return await operation()
  } catch (error) {
    if (error instanceof OpenCodeError) {
      console.error(`OpenCode Error [${error.code}]: ${error.message}`)
      throw error
    }
    throw new OpenCodeError(
      "Unexpected error",
      "UNKNOWN_ERROR",
      { originalError: error }
    )
  }
}
```

## Import Patterns

### Complete Type Import

```typescript
// Import all types
import * as OpenCode from "@opencode-ai/sdk"
import type { 
  Client,
  Session,
  Message,
  Part,
  Model,
  Event,
  Config
} from "@opencode-ai/sdk"
```

### Selective Type Import

```typescript
// Import only needed types
import type { 
  Session as OpenCodeSession,
  CreateSessionRequest,
  AssistantMessage 
} from "@opencode-ai/sdk"

// Use with type alias
type MySession = OpenCodeSession & {
  customField: string
}
```

### Ambient Types

```typescript
// For global type declarations
declare global {
  namespace OpenCode {
    interface CustomMetadata {
      userId: string
      sessionId: string
    }
  }
}
```