# OpenCode SDK Error Handling

Complete error handling patterns, debugging strategies, and solutions for the OpenCode SDK.

## Table of Contents

- [Common Error Types](#common-error-types)
- [Error Handling Patterns](#error-handling-patterns)
- [Debugging Strategies](#debugging-strategies)
- [Specific Error Solutions](#specific-error-solutions)
- [Retry Patterns](#retry-patterns)
- [Logging and Monitoring](#logging-and-monitoring)
- [Best Practices](#best-practices)

## Common Error Types

### Connection Errors

```typescript
// Server not running or unreachable
class ConnectionError extends Error {
  constructor(message: string) {
    super(message)
    this.name = "ConnectionError"
  }
}

// Example scenarios
try {
  const client = createOpencodeClient({ baseUrl: "http://localhost:4096" })
} catch (error) {
  if (error instanceof ConnectionError) {
    console.error("Cannot connect to OpenCode server:", error.message)
  }
}
```

### Authentication Errors

```typescript
// Invalid API keys or credentials
class AuthenticationError extends Error {
  constructor(provider: string, message: string) {
    super(`Authentication failed for ${provider}: ${message}`)
    this.name = "AuthenticationError"
  }
}

// Example
try {
  await client.auth.set({
    path: { id: "anthropic" },
    body: { type: "api", key: "invalid-key" }
  })
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error("Auth error:", error.message)
  }
}
```

### Session Errors

```typescript
// Session not found or invalid
class SessionError extends Error {
  constructor(sessionId: string, message: string) {
    super(`Session error for ${sessionId}: ${message}`)
    this.name = "SessionError"
  }
}

// Example
try {
  await client.session.get({ path: { id: "invalid-session-id" } })
} catch (error) {
  if (error instanceof SessionError) {
    console.error("Session error:", error.message)
  }
}
```

### File Operation Errors

```typescript
// File not found or permission denied
class FileOperationError extends Error {
  constructor(operation: string, path: string, message: string) {
    super(`File ${operation} failed for ${path}: ${message}`)
    this.name = "FileOperationError"
  }
}

// Example
try {
  await client.file.read({ query: { path: "nonexistent/file.ts" } })
} catch (error) {
  if (error instanceof FileOperationError) {
    console.error("File error:", error.message)
  }
}
```

## Error Handling Patterns

### Basic Try-Catch Pattern

```typescript
import { createOpencodeClient } from "@opencode-ai/sdk"

async function safeClientOperation() {
  const client = createOpencodeClient({ baseUrl: "http://localhost:4096" })
  
  try {
    const sessions = await client.session.list()
    return sessions.data
  } catch (error) {
    console.error("Operation failed:", error.message)
    return null
  }
}
```

### Type-Safe Error Handling

```typescript
interface APIResult<T> {
  success: boolean
  data?: T
  error?: string
}

async function handleAPICall<T>(
  operation: () => Promise<T>
): Promise<APIResult<T>> {
  try {
    const data = await operation()
    return { success: true, data }
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : "Unknown error"
    }
  }
}

// Usage
const result = await handleAPICall(() => client.session.list())
if (!result.success) {
  console.error("Failed to list sessions:", result.error)
}
```

### Error Boundary Pattern

```typescript
class OpenCodeErrorBoundary {
  private client: any
  private maxRetries: number = 3

  constructor(client: any, maxRetries: number = 3) {
    this.client = client
    this.maxRetries = maxRetries
  }

  async executeWithRetry<T>(
    operation: () => Promise<T>,
    operationName: string
  ): Promise<T> {
    let lastError: Error
    
    for (let attempt = 1; attempt <= this.maxRetries; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error as Error
        console.warn(`${operationName} failed (attempt ${attempt}/${this.maxRetries}):`, error.message)
        
        if (attempt < this.maxRetries) {
          await this.delay(1000 * attempt) // Exponential backoff
        }
      }
    }
    
    throw new Error(`${operationName} failed after ${this.maxRetries} attempts: ${lastError.message}`)
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}
```

## Debugging Strategies

### Enable Debug Logging

```typescript
// Create client with debug mode
const client = createOpencodeClient({
  baseUrl: "http://localhost:4096",
  // Add custom fetch for debugging
  fetch: async (url: string, options?: RequestInit) => {
    console.log(`[DEBUG] Request: ${options?.method || 'GET'} ${url}`)
    console.log(`[DEBUG] Headers:`, options?.headers)
    
    const response = await fetch(url, options)
    
    console.log(`[DEBUG] Response: ${response.status} ${response.statusText}`)
    
    return response
  }
})
```

### Health Check Before Operations

```typescript
async function ensureServerHealth(client: any): Promise<boolean> {
  try {
    const health = await client.global.health()
    console.log("Server health:", health.data)
    return health.data.healthy
  } catch (error) {
    console.error("Health check failed:", error)
    return false
  }
}

// Usage
if (await ensureServerHealth(client)) {
  // Proceed with operations
} else {
  console.error("Server is not healthy")
}
```

### Request/Response Logging

```typescript
function createLoggingClient(baseUrl: string) {
  return createOpencodeClient({
    baseUrl,
    fetch: async (url: string, options?: RequestInit) => {
      const requestId = Math.random().toString(36).substr(2, 9)
      console.log(`[${requestId}] → ${options?.method || 'GET'} ${url}`)
      
      if (options?.body) {
        console.log(`[${requestId}] Body:`, options.body)
      }
      
      const startTime = Date.now()
      const response = await fetch(url, options)
      const duration = Date.now() - startTime
      
      console.log(`[${requestId}] ← ${response.status} (${duration}ms)`)
      
      return response
    }
  })
}
```

## Specific Error Solutions

### Session Not Found

```typescript
async function safeGetSession(client: any, sessionId: string) {
  try {
    const session = await client.session.get({ path: { id: sessionId } })
    return session.data
  } catch (error) {
    if (error.message.includes("not found")) {
      console.log(`Session ${sessionId} not found, creating new session...`)
      const newSession = await client.session.create({
        body: { title: `Session ${sessionId}` }
      })
      return newSession.data
    }
    throw error
  }
}
```

### Authentication Timeout

```typescript
async function safeAuthSetup(client: any, provider: string, credentials: any) {
  const timeout = 10000 // 10 seconds
  
  try {
    const result = await Promise.race([
      client.auth.set({
        path: { id: provider },
        body: credentials
      }),
      new Promise((_, reject) => 
        setTimeout(() => reject(new Error("Auth timeout")), timeout)
      )
    ])
    
    return result
  } catch (error) {
    if (error.message === "Auth timeout") {
      console.error("Authentication setup timed out")
      // Fallback: try cached credentials or alternative auth method
    }
    throw error
  }
}
```

### File Permission Errors

```typescript
async function safeFileRead(client: any, path: string): Promise<string | null> {
  try {
    const file = await client.file.read({ query: { path } })
    return file.data.content
  } catch (error) {
    if (error.message.includes("permission denied")) {
      console.warn(`Permission denied for file: ${path}`)
      return null
    }
    if (error.message.includes("not found")) {
      console.warn(`File not found: ${path}`)
      return null
    }
    throw error
  }
}
```

## Retry Patterns

### Exponential Backoff

```typescript
async function exponentialBackoff<T>(
  operation: () => Promise<T>,
  maxRetries: number = 3,
  baseDelay: number = 1000
): Promise<T> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      if (attempt === maxRetries) {
        throw error
      }
      
      const delay = baseDelay * Math.pow(2, attempt - 1)
      console.log(`Retrying in ${delay}ms (attempt ${attempt}/${maxRetries})`)
      await new Promise(resolve => setTimeout(resolve, delay))
    }
  }
  
  throw new Error("Max retries exceeded")
}

// Usage
const sessions = await exponentialBackoff(
  () => client.session.list(),
  3,
  1000
)
```

### Conditional Retry

```typescript
async function conditionalRetry<T>(
  operation: () => Promise<T>,
  shouldRetry: (error: Error) => boolean,
  maxRetries: number = 3
): Promise<T> {
  let lastError: Error
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation()
    } catch (error) {
      lastError = error as Error
      
      if (!shouldRetry(lastError) || attempt === maxRetries) {
        throw lastError
      }
      
      console.log(`Retrying due to: ${lastError.message}`)
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt))
    }
  }
  
  throw lastError
}

// Usage: Only retry on connection errors
const sessions = await conditionalRetry(
  () => client.session.list(),
  (error) => error.message.includes("ECONNREFUSED") || error.message.includes("timeout"),
  3
)
```

## Logging and Monitoring

### Structured Logging

```typescript
interface LogEntry {
  timestamp: string
  level: "info" | "warn" | "error" | "debug"
  operation: string
  sessionId?: string
  duration?: number
  error?: string
  metadata?: Record<string, any>
}

class OpenCodeLogger {
  private logs: LogEntry[] = []
  
  log(entry: Omit<LogEntry, "timestamp">) {
    const logEntry: LogEntry = {
      timestamp: new Date().toISOString(),
      ...entry
    }
    
    this.logs.push(logEntry)
    console.log(JSON.stringify(logEntry))
  }
  
  info(operation: string, metadata?: Record<string, any>) {
    this.log({ level: "info", operation, metadata })
  }
  
  error(operation: string, error: string, metadata?: Record<string, any>) {
    this.log({ level: "error", operation, error, metadata })
  }
  
  getLogs(): LogEntry[] {
    return this.logs
  }
}

// Usage
const logger = new OpenCodeLogger()

async function loggedSessionOperation(client: any, title: string) {
  const startTime = Date.now()
  
  try {
    logger.info("session.create", { title })
    
    const session = await client.session.create({ body: { title } })
    
    const duration = Date.now() - startTime
    logger.info("session.create.success", { 
      sessionId: session.data.id,
      duration 
    })
    
    return session.data
  } catch (error) {
    const duration = Date.now() - startTime
    logger.error("session.create.failed", error.message, { title, duration })
    throw error
  }
}
```

### Error Metrics

```typescript
class ErrorMetrics {
  private errors: Map<string, number> = new Map()
  private operations: Map<string, number> = new Map()
  
  recordOperation(operation: string) {
    this.operations.set(operation, (this.operations.get(operation) || 0) + 1)
  }
  
  recordError(operation: string, error: string) {
    const key = `${operation}:${error}`
    this.errors.set(key, (this.errors.get(key) || 0) + 1)
  }
  
  getErrorRate(operation: string): number {
    const totalOps = this.operations.get(operation) || 0
    const totalErrors = Array.from(this.errors.keys())
      .filter(key => key.startsWith(operation))
      .reduce((sum, key) => sum + this.errors.get(key)!, 0)
    
    return totalOps > 0 ? totalErrors / totalOps : 0
  }
  
  getReport(): Record<string, any> {
    return {
      operations: Object.fromEntries(this.operations),
      errors: Object.fromEntries(this.errors),
      errorRates: Array.from(this.operations.keys()).reduce((rates, op) => {
        rates[op] = this.getErrorRate(op)
        return rates
      }, {} as Record<string, number>)
    }
  }
}
```

## Best Practices

### 1. Always Wrap SDK Calls

```typescript
// Good: Always handle errors
async function createSession(title: string) {
  try {
    const session = await client.session.create({ body: { title } })
    return session.data
  } catch (error) {
    console.error("Failed to create session:", error.message)
    throw error
  }
}

// Bad: No error handling
async function createSession(title: string) {
  const session = await client.session.create({ body: { title } })
  return session.data
}
```

### 2. Use Type Guards

```typescript
function isOpenCodeError(error: unknown): error is Error {
  return error instanceof Error && error.message !== undefined
}

function isConnectionError(error: Error): boolean {
  return error.message.includes("ECONNREFUSED") || 
         error.message.includes("timeout") ||
         error.message.includes("ENOTFOUND")
}

// Usage
try {
  await client.session.list()
} catch (error) {
  if (!isOpenCodeError(error)) {
    console.error("Unknown error type:", error)
    return
  }
  
  if (isConnectionError(error)) {
    console.error("Connection issue - check server status")
  }
}
```

### 3. Provide Context in Errors

```typescript
class ContextualError extends Error {
  constructor(
    message: string,
    public operation: string,
    public context: Record<string, any>,
    public cause?: Error
  ) {
    super(message)
    this.name = "ContextualError"
  }
}

async function contextualSessionOperation(title: string) {
  try {
    return await client.session.create({ body: { title } })
  } catch (error) {
    throw new ContextualError(
      "Session creation failed",
      "session.create",
      { title, timestamp: new Date().toISOString() },
      error as Error
    )
  }
}
```

### 4. Graceful Degradation

```typescript
async function getSessionsWithFallback(client: any) {
  try {
    // Try to get fresh sessions
    const sessions = await client.session.list()
    return sessions.data
  } catch (error) {
    console.warn("Failed to get sessions, using cached data:", error.message)
    
    // Fallback to cached or default data
    return []
  }
}
```

### 5. Resource Cleanup

```typescript
async function withClient<T>(
  clientFactory: () => any,
  operation: (client: any) => Promise<T>
): Promise<T> {
  const client = clientFactory()
  
  try {
    return await operation(client)
  } finally {
    // Cleanup if needed
    // client.close?.()
  }
}

// Usage
const result = await withClient(
  () => createOpencodeClient({ baseUrl: "http://localhost:4096" }),
  async (client) => {
    return await client.session.list()
  }
)
```

### 6. Input Validation

```typescript
function validateSessionTitle(title: string): void {
  if (!title || title.trim().length === 0) {
    throw new Error("Session title cannot be empty")
  }
  
  if (title.length > 100) {
    throw new Error("Session title too long (max 100 characters)")
  }
  
  if (!/^[a-zA-Z0-9\s\-_]+$/.test(title)) {
    throw new Error("Session title contains invalid characters")
  }
}

async function createValidatedSession(title: string) {
  validateSessionTitle(title)
  
  try {
    return await client.session.create({ body: { title: title.trim() } })
  } catch (error) {
    console.error("Failed to create validated session:", error.message)
    throw error
  }
}
```

### 7. Timeout Handling

```typescript
async function withTimeout<T>(
  promise: Promise<T>,
  timeoutMs: number,
  timeoutMessage: string = "Operation timed out"
): Promise<T> {
  const timeoutPromise = new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error(timeoutMessage)), timeoutMs)
  })
  
  return Promise.race([promise, timeoutPromise])
}

// Usage
const sessions = await withTimeout(
  client.session.list(),
  5000,
  "Session listing timed out"
)
```

This comprehensive error handling guide provides patterns, strategies, and solutions for working with the OpenCode SDK effectively and safely.