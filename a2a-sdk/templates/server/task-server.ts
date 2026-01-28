# Task-Based A2A Agent Server

```typescript
// task-server.ts
import express from 'express';
import { v4 as uuidv4 } from 'uuid';
import { 
  AgentCard, 
  AgentExecutor, 
  RequestContext, 
  ExecutionEventBus,
  Message,
  Task,
  TaskStatusUpdateEvent,
  TaskArtifactUpdateEvent
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

// 1. Define agent card for task-based operations
const agentCard: AgentCard = {
  name: 'Task A2A Agent',
  description: 'An A2A agent that handles long-running tasks and provides artifacts',
  protocolVersion: '0.3.0',
  version: '1.0.0',
  url: 'http://localhost:4000/a2a/jsonrpc',
  skills: [
    { 
      id: 'process', 
      name: 'Data Processing', 
      description: 'Process data and generate reports',
      tags: ['processing', 'tasks', 'artifacts']
    },
    {
      id: 'analyze',
      name: 'Analysis',
      description: 'Analyze content and provide insights',
      tags: ['analysis', 'reports']
    }
  ],
  capabilities: {
    streaming: true,
    pushNotifications: false,
    stateTransitionHistory: true,
  },
  defaultInputModes: ['text'],
  defaultOutputModes: ['text'],
  additionalInterfaces: [
    { url: 'http://localhost:4000/a2a/jsonrpc', transport: 'JSONRPC' },
    { url: 'http://localhost:4000/a2a/rest', transport: 'HTTP+JSON' },
  ],
};

// 2. Implement task-based agent executor
class TaskAgentExecutor implements AgentExecutor {
  private cancelledTasks = new Set<string>();

  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { taskId, contextId, userMessage, task } = requestContext;
    const userText = userMessage.parts.find(part => part.kind === 'text')?.text || '';

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

    try {
      // Simulate multi-step processing
      await this.processWithCancellation(taskId, contextId, userText, eventBus);

      // Mark as completed
      eventBus.publish({
        kind: 'status-update',
        taskId,
        contextId,
        status: { state: 'completed', timestamp: new Date().toISOString() },
        final: true,
      });

    } catch (error) {
      // Handle task failure
      eventBus.publish({
        kind: 'status-update',
        taskId,
        contextId,
        status: { 
          state: 'failed', 
          timestamp: new Date().toISOString(),
          error: { message: 'Task processing failed' }
        },
        final: true,
      });
    } finally {
      this.cancelledTasks.delete(taskId);
    }

    eventBus.finished();
  }

  private async processWithCancellation(
    taskId: string, 
    contextId: string, 
    input: string, 
    eventBus: ExecutionEventBus
  ): Promise<void> {
    // Step 1: Data analysis
    await this.simulateWork(taskId, contextId, 'Analyzing input data...', 1000);
    
    // Check for cancellation
    if (this.cancelledTasks.has(taskId)) {
      throw new Error('Task was cancelled');
    }

    // Create analysis artifact
    const analysisResult = this.analyzeInput(input);
    eventBus.publish({
      kind: 'artifact-update',
      taskId,
      contextId,
      artifact: {
        artifactId: 'analysis-' + Date.now(),
        name: 'analysis_report.txt',
        parts: [{
          kind: 'text',
          text: `Analysis Report\n================\nInput: "${input}"\n${analysisResult}`,
        }],
      },
    });

    // Step 2: Processing
    await this.simulateWork(taskId, contextId, 'Processing analysis results...', 1500);
    
    // Check for cancellation again
    if (this.cancelledTasks.has(taskId)) {
      throw new Error('Task was cancelled');
    }

    // Create final result artifact
    const processedResult = this.processAnalysis(input, analysisResult);
    eventBus.publish({
      kind: 'artifact-update',
      taskId,
      contextId,
      artifact: {
        artifactId: 'result-' + Date.now(),
        name: 'processed_result.txt',
        parts: [{
          kind: 'text',
          text: `Processed Result\n==================\n${processedResult}`,
        }],
      },
    });
  }

  private async simulateWork(taskId: string, contextId: string, description: string, duration: number): Promise<void> {
    eventBus.publish({
      kind: 'status-update',
      taskId,
      contextId,
      status: { 
        state: 'working', 
        timestamp: new Date().toISOString(),
        message: description
      },
      final: false,
    });
    
    await new Promise(resolve => setTimeout(resolve, duration));
  }

  private analyzeInput(input: string): string {
    const words = input.split(' ').length;
    const chars = input.length;
    const lines = input.split('\n').length;
    
    return `Word count: ${words}\nCharacter count: ${chars}\nLine count: ${lines}\nAnalysis completed at ${new Date().toISOString()}`;
  }

  private processAnalysis(input: string, analysis: string): string {
    return `Original Input: "${input}"\n\nAnalysis Summary:\n${analysis}\n\nProcessing completed at ${new Date().toISOString()}`;
  }

  async cancelTask(taskId: string, eventBus: ExecutionEventBus): Promise<void> {
    this.cancelledTasks.add(taskId);
    
    eventBus.publish({
      kind: 'status-update',
      taskId,
      contextId: '',
      status: { 
        state: 'canceled', 
        timestamp: new Date().toISOString(),
        message: 'Task was cancelled by user'
      },
      final: true,
    });
    
    eventBus.finished();
  }
}

// 3. Setup and run server
const agentExecutor = new TaskAgentExecutor();
const requestHandler = new DefaultRequestHandler(
  agentCard,
  new InMemoryTaskStore(),
  agentExecutor
);

const app = express();

app.use(express.json());

// Agent Card endpoint
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

// Additional REST endpoints for manual testing
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', timestamp: new Date().toISOString() });
});

app.get('/tasks', (req, res) => {
  res.json({ message: 'Use A2A protocol endpoints to create and manage tasks' });
});

// Start server
const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`🚀 Task-based A2A Agent server running on http://localhost:${PORT}`);
  console.log(`📋 Agent Card: http://localhost:${PORT}/.well-known/agent-card.json`);
  console.log(`🔌 JSON-RPC: http://localhost:${PORT}/a2a/jsonrpc`);
  console.log(`🌐 REST API: http://localhost:${PORT}/a2a/rest`);
  console.log(`❤️ Health Check: http://localhost:${PORT}/health`);
});
```

## Features

- **Task Management**: Creates and manages long-running tasks
- **Progress Updates**: Provides status updates during processing
- **Artifacts**: Generates analysis and result files
- **Cancellation**: Supports task cancellation during execution
- **Streaming**: Real-time updates via SSE
- **Error Handling**: Graceful failure handling

## Usage

1. **Start server:**
```bash
npx ts-node task-server.ts
```

2. **Test task creation:**
```bash
curl -X POST http://localhost:4000/a2a/rest/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "messageId": "task-test-123",
      "role": "user", 
      "parts": [{"kind": "text", "text": "Analyze this sample text for me"}],
      "kind": "message"
    }
  }'
```

3. **Stream task updates:**
```bash
curl -N http://localhost:4000/a2a/rest/message/stream \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "messageId": "stream-test-123",
      "role": "user",
      "parts": [{"kind": "text", "text": "Process this with streaming"}],
      "kind": "message"
    }
  }'
```