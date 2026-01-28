# A2A SDK Complete Reference

## Installation and Setup

### Basic Installation
```bash
npm install @a2a-js/sdk
```

### With Express Server Support
```bash
npm install @a2a-js/sdk express
```

### With gRPC Support
```bash
npm install @a2a-js/sdk @grpc/grpc-js @bufbuild/protobuf
```

## Core Concepts

### Agent Card
The Agent Card is the metadata descriptor for your A2A agent:

```typescript
interface AgentCard {
  name: string;
  description: string;
  protocolVersion: string; // "0.3.0"
  version: string;
  url: string;
  skills: Skill[];
  capabilities: {
    streaming?: boolean;
    pushNotifications?: boolean;
    stateTransitionHistory?: boolean;
  };
  defaultInputModes: string[];
  defaultOutputModes: string[];
  additionalInterfaces?: AdditionalInterface[];
}
```

### Message Types
```typescript
// Direct Message
interface Message {
  kind: 'message';
  messageId: string;
  role: 'user' | 'agent';
  parts: Part[];
  contextId: string;
}

// Task for long-running operations
interface Task {
  kind: 'task';
  id: string;
  contextId: string;
  status: TaskStatus;
  artifacts?: TaskArtifact[];
  history: Message[];
}
```

### Transport Protocols
- **JSON-RPC**: Default, simple client-server communication
- **HTTP+JSON/REST**: RESTful API interface
- **gRPC**: High-performance binary protocol

## Server Implementation

### Basic Agent Server
```typescript
import express from 'express';
import { 
  AgentCard, 
  AgentExecutor, 
  RequestContext, 
  ExecutionEventBus,
  Message,
  v4 as uuidv4
} from '@a2a-js/sdk';
import { 
  DefaultRequestHandler, 
  InMemoryTaskStore 
} from '@a2a-js/sdk/server';
import { 
  agentCardHandler, 
  jsonRpcHandler, 
  restHandler 
} from '@a2a-js/sdk/server/express';

// 1. Define Agent Card
const agentCard: AgentCard = {
  name: 'Hello Agent',
  description: 'A simple agent that responds to messages',
  protocolVersion: '0.3.0',
  version: '1.0.0',
  url: 'http://localhost:4000/a2a/jsonrpc',
  skills: [
    { 
      id: 'chat', 
      name: 'Chat', 
      description: 'Simple chat interaction',
      tags: ['chat', 'simple']
    }
  ],
  capabilities: {
    streaming: true,
    pushNotifications: false,
  },
  defaultInputModes: ['text'],
  defaultOutputModes: ['text'],
  additionalInterfaces: [
    { url: 'http://localhost:4000/a2a/jsonrpc', transport: 'JSONRPC' },
    { url: 'http://localhost:4000/a2a/rest', transport: 'HTTP+JSON' },
  ],
};

// 2. Implement Agent Logic
class HelloAgentExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { userMessage, contextId } = requestContext;

    // Create response
    const response: Message = {
      kind: 'message',
      messageId: uuidv4(),
      role: 'agent',
      parts: [{ 
        kind: 'text', 
        text: `Hello! You said: "${userMessage.parts[0].text}"` 
      }],
      contextId,
    };

    // Publish and finish
    eventBus.publish(response);
    eventBus.finished();
  }

  async cancelTask(): Promise<void> {
    // Handle cancellation if needed
  }
}

// 3. Setup Server
const requestHandler = new DefaultRequestHandler(
  agentCard,
  new InMemoryTaskStore(),
  new HelloAgentExecutor()
);

const app = express();

// Agent Card endpoint
app.use('/.well-known/agent-card.json', agentCardHandler({ 
  agentCardProvider: requestHandler 
}));

// JSON-RPC endpoint
app.use('/a2a/jsonrpc', jsonRpcHandler({ 
  requestHandler,
  userBuilder: UserBuilder.noAuthentication 
}));

// REST endpoint
app.use('/a2a/rest', restHandler({ 
  requestHandler,
  userBuilder: UserBuilder.noAuthentication 
}));

app.listen(4000, () => {
  console.log('🚀 A2A Agent server running on http://localhost:4000');
});
```

### Task-Based Agent Server
```typescript
import { 
  Task, 
  TaskStatusUpdateEvent, 
  TaskArtifactUpdateEvent 
} from '@a2a-js/sdk';

class TaskAgentExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { taskId, contextId, userMessage, task } = requestContext;

    // Create initial task if it doesn't exist
    if (!task) {
      const initialTask: Task = {
        kind: 'task',
        id: taskId,
        contextId,
        status: {
          state: 'submitted',
          timestamp: new Date().toISOString(),
        },
        history: [userMessage],
      };
      eventBus.publish(initialTask);
    }

    // Update status to working
    eventBus.publish({
      kind: 'status-update',
      taskId,
      contextId,
      status: { state: 'working', timestamp: new Date().toISOString() },
      final: false,
    });

    // Simulate work
    await new Promise(resolve => setTimeout(resolve, 2000));

    // Create artifact
    eventBus.publish({
      kind: 'artifact-update',
      taskId,
      contextId,
      artifact: {
        artifactId: 'result-' + Date.now(),
        name: 'analysis_result.txt',
        parts: [{
          kind: 'text',
          text: `Analysis complete for task ${taskId}. Processed: ${userMessage.parts[0].text}`
        }],
      },
    });

    // Mark as completed
    eventBus.publish({
      kind: 'status-update',
      taskId,
      contextId,
      status: { state: 'completed', timestamp: new Date().toISOString() },
      final: true,
    });

    eventBus.finished();
  }

  async cancelTask(taskId: string, eventBus: ExecutionEventBus): Promise<void> {
    eventBus.publish({
      kind: 'status-update',
      taskId,
      contextId: '', // Will be set by framework
      status: { state: 'canceled', timestamp: new Date().toISOString() },
      final: true,
    });
    eventBus.finished();
  }
}
```

## Client Implementation

### Basic Client
```typescript
import { ClientFactory } from '@a2a-js/sdk/client';
import { MessageSendParams, v4 as uuidv4 } from '@a2a-js/sdk';

async function basicClientExample() {
  const factory = new ClientFactory();
  
  // Connect to agent
  const client = await factory.createFromUrl('http://localhost:4000');

  // Send message
  const sendParams: MessageSendParams = {
    message: {
      messageId: uuidv4(),
      role: 'user',
      parts: [{ kind: 'text', text: 'Hello, agent!' }],
      kind: 'message',
    },
  };

  try {
    const response = await client.sendMessage(sendParams);
    
    if (response.kind === 'message') {
      console.log('Agent response:', response.parts[0].text);
    } else if (response.kind === 'task') {
      console.log('Task created:', response.id);
      console.log('Status:', response.status.state);
    }
  } catch (error) {
    console.error('Error:', error);
  }
}
```

### Streaming Client
```typescript
async function streamingClientExample() {
  const factory = new ClientFactory();
  const client = await factory.createFromUrl('http://localhost:4000');

  const sendParams: MessageSendParams = {
    message: {
      messageId: uuidv4(),
      role: 'user',
      parts: [{ kind: 'text', text: 'Start a long task' }],
      kind: 'message',
    },
  };

  try {
    const stream = client.sendMessageStream(sendParams);

    for await (const event of stream) {
      switch (event.kind) {
        case 'task':
          console.log(`[Task] Created: ${event.id} - Status: ${event.status.state}`);
          break;
        case 'status-update':
          console.log(`[Status] Task ${event.taskId}: ${event.status.state}`);
          break;
        case 'artifact-update':
          console.log(`[Artifact] Task ${event.taskId}: ${event.artifact.name}`);
          break;
      }
    }
    console.log('Stream completed');
  } catch (error) {
    console.error('Stream error:', error);
  }
}
```

### gRPC Client
```typescript
import { ClientFactory, ClientFactoryOptions } from '@a2a-js/sdk/client';
import { GrpcTransportFactory } from '@a2a-js/sdk/client/grpc';

async function grpcClientExample() {
  const factory = new ClientFactory({
    transports: [new GrpcTransportFactory()]
  });

  const client = await factory.createFromUrl('http://localhost:4000');

  const response = await client.sendMessage({
    message: {
      messageId: uuidv4(),
      role: 'user',
      parts: [{ kind: 'text', text: 'gRPC message' }],
      kind: 'message',
    },
  });

  console.log('gRPC response:', response);
}
```

## Advanced Features

### Authentication
```typescript
import { 
  AuthenticationHandler,
  createAuthenticatingFetchWithRetry,
  JsonRpcTransportFactory 
} from '@a2a-js/sdk/client';

// Custom authentication handler
class BearerTokenAuthHandler implements AuthenticationHandler {
  constructor(private tokenProvider: () => Promise<string>) {}

  async headers(): Promise<Record<string, string>> {
    const token = await this.tokenProvider();
    return { Authorization: `Bearer ${token}` };
  }

  async shouldRetryWithHeaders(): Promise<Record<string, string> | undefined> {
    // Refresh token on 401 and retry
    const newToken = await this.tokenProvider();
    return { Authorization: `Bearer ${newToken}` };
  }
}

// Setup authenticated client
async function authenticatedClient() {
  const tokenProvider = async () => {
    // Your token refresh logic here
    return 'your-bearer-token';
  };

  const authHandler = new BearerTokenAuthHandler(tokenProvider);
  const authFetch = createAuthenticatingFetchWithRetry(fetch, authHandler);

  const factory = new ClientFactory({
    transports: [new JsonRpcTransportFactory({ fetchImpl: authFetch })]
  });

  const client = await factory.createFromUrl('https://secure-agent.com');
  return client;
}
```

### Request Interceptors
```typescript
import { CallInterceptor, BeforeArgs, AfterArgs } from '@a2a-js/sdk/client';

class LoggingInterceptor implements CallInterceptor {
  async before(args: BeforeArgs): Promise<void> {
    console.log(`[Request] ${args.method}:`, args.params);
  }

  async after(args: AfterArgs): Promise<void> {
    console.log(`[Response] Status: ${args.response?.status || 'unknown'}`);
  }
}

class RequestIdInterceptor implements CallInterceptor {
  async before(args: BeforeArgs): Promise<void> {
    args.options = {
      ...args.options,
      serviceParameters: {
        ...args.options.serviceParameters,
        'X-Request-ID': uuidv4(),
      },
    };
  }

  async after(): Promise<void> {}
}

// Use interceptors
const factory = new ClientFactory({
  clientConfig: {
    interceptors: [new LoggingInterceptor(), new RequestIdInterceptor()]
  }
});
```

### Push Notifications
```typescript
import { PushNotificationConfig } from '@a2a-js/sdk';

// Server-side: Enable push notifications in agent card
const agentCard: AgentCard = {
  // ... other properties
  capabilities: {
    streaming: true,
    pushNotifications: true, // Enable push notifications
  },
};

// Client-side: Configure push notifications
const pushConfig: PushNotificationConfig = {
  id: 'my-webhook',
  url: 'https://my-app.com/webhook/a2a-updates',
  token: 'webhook-auth-token',
};

const sendParams: MessageSendParams = {
  message: {
    messageId: uuidv4(),
    role: 'user',
    parts: [{ kind: 'text', text: 'Long running task' }],
    kind: 'message',
  },
  configuration: {
    blocking: true,
    pushNotificationConfig: pushConfig,
  },
};
```

### Timeout Configuration
```typescript
// Set timeout for individual requests
await client.sendMessage(sendParams, {
  signal: AbortSignal.timeout(10000), // 10 seconds
});

// Custom timeout logic
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 5000);

try {
  await client.sendMessage(sendParams, { signal: controller.signal });
} finally {
  clearTimeout(timeoutId);
}
```

## Error Handling

### Common Error Patterns
```typescript
async function robustClientExample() {
  const factory = new ClientFactory();
  const client = await factory.createFromUrl('http://localhost:4000');

  try {
    const response = await client.sendMessage({
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ kind: 'text', text: 'Test message' }],
        kind: 'message',
      },
      options: {
        signal: AbortSignal.timeout(5000), // 5 second timeout
      },
    });

    // Handle response types
    if (response.kind === 'message') {
      console.log('Direct message:', response.parts[0].text);
    } else if (response.kind === 'task') {
      console.log('Task:', response.id, 'Status:', response.status.state);
      
      // Handle artifacts
      if (response.artifacts) {
        response.artifacts.forEach(artifact => {
          console.log(`Artifact: ${artifact.name}`);
          artifact.parts.forEach(part => {
            if (part.kind === 'text') {
              console.log('Content:', part.text);
            }
          });
        });
      }
    }
  } catch (error) {
    if (error.name === 'AbortError') {
      console.error('Request timed out');
    } else if (error.status === 401) {
      console.error('Authentication failed');
    } else if (error.status === 404) {
      console.error('Agent not found');
    } else {
      console.error('Unexpected error:', error);
    }
  }
}
```

## Testing

### Mock Agent for Testing
```typescript
// test-mock-agent.ts
import { AgentExecutor, RequestContext, ExecutionEventBus } from '@a2a-js/sdk';

class MockTestExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { userMessage, contextId } = requestContext;
    
    // Simulate different behaviors based on input
    const input = userMessage.parts[0].text;
    
    if (input.includes('error')) {
      throw new Error('Test error');
    }
    
    if (input.includes('task')) {
      // Return a task
      eventBus.publish({
        kind: 'task',
        id: uuidv4(),
        contextId,
        status: { state: 'completed', timestamp: new Date().toISOString() },
        history: [userMessage],
      });
    } else {
      // Return a direct message
      eventBus.publish({
        kind: 'message',
        messageId: uuidv4(),
        role: 'agent',
        parts: [{ kind: 'text', text: `Mock response to: ${input}` }],
        contextId,
      });
    }
    
    eventBus.finished();
  }

  async cancelTask(): Promise<void> {}
}
```

### Client Tests
```typescript
// client.test.ts
import { ClientFactory } from '@a2a-js/sdk/client';

describe('A2A Client', () => {
  let client: A2AClient;
  let mockServer: any;

  beforeAll(async () => {
    // Setup mock server
    mockServer = await setupMockAgent();
    
    const factory = new ClientFactory();
    client = await factory.createFromUrl(mockServer.url);
  });

  it('should send and receive messages', async () => {
    const response = await client.sendMessage({
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ kind: 'text', text: 'Hello test' }],
        kind: 'message',
      },
    });

    expect(response.kind).toBe('message');
    expect(response.parts[0].text).toContain('Mock response');
  });

  it('should handle task responses', async () => {
    const response = await client.sendMessage({
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ kind: 'text', text: 'Create task' }],
        kind: 'message',
      },
    });

    expect(response.kind).toBe('task');
    expect(response.status.state).toBe('completed');
  });

  it('should handle errors gracefully', async () => {
    await expect(client.sendMessage({
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ kind: 'text', text: 'trigger error' }],
        kind: 'message',
      },
    })).rejects.toThrow();
  });
});
```

## Best Practices

### Server Best Practices
1. **Always implement cancelTask** for long-running operations
2. **Use proper error handling** and publish error states
3. **Implement timeouts** for external service calls
4. **Log important events** for debugging
5. **Validate input messages** before processing

### Client Best Practices
1. **Set appropriate timeouts** for requests
2. **Implement retry logic** with exponential backoff
3. **Handle different response types** (message vs task)
4. **Use streaming for long-running operations**
5. **Implement proper authentication** for production use

### Performance Optimization
1. **Use gRPC** for high-performance scenarios
2. **Implement connection pooling** for multiple clients
3. **Cache agent cards** to reduce discovery calls
4. **Use streaming** instead of polling for task updates
5. **Optimize artifact sizes** and use compression when needed

This comprehensive reference covers all major aspects of the A2A JavaScript SDK, from basic setup to advanced features and best practices.