# OpenCode Integration Template

A comprehensive, production-ready template for building applications with the OpenCode SDK. This template includes best practices for error handling, logging, retry logic, and project structure.

## Features

- **TypeScript Support**: Full type safety and IntelliSense
- **Modular Architecture**: Clean separation of concerns
- **Error Handling**: Comprehensive error handling with retry logic
- **Logging**: Structured logging with Winston
- **Configuration**: Environment-based configuration management
- **Testing**: Jest test framework setup
- **Linting**: ESLint and Prettier for code quality
- **Build System**: TypeScript compilation and bundling

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Environment Setup

Copy the environment template and configure:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
OPENCODE_BASE_URL=http://localhost:4096
ANTHROPIC_API_KEY=your_api_key_here
LOG_LEVEL=info
```

### 3. Build and Run

```bash
# Development mode
npm run dev

# Build for production
npm run build
npm start
```

## Project Structure

```
src/
├── config/           # Configuration management
├── services/         # Business logic services
│   ├── client.ts     # OpenCode client factory
│   └── session.ts    # Session management
├── utils/            # Utility functions
│   ├── logger.ts     # Logging configuration
│   └── retry.ts      # Retry logic
├── types/            # TypeScript type definitions
│   └── config.ts     # Configuration types
└── index.ts          # Main entry point
```

## Usage Examples

### Basic Session Management

```typescript
import { integration } from "./src/index.js"

await integration.initialize()

// Create a session
const session = await integration.createSession("My Session")

// Send a message
const response = await integration.sendMessage(
  session.id, 
  "Hello! Can you help me with TypeScript?"
)

// List all sessions
const sessions = await integration.listSessions()
```

### Advanced Usage

```typescript
import { ClientFactory } from "./src/services/client.js"
import { SessionService } from "./src/services/session.js"

// Configure client factory
ClientFactory.configure({
  baseUrl: "http://localhost:4096",
  model: {
    providerID: "anthropic",
    modelID: "claude-3-5-sonnet-20241022"
  }
})

// Use services directly
const sessionService = new SessionService()
const session = await sessionService.createSession({
  title: "Advanced Session",
  metadata: { project: "my-app", environment: "dev" }
})
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENCODE_BASE_URL` | OpenCode server URL | `http://localhost:4096` |
| `DEFAULT_PROVIDER` | Default AI provider | `anthropic` |
| `DEFAULT_MODEL` | Default AI model | `claude-3-5-sonnet-20241022` |
| `ANTHROPIC_API_KEY` | Anthropic API key | - |
| `LOG_LEVEL` | Logging level | `info` |
| `MAX_RETRIES` | Maximum retry attempts | `3` |
| `NODE_ENV` | Environment | `development` |

### Configuration Files

- `src/config/index.ts` - Main configuration
- `src/types/config.ts` - Type definitions
- `.env.example` - Environment template

## Error Handling

The template includes comprehensive error handling:

```typescript
import { RetryManager } from "./src/utils/retry.js"

const retryManager = new RetryManager({
  maxAttempts: 3,
  baseDelay: 1000
})

await retryManager.execute(
  async () => {
    // Your operation here
  },
  "operation.name",
  { context: "data" }
)
```

## Logging

Structured logging with multiple outputs:

```typescript
import { logger } from "./src/utils/logger.js"

logger.info("Operation completed", { sessionId: "123" })
logger.error("Operation failed", { error: "message", context: {} })
```

## Testing

```bash
# Run tests
npm test

# Watch mode
npm run test:watch
```

## Code Quality

```bash
# Lint code
npm run lint

# Fix linting issues
npm run lint:fix

# Format code
npm run format
```

## Deployment

### Build for Production

```bash
npm run build
```

The compiled JavaScript will be in the `dist/` directory.

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY dist/ ./dist/
CMD ["node", "dist/index.js"]
```

## Best Practices

1. **Always handle errors**: Use try-catch blocks and the retry manager
2. **Use structured logging**: Include context in all log messages
3. **Configure properly**: Set up environment variables before running
4. **Type safety**: Leverage TypeScript for better development experience
5. **Modular design**: Keep services focused and single-purpose

## Troubleshooting

### Connection Issues

- Verify OpenCode server is running
- Check `OPENCODE_BASE_URL` configuration
- Review network connectivity

### Authentication Problems

- Ensure API keys are set in environment
- Verify provider credentials
- Check authentication setup

### Performance Issues

- Adjust retry configuration
- Monitor log levels
- Review timeout settings

## Contributing

1. Follow the existing code style
2. Add tests for new features
3. Update documentation
4. Use semantic versioning

## License

MIT License - see LICENSE file for details.