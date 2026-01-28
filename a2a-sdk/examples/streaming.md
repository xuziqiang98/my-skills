# A2A Streaming Examples

These examples show how to implement streaming updates with A2A tasks using Server-Sent Events (SSE).

## Streaming Server Example

```typescript
import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import {
  AgentCard,
  AgentExecutor,
  RequestContext,
  ExecutionEventBus,
  Task,
} from '@a2a-js/sdk';
import { DefaultRequestHandler, InMemoryTaskStore } from '@a2a-js/sdk/server';
import { agentCardHandler, jsonRpcHandler, restHandler, UserBuilder } from '@a2a-js/sdk/server/express';

const agentCard: AgentCard = {
  name: 'Streaming A2A Agent',
  description: 'An A2A agent that streams task updates',
  protocolVersion: '0.3.0',
  version: '1.0.0',
  url: 'http://localhost:4000/a2a/jsonrpc',
  skills: [{ id: 'stream', name: 'Streaming', description: 'Stream task updates' }],
  capabilities: { streaming: true },
  defaultInputModes: ['text'],
  defaultOutputModes: ['text'],
  additionalInterfaces: [
    { url: 'http://localhost:4000/a2a/jsonrpc', transport: 'JSONRPC' },
    { url: 'http://localhost:4000/a2a/rest', transport: 'HTTP+JSON' },
  ],
};

class StreamingExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { taskId, contextId, userMessage, task } = requestContext;

    if (!task) {
      const initialTask: Task = {
        kind: 'task',
        id: taskId,
        contextId,
        status: { state: 'submitted', timestamp: new Date().toISOString() },
        history: [userMessage],
      };
      eventBus.publish(initialTask);
    }

    eventBus.publish({
      kind: 'status-update',
      taskId,
      contextId,
      status: { state: 'working', timestamp: new Date().toISOString(), message: 'Step 1: preparing' },
      final: false,
    });

    await new Promise((resolve) => setTimeout(resolve, 1000));

    eventBus.publish({
      kind: 'artifact-update',
      taskId,
      contextId,
      artifact: {
        artifactId: `artifact-${uuidv4()}`,
        name: 'step-1.txt',
        parts: [{ kind: 'text', text: 'First step completed.' }],
      },
    });

    eventBus.publish({
      kind: 'status-update',
      taskId,
      contextId,
      status: { state: 'working', timestamp: new Date().toISOString(), message: 'Step 2: processing' },
      final: false,
    });

    await new Promise((resolve) => setTimeout(resolve, 1000));

    eventBus.publish({
      kind: 'artifact-update',
      taskId,
      contextId,
      artifact: {
        artifactId: `artifact-${uuidv4()}`,
        name: 'step-2.txt',
        parts: [{ kind: 'text', text: 'Second step completed.' }],
      },
    });

    eventBus.publish({
      kind: 'status-update',
      taskId,
      contextId,
      status: { state: 'completed', timestamp: new Date().toISOString() },
      final: true,
    });

    eventBus.finished();
  }

  async cancelTask(): Promise<void> {}
}

const requestHandler = new DefaultRequestHandler(
  agentCard,
  new InMemoryTaskStore(),
  new StreamingExecutor()
);

const app = express();
app.use('/.well-known/agent-card.json', agentCardHandler({ agentCardProvider: requestHandler }));
app.use('/a2a/jsonrpc', jsonRpcHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));
app.use('/a2a/rest', restHandler({ requestHandler, userBuilder: UserBuilder.noAuthentication }));

app.listen(4000, () => {
  console.log('Streaming server running on http://localhost:4000');
});
```

## Streaming Client Example

```typescript
import { ClientFactory } from '@a2a-js/sdk/client';
import { MessageSendParams, v4 as uuidv4 } from '@a2a-js/sdk';

async function streamTask() {
  const factory = new ClientFactory();
  const client = await factory.createFromUrl('http://localhost:4000');

  const sendParams: MessageSendParams = {
    message: {
      messageId: uuidv4(),
      role: 'user',
      parts: [{ kind: 'text', text: 'Stream task updates' }],
      kind: 'message',
    },
  };

  const stream = client.sendMessageStream(sendParams);

  for await (const event of stream) {
    if (event.kind === 'task') {
      console.log(`Task created: ${event.id}`);
    } else if (event.kind === 'status-update') {
      console.log(`Status: ${event.status.state} (${event.status.message || ''})`);
    } else if (event.kind === 'artifact-update') {
      console.log(`Artifact: ${event.artifact.name}`);
    } else if (event.kind === 'message') {
      const text = event.parts.find((part: any) => part.kind === 'text')?.text;
      if (text) {
        console.log(`Message: ${text}`);
      }
    }
  }
}

streamTask().catch((error) => {
  console.error('Streaming error:', error);
});
```

## Usage

1. Start the streaming server example.
2. Run the streaming client example.
3. Observe task, status, and artifact events in real time.
