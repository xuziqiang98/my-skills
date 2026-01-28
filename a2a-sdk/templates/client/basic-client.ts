# Basic A2A Client

```typescript
// basic-client.ts
import { ClientFactory } from '@a2a-js/sdk/client';
import { MessageSendParams, v4 as uuidv4 } from '@a2a-js/sdk';

/**
 * Basic A2A client implementation
 */
class BasicA2AClient {
  private client: any;
  private agentUrl: string;

  constructor(agentUrl: string) {
    this.agentUrl = agentUrl;
  }

  /**
   * Initialize the client connection
   */
  async initialize(): Promise<void> {
    const factory = new ClientFactory();
    this.client = await factory.createFromUrl(this.agentUrl);
    console.log(`✅ Connected to A2A agent at ${this.agentUrl}`);
  }

  /**
   * Send a simple text message
   */
  async sendMessage(text: string, options?: { timeout?: number }): Promise<any> {
    if (!this.client) {
      throw new Error('Client not initialized. Call initialize() first.');
    }

    const sendParams: MessageSendParams = {
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ kind: 'text', text }],
        kind: 'message',
      },
    };

    const requestOptions = options?.timeout 
      ? { signal: AbortSignal.timeout(options.timeout) }
      : undefined;

    try {
      const response = await this.client.sendMessage(sendParams, requestOptions);
      return this.handleResponse(response);
    } catch (error) {
      console.error('❌ Error sending message:', error);
      throw error;
    }
  }

  /**
   * Handle different response types
   */
  private handleResponse(response: any): any {
    if (response.kind === 'message') {
      return {
        type: 'message',
        content: response.parts[0].text,
        messageId: response.messageId,
        role: response.role,
      };
    } else if (response.kind === 'task') {
      return {
        type: 'task',
        taskId: response.id,
        status: response.status.state,
        artifacts: response.artifacts || [],
        history: response.history || [],
      };
    }
    return response;
  }

  /**
   * Get agent information
   */
  async getAgentInfo(): Promise<any> {
    if (!this.client) {
      throw new Error('Client not initialized. Call initialize() first.');
    }

    try {
      // This would typically get the agent card
      const agentCard = await this.client.getAgentCard();
      return agentCard;
    } catch (error) {
      console.error('❌ Error getting agent info:', error);
      throw error;
    }
  }
}

/**
 * Example usage
 */
async function basicClientExample() {
  const client = new BasicA2AClient('http://localhost:4000');

  try {
    // Initialize connection
    await client.initialize();

    // Get agent information
    console.log('📋 Getting agent information...');
    const agentInfo = await client.getAgentInfo();
    console.log('Agent Info:', agentInfo);

    // Send a simple message
    console.log('💬 Sending message...');
    const response1 = await client.sendMessage('Hello, A2A agent!');
    console.log('Response 1:', response1);

    // Send another message
    console.log('💬 Sending another message...');
    const response2 = await client.sendMessage('How are you doing today?');
    console.log('Response 2:', response2);

    // Send message with timeout
    console.log('💬 Sending message with timeout...');
    const response3 = await client.sendMessage('Quick response needed', { timeout: 5000 });
    console.log('Response 3:', response3);

  } catch (error) {
    console.error('❌ Client error:', error);
  }
}

// Run the example if this file is executed directly
if (require.main === module) {
  basicClientExample();
}

export { BasicA2AClient, basicClientExample };
```

## Usage

1. **Install dependencies:**
```bash
npm install @a2a-js/sdk uuid
```

2. **Run the client:**
```bash
npx ts-node basic-client.ts
```

3. **Use in your own code:**
```typescript
import { BasicA2AClient } from './basic-client';

const client = new BasicA2AClient('http://localhost:4000');
await client.initialize();
const response = await client.sendMessage('Hello!');
console.log(response);
```

## Features

- **Simple API**: Easy-to-use client for basic A2A operations
- **Error Handling**: Comprehensive error handling and logging
- **Timeout Support**: Configurable timeouts for requests
- **Response Parsing**: Automatic handling of different response types
- **Agent Discovery**: Built-in agent information retrieval

## Response Types

The client handles two main response types:

1. **Message Response**: Direct text responses from the agent
2. **Task Response**: Task objects with status, artifacts, and history

## Error Handling

The client provides detailed error information for:
- Connection failures
- Timeout errors
- Invalid responses
- Agent-side errors