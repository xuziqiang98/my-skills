# A2A SDK Skill

The A2A SDK skill provides comprehensive tools and guidance for working with the A2A (Agent-to-Agent) JavaScript SDK. This skill helps you build, configure, and deploy A2A-compliant agents and clients.

## Overview

The A2A JavaScript SDK implements the Agent2Agent Protocol Specification v0.3.0, enabling:
- Building A2A-compliant agent servers
- Creating clients to interact with any A2A agent
- Support for multiple transport protocols (JSON-RPC, HTTP+JSON/REST, gRPC)
- Real-time streaming capabilities
- Task management and cancellation
- Push notifications for long-running tasks

## Key Features

### Transport Support
- **JSON-RPC**: Full client and server support
- **HTTP+JSON/REST**: RESTful API interface
- **gRPC**: High-performance binary protocol (Node.js only)

### Core Capabilities
- **Message Exchange**: Direct agent communication
- **Task Management**: Stateful, long-running operations
- **Streaming**: Real-time updates via Server-Sent Events
- **Authentication**: Bearer token and custom auth handlers
- **Push Notifications**: Async updates for long-running tasks

## Quick Start Examples

### Basic Agent Server
```typescript
import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import { AgentCard, AgentExecutor, RequestContext, ExecutionEventBus } from '@a2a-js/sdk';
import { DefaultRequestHandler, InMemoryTaskStore } from '@a2a-js/sdk/server';
import { agentCardHandler, jsonRpcHandler, restHandler, UserBuilder } from '@a2a-js/sdk/server/express';

const agentCard: AgentCard = {
  name: 'My Agent',
  description: 'A simple A2A agent',
  protocolVersion: '0.3.0',
  version: '1.0.0',
  url: 'http://localhost:4000/a2a/jsonrpc',
  skills: [{ id: 'chat', name: 'Chat', description: 'Chat with the agent' }],
  capabilities: { streaming: true },
  defaultInputModes: ['text'],
  defaultOutputModes: ['text'],
  additionalInterfaces: [
    { url: 'http://localhost:4000/a2a/jsonrpc', transport: 'JSONRPC' },
    { url: 'http://localhost:4000/a2a/rest', transport: 'HTTP+JSON' },
  ],
};

class MyExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const response = {
      kind: 'message' as const,
      messageId: uuidv4(),
      role: 'agent' as const,
      parts: [{ kind: 'text' as const, text: 'Hello from your A2A agent!' }],
      contextId: requestContext.contextId,
    };
    eventBus.publish(response);
    eventBus.finished();
  }
  cancelTask = async (): Promise<void> => {};
}

const requestHandler = new DefaultRequestHandler(
  agentCard,
  new InMemoryTaskStore(),
  new MyExecutor()
);

const app = express();
app.use('/.well-known/agent-card.json', agentCardHandler({ agentCardProvider: requestHandler }));
app.use('/a2a/jsonrpc', jsonRpcHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));
app.use('/a2a/rest', restHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));
app.listen(4000);
```

### Client Implementation
```typescript
import { ClientFactory } from '@a2a-js/sdk/client';
import { v4 as uuidv4 } from '@a2a-js/sdk';

const factory = new ClientFactory();
const client = await factory.createFromUrl('http://localhost:4000');

const response = await client.sendMessage({
  message: {
    messageId: uuidv4(),
    role: 'user',
    parts: [{ kind: 'text', text: 'Hello agent!' }],
    kind: 'message',
  },
});
```

## Bundled Resources

- `REFERENCE.md`: Full API reference and advanced patterns
- `HELPERS.md`: Utility helpers and common recipes
- `templates/server/basic-server.ts`: Minimal JSON-RPC/REST agent
- `templates/server/task-server.ts`: Task-based agent with status updates and artifacts
- `templates/client/basic-client.ts`: Simple client wrapper
- `templates/client/streaming-client.ts`: Streaming client for real-time updates
- `examples/authentication.md`: Authentication patterns
- `examples/streaming.md`: Streaming examples

## Available Commands

Use this skill when you need to:
- Set up A2A agent servers
- Create A2A clients
- Implement streaming communication
- Handle authentication in A2A
- Configure push notifications
- Debug A2A implementations
- Generate A2A-compliant code

## Installation Requirements

```bash
npm install @a2a-js/sdk
# For Express server support
npm install express uuid
# For gRPC support
npm install @grpc/grpc-js @bufbuild/protobuf
```

## Transport Options

Choose the appropriate transport based on your needs:
- **JSON-RPC**: Best for simple client-server communication
- **HTTP+JSON/REST**: Ideal for web applications and RESTful APIs
- **gRPC**: Optimal for high-performance, low-latency scenarios

This skill provides templates and examples for all supported transports and use cases.
