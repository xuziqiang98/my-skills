# A2A Authentication Examples

This directory contains examples of implementing authentication in A2A agents and clients.

## Bearer Token Authentication

### Authenticated Server Example

```typescript
// authenticated-server.ts
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
  UserBuilder,
  UserContext
} from '@a2a-js/sdk/server/express';

// 1. Define agent card (same as basic server)
const agentCard: AgentCard = {
  name: 'Authenticated A2A Agent',
  description: 'An A2A agent with bearer token authentication',
  protocolVersion: '0.3.0',
  version: '1.0.0',
  url: 'http://localhost:4000/a2a/jsonrpc',
  skills: [
    { 
      id: 'secure-chat', 
      name: 'Secure Chat', 
      description: 'Authenticated conversation with the agent',
      tags: ['chat', 'authenticated', 'secure']
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

// 2. Authentication middleware
class BearerTokenAuth {
  private validTokens = new Set<string>();

  constructor() {
    // Add some demo tokens
    this.validTokens.add('demo-token-123');
    this.validTokens.add('secure-token-456');
  }

  validateToken(token: string): boolean {
    return this.validTokens.has(token);
  }

  addUserToken(token: string): void {
    this.validTokens.add(token);
  }

  removeUserToken(token: string): void {
    this.validTokens.delete(token);
  }
}

const authService = new BearerTokenAuth();

// 3. User builder with authentication
class AuthenticatedUserBuilder implements UserBuilder {
  async build(headers: Record<string, string>): Promise<UserContext> {
    const authHeader = headers['authorization'];
    
    if (!authHeader || !authHeader.startsWith('Bearer ')) {
      throw new Error('Missing or invalid authorization header');
    }

    const token = authHeader.substring(7); // Remove 'Bearer ' prefix
    
    if (!authService.validateToken(token)) {
      throw new Error('Invalid or expired token');
    }

    return {
      id: `user-${token.substring(0, 8)}`,
      metadata: {
        token: token,
        authenticated: true,
        authTime: new Date().toISOString(),
      },
    };
  }
}

// 4. Authenticated agent executor
class AuthenticatedAgentExecutor implements AgentExecutor {
  async execute(requestContext: RequestContext, eventBus: ExecutionEventBus): Promise<void> {
    const { userMessage, contextId, user } = requestContext;
    const userText = userMessage.parts.find(part => part.kind === 'text')?.text || '';

    // Create personalized response
    const response: Message = {
      kind: 'message',
      messageId: uuidv4(),
      role: 'agent',
      parts: [{ 
        kind: 'text', 
        text: `Hello ${user?.id || 'authenticated user'}! You said: "${userText}". Your request is authenticated and secure.` 
      }],
      contextId,
    };

    eventBus.publish(response);
    eventBus.finished();
  }

  async cancelTask(): Promise<void> {
    // Handle cancellation if needed
  }
}

// 5. Setup server with authentication
const agentExecutor = new AuthenticatedAgentExecutor();
const requestHandler = new DefaultRequestHandler(
  agentCard,
  new InMemoryTaskStore(),
  agentExecutor
);

const app = express();

// Add authentication endpoint for token management
app.post('/auth/login', express.json(), (req, res) => {
  const { username, password } = req.body;
  
  // Simple authentication check (in production, use proper auth)
  if (username === 'demo' && password === 'password') {
    const token = `token-${uuidv4()}`;
    authService.addUserToken(token);
    res.json({ token, expiresIn: '1h' });
  } else {
    res.status(401).json({ error: 'Invalid credentials' });
  }
});

app.post('/auth/logout', express.json(), (req, res) => {
  const { token } = req.body;
  authService.removeUserToken(token);
  res.json({ message: 'Logged out successfully' });
});

app.get('/auth/status', (req, res) => {
  const authHeader = req.headers['authorization'];
  if (authHeader && authHeader.startsWith('Bearer ')) {
    const token = authHeader.substring(7);
    const isValid = authService.validateToken(token);
    res.json({ authenticated: isValid, token: token.substring(0, 8) + '...' });
  } else {
    res.json({ authenticated: false });
  }
});

// Agent Card endpoint (public)
app.use(`/.well-known/agent-card.json`, agentCardHandler({ 
  agentCardProvider: requestHandler 
}));

// Authenticated endpoints
app.use('/a2a/jsonrpc', jsonRpcHandler({ 
  requestHandler,
  userBuilder: new AuthenticatedUserBuilder()
}));

app.use('/a2a/rest', restHandler({ 
  requestHandler,
  userBuilder: new AuthenticatedUserBuilder()
}));

// Start server
const PORT = process.env.PORT || 4000;
app.listen(PORT, () => {
  console.log(`🔐 Authenticated A2A Agent server running on http://localhost:${PORT}`);
  console.log(`📋 Agent Card: http://localhost:${PORT}/.well-known/agent-card.json`);
  console.log(`🔌 JSON-RPC: http://localhost:${PORT}/a2a/jsonrpc`);
  console.log(`🌐 REST API: http://localhost:${PORT}/a2a/rest`);
  console.log(`🔑 Auth Login: POST http://localhost:${PORT}/auth/login`);
});
```

### Authenticated Client Example

```typescript
// authenticated-client.ts
import { ClientFactory, ClientFactoryOptions } from '@a2a-js/sdk/client';
import { 
  AuthenticationHandler,
  createAuthenticatingFetchWithRetry,
  JsonRpcTransportFactory 
} from '@a2a-js/sdk/client';
import { MessageSendParams, v4 as uuidv4 } from '@a2a-js/sdk';

// 1. Token provider
class TokenProvider {
  private token: string | null = null;
  private refreshToken: string | null = null;

  async getCurrentToken(): Promise<string> {
    if (!this.token) {
      await this.login();
    }
    return this.token!;
  }

  async login(): Promise<void> {
    try {
      const response = await fetch('http://localhost:4000/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: 'demo', password: 'password' }),
      });

      if (!response.ok) {
        throw new Error('Login failed');
      }

      const data = await response.json();
      this.token = data.token;
      console.log('✅ Logged in successfully');
    } catch (error) {
      console.error('❌ Login error:', error);
      throw error;
    }
  }

  async refreshAuthToken(): Promise<string> {
    console.log('🔄 Refreshing authentication token...');
    await this.login();
    return this.token!;
  }

  async logout(): Promise<void> {
    if (this.token) {
      try {
        await fetch('http://localhost:4000/auth/logout', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ token: this.token }),
        });
      } catch (error) {
        console.error('Logout error:', error);
      }
    }
    this.token = null;
    this.refreshToken = null;
    console.log('✅ Logged out');
  }
}

// 2. Authentication handler
class BearerTokenAuthHandler implements AuthenticationHandler {
  constructor(private tokenProvider: TokenProvider) {}

  async headers(): Promise<Record<string, string>> {
    const token = await this.tokenProvider.getCurrentToken();
    return { Authorization: `Bearer ${token}` };
  }

  async shouldRetryWithHeaders(): Promise<Record<string, string> | undefined> {
    try {
      const newToken = await this.tokenProvider.refreshAuthToken();
      return { Authorization: `Bearer ${newToken}` };
    } catch (error) {
      console.error('❌ Token refresh failed:', error);
      return undefined;
    }
  }
}

// 3. Authenticated client class
class AuthenticatedA2AClient {
  private client: any;
  private tokenProvider: TokenProvider;
  private agentUrl: string;

  constructor(agentUrl: string) {
    this.agentUrl = agentUrl;
    this.tokenProvider = new TokenProvider();
  }

  async initialize(): Promise<void> {
    const authHandler = new BearerTokenAuthHandler(this.tokenProvider);
    const authFetch = createAuthenticatingFetchWithRetry(fetch, authHandler);

    const factory = new ClientFactory({
      transports: [new JsonRpcTransportFactory({ fetchImpl: authFetch })]
    });

    this.client = await factory.createFromUrl(this.agentUrl);
    console.log(`✅ Connected to authenticated A2A agent at ${this.agentUrl}`);
  }

  async sendMessage(text: string): Promise<any> {
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

    try {
      const response = await this.client.sendMessage(sendParams);
      
      if (response.kind === 'message') {
        return {
          type: 'message',
          content: response.parts[0].text,
          messageId: response.messageId,
        };
      }
      
      return response;
    } catch (error) {
      console.error('❌ Error sending authenticated message:', error);
      throw error;
    }
  }

  async checkAuthStatus(): Promise<boolean> {
    try {
      const token = await this.tokenProvider.getCurrentToken();
      const response = await fetch('http://localhost:4000/auth/status', {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      const data = await response.json();
      return data.authenticated;
    } catch (error) {
      console.error('❌ Error checking auth status:', error);
      return false;
    }
  }

  async logout(): Promise<void> {
    await this.tokenProvider.logout();
    this.client = null;
    console.log('✅ Client logged out and disconnected');
  }
}

// 4. Example usage
async function authenticatedClientExample() {
  const client = new AuthenticatedA2AClient('http://localhost:4000');

  try {
    // Initialize (this will trigger login)
    await client.initialize();

    // Check authentication status
    const isAuthed = await client.checkAuthStatus();
    console.log(`Authentication status: ${isAuthed ? '✅ Valid' : '❌ Invalid'}`);

    // Send authenticated messages
    console.log('💬 Sending authenticated message 1...');
    const response1 = await client.sendMessage('Hello from authenticated client!');
    console.log('Response 1:', response1);

    console.log('💬 Sending authenticated message 2...');
    const response2 = await client.sendMessage('This is a secure communication');
    console.log('Response 2:', response2);

    // Logout
    await client.logout();

  } catch (error) {
    console.error('❌ Authenticated client error:', error);
  }
}

// Run example if executed directly
if (require.main === module) {
  authenticatedClientExample();
}

export { 
  AuthenticatedA2AClient, 
  TokenProvider, 
  BearerTokenAuthHandler,
  authenticatedClientExample 
};
```

## Usage

1. **Start the authenticated server:**
```bash
npx ts-node authenticated-server.ts
```

2. **Run the authenticated client:**
```bash
npx ts-node authenticated-client.ts
```

3. **Test authentication manually:**
```bash
# Login
curl -X POST http://localhost:4000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "demo", "password": "password"}'

# Use token to send message
curl -X POST http://localhost:4000/a2a/rest/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "message": {
      "messageId": "auth-test-123",
      "role": "user",
      "parts": [{"kind": "text", "text": "Hello authenticated agent!"}],
      "kind": "message"
    }
  }'
```

## Features

- **Bearer Token Authentication**: Secure token-based authentication
- **Automatic Token Refresh**: Handles token expiration and refresh
- **User Context**: Provides user information to agent executors
- **Error Handling**: Comprehensive authentication error handling
- **Token Management**: Login, logout, and status checking
- **Security**: Validates tokens on every request

## Security Considerations

- Use HTTPS in production
- Implement proper token expiration
- Use secure token storage
- Validate tokens on every request
- Implement rate limiting
- Add audit logging