# Streaming A2A Client

```typescript
// streaming-client.ts
import { ClientFactory } from '@a2a-js/sdk/client';
import { MessageSendParams, v4 as uuidv4 } from '@a2a-js/sdk';

/**
 * Streaming A2A client for real-time task updates
 */
class StreamingA2AClient {
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
   * Send a message and stream the response
   */
  async sendMessageStream(text: string, options?: { timeout?: number }): Promise<void> {
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
      console.log(`📤 Sending message: "${text}"`);
      const stream = this.client.sendMessageStream(sendParams, requestOptions);

      console.log('🔄 Starting to stream responses...');

      for await (const event of stream) {
        this.handleStreamEvent(event);
      }

      console.log('✅ Stream completed');

    } catch (error) {
      console.error('❌ Error in streaming:', error);
      throw error;
    }
  }

  /**
   * Handle different stream events
   */
  private handleStreamEvent(event: any): void {
    const timestamp = new Date().toISOString();

    switch (event.kind) {
      case 'task':
        console.log(`[${timestamp}] 📋 Task Created: ${event.id}`);
        console.log(`   Status: ${event.status.state}`);
        console.log(`   Context: ${event.contextId}`);
        break;

      case 'status-update':
        console.log(`[${timestamp}] 📊 Status Update: ${event.taskId}`);
        console.log(`   New Status: ${event.status.state}`);
        if (event.status.message) {
          console.log(`   Message: ${event.status.message}`);
        }
        if (event.final) {
          console.log(`   ✅ Final status received`);
        }
        break;

      case 'artifact-update':
        console.log(`[${timestamp}] 📎 Artifact Update: ${event.taskId}`);
        console.log(`   Artifact ID: ${event.artifact.artifactId}`);
        console.log(`   Name: ${event.artifact.name}`);
        
        // Show artifact content preview
        const textPart = event.artifact.parts.find((part: any) => part.kind === 'text');
        if (textPart) {
          const preview = textPart.text.length > 100 
            ? textPart.text.substring(0, 100) + '...' 
            : textPart.text;
          console.log(`   Content Preview: ${preview}`);
        }
        break;

      case 'message':
        console.log(`[${timestamp}] 💬 Direct Message:`);
        console.log(`   Message ID: ${event.messageId}`);
        console.log(`   Role: ${event.role}`);
        
        const messageText = event.parts.find((part: any) => part.kind === 'text')?.text;
        if (messageText) {
          console.log(`   Content: ${messageText}`);
        }
        break;

      default:
        console.log(`[${timestamp}] ❓ Unknown event type: ${event.kind}`);
        console.log(`   Event:`, event);
    }
  }

  /**
   * Send a message and collect all events
   */
  async collectStreamEvents(text: string, options?: { timeout?: number }): Promise<any[]> {
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

    const events: any[] = [];

    try {
      console.log(`📤 Sending message: "${text}"`);
      const stream = this.client.sendMessageStream(sendParams, requestOptions);

      for await (const event of stream) {
        events.push({
          ...event,
          timestamp: new Date().toISOString(),
        });
      }

      console.log(`✅ Collected ${events.length} events`);
      return events;

    } catch (error) {
      console.error('❌ Error collecting events:', error);
      throw error;
    }
  }

  /**
   * Send a message and wait for task completion
   */
  async waitForTaskCompletion(text: string, options?: { timeout?: number; pollInterval?: number }): Promise<any> {
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
      console.log(`📤 Sending message: "${text}"`);
      const stream = this.client.sendMessageStream(sendParams, requestOptions);

      let finalTask: any = null;
      let artifacts: any[] = [];

      for await (const event of stream) {
        this.handleStreamEvent(event);

        if (event.kind === 'task') {
          finalTask = event;
        } else if (event.kind === 'artifact-update') {
          artifacts.push(event.artifact);
        } else if (event.kind === 'status-update' && event.final) {
          console.log('✅ Task completed!');
          break;
        }
      }

      return {
        task: finalTask,
        artifacts,
        completed: true,
      };

    } catch (error) {
      console.error('❌ Error waiting for completion:', error);
      throw error;
    }
  }
}

/**
 * Example usage functions
 */
async function streamingClientExample() {
  const client = new StreamingA2AClient('http://localhost:4000');

  try {
    await client.initialize();

    // Example 1: Basic streaming
    console.log('=== Example 1: Basic Streaming ===');
    await client.sendMessageStream('Process this data with streaming updates');

    // Example 2: Collect events
    console.log('\n=== Example 2: Collect Events ===');
    const events = await client.collectStreamEvents('Analyze this text and collect all events');
    console.log(`Total events collected: ${events.length}`);
    events.forEach((event, index) => {
      console.log(`Event ${index + 1}: ${event.kind} at ${event.timestamp}`);
    });

    // Example 3: Wait for completion
    console.log('\n=== Example 3: Wait for Task Completion ===');
    const result = await client.waitForTaskCompletion('Create a comprehensive report');
    console.log('Final result:', result);

  } catch (error) {
    console.error('❌ Streaming client error:', error);
  }
}

/**
 * Advanced streaming example with custom event handling
 */
async function advancedStreamingExample() {
  const client = new StreamingA2AClient('http://localhost:4000');

  try {
    await client.initialize();

    console.log('=== Advanced Streaming with Custom Handling ===');
    
    const sendParams: MessageSendParams = {
      message: {
        messageId: uuidv4(),
        role: 'user',
        parts: [{ 
          kind: 'text', 
          text: 'Perform complex analysis with multiple steps' 
        }],
        kind: 'message',
      },
    };

    const stream = client.client.sendMessageStream(sendParams);
    
    let stepCount = 0;
    let artifactCount = 0;

    for await (const event of stream) {
      switch (event.kind) {
        case 'status-update':
          if (!event.final) {
            stepCount++;
            console.log(`🔄 Step ${stepCount}: ${event.status.message || 'Processing...'}`);
          } else {
            console.log(`✅ Completed after ${stepCount} steps`);
          }
          break;

        case 'artifact-update':
          artifactCount++;
          console.log(`📎 Artifact ${artifactCount}: ${event.artifact.name}`);
          break;

        case 'task':
          console.log(`📋 Task started: ${event.id}`);
          break;
      }
    }

    console.log(`📊 Summary: ${stepCount} steps, ${artifactCount} artifacts created`);

  } catch (error) {
    console.error('❌ Advanced streaming error:', error);
  }
}

// Run examples if this file is executed directly
if (require.main === module) {
  streamingClientExample();
}

export { 
  StreamingA2AClient, 
  streamingClientExample, 
  advancedStreamingExample 
};
```

## Usage

1. **Install dependencies:**
```bash
npm install @a2a-js/sdk uuid
```

2. **Run the streaming client:**
```bash
npx ts-node streaming-client.ts
```

3. **Use in your own code:**
```typescript
import { StreamingA2AClient } from './streaming-client';

const client = new StreamingA2AClient('http://localhost:4000');
await client.initialize();

// Stream responses in real-time
await client.sendMessageStream('Start a long-running task');

// Or wait for completion
const result = await client.waitForTaskCompletion('Process this data');
console.log('Final result:', result);
```

## Features

- **Real-time Streaming**: Live updates as tasks progress
- **Event Collection**: Gather all stream events for analysis
- **Task Completion**: Wait for tasks to finish and get final results
- **Custom Event Handling**: Process different event types appropriately
- **Error Handling**: Robust error handling for streaming operations
- **Timeout Support**: Configurable timeouts for long-running operations

## Stream Event Types

1. **task**: Initial task creation
2. **status-update**: Progress updates and state changes
3. **artifact-update**: File/data artifacts created during processing
4. **message**: Direct messages from the agent

## Best Practices

- Use streaming for long-running operations
- Handle different event types appropriately
- Implement proper error handling
- Set reasonable timeouts
- Collect events for debugging and analysis