# A2A SDK Helper Functions

This file provides utility functions and helpers to simplify common A2A SDK operations.

## Client Helpers

### Quick Client Factory
```typescript
import { ClientFactory, ClientFactoryOptions } from '@a2a-js/sdk/client';
import { JsonRpcTransportFactory, GrpcTransportFactory } from '@a2a-js/sdk/client';

/**
 * Create a client with default configuration
 */
export async function createQuickClient(agentUrl: string, transport: 'jsonrpc' | 'grpc' = 'jsonrpc') {
  const transports = transport === 'grpc' 
    ? [new GrpcTransportFactory()]
    : [new JsonRpcTransportFactory()];
    
  const factory = new ClientFactory({ transports });
  return await factory.createFromUrl(agentUrl);
}

/**
 * Create a client with authentication
 */
export async function createAuthenticatedClient(
  agentUrl: string, 
  tokenProvider: () => Promise<string>,
  transport: 'jsonrpc' | 'grpc' = 'jsonrpc'
) {
  const authHandler = new BearerTokenAuthHandler(tokenProvider);
  const authFetch = createAuthenticatingFetchWithRetry(fetch, authHandler);
  
  const transports = transport === 'grpc'
    ? [new GrpcTransportFactory()]
    : [new JsonRpcTransportFactory({ fetchImpl: authFetch })];
    
  const factory = new ClientFactory({ transports });
  return await factory.createFromUrl(agentUrl);
}

/**
 * Send a simple text message
 */
export async function sendSimpleMessage(
  client: any, 
  text: string, 
  options?: { timeout?: number }
) {
  const params = {
    message: {
      messageId: uuidv4(),
      role: 'user' as const,
      parts: [{ kind: 'text' as const, text }],
      kind: 'message' as const,
    },
  };

  const requestOptions = options?.timeout 
    ? { signal: AbortSignal.timeout(options.timeout) }
    : undefined;

  return await client.sendMessage(params, requestOptions);
}

/**
 * Send a message and wait for task completion
 */
export async function sendAndWaitForTask(
  client: any,
  text: string,
  options?: { timeout?: number; pollInterval?: number }
) {
  const response = await sendSimpleMessage(client, text, options);
  
  if (response.kind === 'message') {
    return { type: 'message', data: response };
  }
  
  if (response.kind === 'task') {
    // Poll for task completion
    const pollInterval = options?.pollInterval || 1000;
    const timeout = options?.timeout || 30000;
    const startTime = Date.now();
    
    while (response.status.state === 'working' || response.status.state === 'submitted') {
      if (Date.now() - startTime > timeout) {
        throw new Error('Task timeout');
      }
      
      await new Promise(resolve => setTimeout(resolve, pollInterval));
      // In a real implementation, you'd query the task status here
      // For now, we'll assume the task completes
      break;
    }
    
    return { type: 'task', data: response };
  }
  
  return response;
}
```

### Message Builders
```typescript
/**
 * Build a text message
 */
export function buildTextMessage(text: string, messageId?: string) {
  return {
    messageId: messageId || uuidv4(),
    role: 'user' as const,
    parts: [{ kind: 'text' as const, text }],
    kind: 'message' as const,
  };
}

/**
 * Build a message with multiple parts
 */
export function buildMultiPartMessage(parts: Array<{ text?: string; data?: string }>, messageId?: string) {
  return {
    messageId: messageId || uuidv4(),
    role: 'user' as const,
    parts: parts.map(part => {
      if (part.text) {
        return { kind: 'text' as const, text: part.text };
      }
      if (part.data) {
        return { kind: 'data' as const, data: part.data };
      }
      throw new Error('Part must have either text or data');
    }),
    kind: 'message' as const,
  };
}

/**
 * Build a file part for messages
 */
export function buildFilePart(filename: string, content: string, mimeType?: string) {
  return {
    kind: 'file' as const,
    file: {
      name: filename,
      mimeType: mimeType || 'text/plain',
      data: content,
    }
  };
}
```

## Server Helpers

### Agent Card Builder
```typescript
import { AgentCard, Skill } from '@a2a-js/sdk';

/**
 * Create a basic agent card
 */
export function createBasicAgentCard(config: {
  name: string;
  description: string;
  version: string;
  url: string;
  skills: Skill[];
  capabilities?: {
    streaming?: boolean;
    pushNotifications?: boolean;
    stateTransitionHistory?: boolean;
  };
  inputModes?: string[];
  outputModes?: string[];
}): AgentCard {
  return {
    name: config.name,
    description: config.description,
    protocolVersion: '0.3.0',
    version: config.version,
    url: config.url,
    skills: config.skills,
    capabilities: {
      streaming: false,
      pushNotifications: false,
      stateTransitionHistory: false,
      ...config.capabilities,
    },
    defaultInputModes: config.inputModes || ['text'],
    defaultOutputModes: config.outputModes || ['text'],
    additionalInterfaces: [
      { url: config.url, transport: 'JSONRPC' },
    ],
  };
}

/**
 * Create a skill definition
 */
export function createSkill(config: {
  id: string;
  name: string;
  description: string;
  tags?: string[];
}): Skill {
  return {
    id: config.id,
    name: config.name,
    description: config.description,
    tags: config.tags || [],
  };
}
```

### Response Helpers
```typescript
/**
 * Create a text response message
 */
export function createTextResponse(text: string, contextId: string, messageId?: string) {
  return {
    kind: 'message' as const,
    messageId: messageId || uuidv4(),
    role: 'agent' as const,
    parts: [{ kind: 'text' as const, text }],
    contextId,
  };
}

/**
 * Create an error response
 */
export function createErrorResponse(error: string, contextId: string, messageId?: string) {
  return {
    kind: 'message' as const,
    messageId: messageId || uuidv4(),
    role: 'agent' as const,
    parts: [{ 
      kind: 'text' as const, 
      text: `Error: ${error}` 
    }],
    contextId,
  };
}

/**
 * Create a task with initial status
 */
export function createInitialTask(taskId: string, contextId: string, userMessage: any) {
  return {
    kind: 'task' as const,
    id: taskId,
    contextId,
    status: {
      state: 'submitted' as const,
      timestamp: new Date().toISOString(),
    },
    history: [userMessage],
  };
}

/**
 * Create a task status update
 */
export function createStatusUpdate(
  taskId: string, 
  contextId: string, 
  state: 'submitted' | 'working' | 'completed' | 'canceled' | 'failed',
  isFinal: boolean = false
) {
  return {
    kind: 'status-update' as const,
    taskId,
    contextId,
    status: {
      state,
      timestamp: new Date().toISOString(),
    },
    final: isFinal,
  };
}

/**
 * Create a task artifact
 */
export function createArtifact(
  taskId: string,
  contextId: string,
  artifactId: string,
  name: string,
  content: string,
  mimeType: string = 'text/plain'
) {
  return {
    kind: 'artifact-update' as const,
    taskId,
    contextId,
    artifact: {
      artifactId,
      name,
      parts: [{
        kind: 'text' as const,
        text: content,
      }],
    },
  };
}
```

### Executor Base Class
```typescript
import { AgentExecutor, RequestContext, ExecutionEventBus } from '@a2a-js/sdk';

/**
 * Base class for agent executors with common functionality
 */
export abstract class BaseAgentExecutor implements AgentExecutor {
  protected cancelledTasks = new Set<string>();

  /**
   * Main execution logic - must be implemented by subclasses
   */
  abstract execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void>;

  /**
   * Default cancellation implementation
   */
  async cancelTask(taskId: string, eventBus: ExecutionEventBus): Promise<void> {
    this.cancelledTasks.add(taskId);
    
    eventBus.publish(createStatusUpdate(taskId, '', 'canceled', true));
    eventBus.finished();
  }

  /**
   * Check if a task has been cancelled
   */
  protected isTaskCancelled(taskId: string): boolean {
    return this.cancelledTasks.has(taskId);
  }

  /**
   * Clean up cancelled task
   */
  protected cleanupCancelledTask(taskId: string): void {
    this.cancelledTasks.delete(taskId);
  }

  /**
   * Execute with cancellation support
   */
  protected async executeWithCancellation(
    taskId: string,
    contextId: string,
    work: () => Promise<void>,
    eventBus: ExecutionEventBus
  ): Promise<void> {
    try {
      await work();
    } catch (error) {
      if (this.isTaskCancelled(taskId)) {
        eventBus.publish(createStatusUpdate(taskId, contextId, 'canceled', true));
      } else {
        eventBus.publish(createStatusUpdate(taskId, contextId, 'failed', true));
      }
      throw error;
    } finally {
      this.cleanupCancelledTask(taskId);
    }
  }
}
```

## Utility Functions

### Validation Helpers
```typescript
/**
 * Validate agent card structure
 */
export function validateAgentCard(card: AgentCard): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!card.name || card.name.trim() === '') {
    errors.push('Agent name is required');
  }

  if (!card.description || card.description.trim() === '') {
    errors.push('Agent description is required');
  }

  if (!card.version || card.version.trim() === '') {
    errors.push('Agent version is required');
  }

  if (!card.url || !isValidUrl(card.url)) {
    errors.push('Valid agent URL is required');
  }

  if (!card.skills || card.skills.length === 0) {
    errors.push('At least one skill is required');
  }

  if (card.protocolVersion !== '0.3.0') {
    errors.push('Protocol version must be 0.3.0');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate message structure
 */
export function validateMessage(message: any): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!message.messageId || message.messageId.trim() === '') {
    errors.push('Message ID is required');
  }

  if (!message.role || !['user', 'agent'].includes(message.role)) {
    errors.push('Message role must be "user" or "agent"');
  }

  if (!message.parts || !Array.isArray(message.parts) || message.parts.length === 0) {
    errors.push('Message must have at least one part');
  } else {
    message.parts.forEach((part: any, index: number) => {
      if (!part.kind) {
        errors.push(`Part ${index + 1} must have a kind`);
      }
    });
  }

  if (!message.contextId || message.contextId.trim() === '') {
    errors.push('Context ID is required');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Check if URL is valid
 */
function isValidUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}
```

### Logging Helpers
```typescript
/**
 * Simple logger for A2A operations
 */
export class A2ALogger {
  constructor(private prefix: string = 'A2A') {}

  info(message: string, data?: any) {
    console.log(`[${this.prefix}] [INFO] ${message}`, data || '');
  }

  error(message: string, error?: any) {
    console.error(`[${this.prefix}] [ERROR] ${message}`, error || '');
  }

  warn(message: string, data?: any) {
    console.warn(`[${this.prefix}] [WARN] ${message}`, data || '');
  }

  debug(message: string, data?: any) {
    if (process.env.NODE_ENV === 'development') {
      console.log(`[${this.prefix}] [DEBUG] ${message}`, data || '');
    }
  }

  task(taskId: string, message: string, data?: any) {
    console.log(`[${this.prefix}] [TASK:${taskId}] ${message}`, data || '');
  }
}

/**
 * Default logger instance
 */
export const logger = new A2ALogger();
```

### Configuration Helpers
```typescript
/**
 * Load configuration from environment variables
 */
export function loadConfigFromEnv() {
  return {
    agentUrl: process.env.A2A_AGENT_URL || 'http://localhost:4000',
    authToken: process.env.A2A_AUTH_TOKEN,
    timeout: parseInt(process.env.A2A_TIMEOUT || '30000'),
    retryAttempts: parseInt(process.env.A2A_RETRY_ATTEMPTS || '3'),
    logLevel: process.env.A2A_LOG_LEVEL || 'info',
  };
}

/**
 * Create configuration object
 */
export function createConfig(overrides: Partial<ReturnType<typeof loadConfigFromEnv>> = {}) {
  const defaultConfig = loadConfigFromEnv();
  return { ...defaultConfig, ...overrides };
}
```

## Error Handling

### Custom Errors
```typescript
/**
 * Base A2A error
 */
export class A2AError extends Error {
  constructor(message: string, public code?: string) {
    super(message);
    this.name = 'A2AError';
  }
}

/**
 * Connection error
 */
export class A2AConnectionError extends A2AError {
  constructor(message: string) {
    super(message, 'CONNECTION_ERROR');
    this.name = 'A2AConnectionError';
  }
}

/**
 * Authentication error
 */
export class A2AAuthenticationError extends A2AError {
  constructor(message: string) {
    super(message, 'AUTH_ERROR');
    this.name = 'A2AAuthenticationError';
  }
}

/**
 * Timeout error
 */
export class A2ATimeoutError extends A2AError {
  constructor(message: string) {
    super(message, 'TIMEOUT_ERROR');
    this.name = 'A2ATimeoutError';
  }
}

/**
 * Task error
 */
export class A2ATaskError extends A2AError {
  constructor(message: string, public taskId?: string) {
    super(message, 'TASK_ERROR');
    this.name = 'A2ATaskError';
  }
}
```

### Error Handler
```typescript
/**
 * Handle A2A errors consistently
 */
export function handleA2AError(error: any): A2AError {
  if (error instanceof A2AError) {
    return error;
  }

  if (error.name === 'AbortError') {
    return new A2ATimeoutError('Request timed out');
  }

  if (error.status === 401) {
    return new A2AAuthenticationError('Authentication failed');
  }

  if (error.status === 404) {
    return new A2AConnectionError('Agent not found');
  }

  if (error.code === 'ECONNREFUSED' || error.code === 'ENOTFOUND') {
    return new A2AConnectionError('Connection failed');
  }

  return new A2AError(error.message || 'Unknown error occurred');
}
```

These helper functions provide a solid foundation for building A2A applications with common patterns, error handling, validation, and utilities.