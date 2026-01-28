# Basic OpenCode Client

A minimal example of how to set up and use the OpenCode SDK for basic operations.

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Start OpenCode Server

Make sure you have an OpenCode server running on `http://localhost:4096`, or modify the `CONFIG.baseUrl` in `index.js` to point to your server.

### 3. Run the Example

```bash
npm start
```

## What This Example Shows

This example demonstrates basic OpenCode SDK usage including:

- **Client Creation**: Connect to an existing OpenCode server
- **Session Management**: Create and list sessions
- **Messaging**: Send messages to sessions and receive responses
- **File Operations**: Search for text and read files
- **Health Checks**: Verify server connectivity

## Configuration

Edit the `CONFIG` object in `index.js` to customize:

```javascript
const CONFIG = {
  baseUrl: "http://localhost:4096",
  model: {
    providerID: "anthropic",
    modelID: "claude-3-5-sonnet-20241022"
  }
}
```

## Usage Patterns

### Creating a Client

```javascript
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({
  baseUrl: "http://localhost:4096"
})

const openCode = new BasicOpenCodeClient(client)
```

### Working with Sessions

```javascript
// Create a new session
const session = await openCode.createSession("My Session")

// Send a message
await openCode.sendMessage(session.id, "Hello!")

// List all sessions
const sessions = await openCode.listSessions()
```

### File Operations

```javascript
// Search for text
const results = await openCode.searchText("function.*client")

// Read a file
const content = await openCode.readFile("README.md")
```

## Error Handling

The example includes basic error handling with try-catch blocks and informative error messages. In production code, you might want to implement more sophisticated error handling patterns.

## Next Steps

- Explore more advanced SDK features
- Implement proper error handling and retry logic
- Add authentication setup
- Build real-time event handling
- Create automated workflows

For more comprehensive examples, see the `integration_template` directory.