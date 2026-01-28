# Basic A2A Agent Server

```typescript
// basic-server.ts
import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import { 
  AgentCard, 
  AgentExecutor, 
  RequestContext, 
  ExecutionEventBus,
  Message
} from '@a2a-js/sdk';
import { 
  DefaultRequestHandler, 
  InMemoryTaskStore 
} from '@a2a-js/sdk/server';
import { 
  agentCardHandler, 
  jsonRpcHandler, 
  restHandler,
  UserBuilder 
} from '@a2a-js/sdk/server/express';

// 1. Define your agent's identity card
const agentCard: AgentCard = {
  name: 'Basic A2A Agent',
  description: 'A simple A2A-compliant agent that responds to messages',
  protocolVersion: '0.3.0',
  version: '1.0.0',
  url: 'http://localhost:4000/a2a/jsonrpc',
  skills: [
    { 
      id: 'chat', 
      name: 'Chat', 
      description: 'Simple conversation with the agent',
      tags: ['chat', 'basic']
    }
  ],
  capabilities: {
    streaming: false,
    pushNotifications: false,
  },
  defaultInputModes: ['text'],
  defaultOutputModes: ['text'],
  additionalInterfaces: [
    { url: 'http://localhost:4000/a2a/jsonrpc', transport: 'JSONRPC' },
    { url: 'http://localhost:4000/a2a/rest', transport: 'HTTP+JSON' },
  ],
};

// 2. Implement the agent's logic
class BasicAgentExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { userMessage, contextId } = requestContext;

    // Extract the text from the user message
    const userText = userMessage.parts.find(part => part.kind === 'text')?.text || '';
    
    // Create a response message
    const response: Message = {
      kind: 'message',
      messageId: uuidv4(),
      role: 'agent',
      parts: [{ 
        kind: 'text', 
        text: `Hello! You said: "${userText}"` 
      }],
      contextId,
    };

    // Publish the response and finish
    eventBus.publish(response);
    eventBus.finished();
  }

  // For simple agents, cancellation is not needed
  async cancelTask(): Promise<void> {
    // No cleanup needed for stateless operations
  }
}

// 3. Set up and run the server
const agentExecutor = new BasicAgentExecutor();
const requestHandler = new DefaultRequestHandler(
  agentCard,
  new InMemoryTaskStore(),
  agentExecutor
);

const app = express();

// Agent Card endpoint (for discovery)
app.use(`/.well-known/agent-card.json`, agentCardHandler({ 
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

// Start the server
const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`🚀 Basic A2A Agent server running on http://localhost:${PORT}`);
  console.log(`📋 Agent Card: http://localhost:${PORT}/.well-known/agent-card.json`);
  console.log(`🔌 JSON-RPC: http://localhost:${PORT}/a2a/jsonrpc`);
  console.log(`🌐 REST API: http://localhost:${PORT}/a2a/rest`);
});
```

## Usage

1. **Install dependencies:**
```bash
npm install @a2a-js/sdk express uuid
```

2. **Run the server:**
```bash
npx ts-node basic-server.ts
```

3. **Test the agent:**
```bash
# Get agent card
curl http://localhost:4000/.well-known/agent-card.json

# Send message via REST
curl -X POST http://localhost:4000/a2a/rest/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "messageId": "test-123",
      "role": "user",
      "parts": [{"kind": "text", "text": "Hello, agent!"}],
      "kind": "message"
    }
  }'
```

## Next Steps

- Add authentication
- Implement task-based operations
- Add streaming support
- Integrate with external services
- Add error handling and validation