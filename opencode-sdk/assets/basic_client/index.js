/**
 * Basic OpenCode Client Example
 * 
 * This is a minimal example of how to set up and use the OpenCode SDK
 * for basic session management and file operations.
 */

import { createOpencode, createOpencodeClient } from "@opencode-ai/sdk"


const CONFIG = {
  baseUrl: "http://localhost:4096",
  model: {
    providerID: "anthropic",
    modelID: "claude-3-5-sonnet-20241022"
  }
}

class BasicOpenCodeClient {
  constructor(client) {
    this.client = client
  }

  /**
   * Create a new session
   */
  async createSession(title) {
    try {
      const session = await this.client.session.create({
        body: { title }
      })
      console.log(`✅ Created session: ${session.data.id}`)
      return session.data
    } catch (error) {
      console.error(`❌ Failed to create session: ${error.message}`)
      throw error
    }
  }

  /**
   * List all sessions
   */
  async listSessions() {
    try {
      const sessions = await this.client.session.list()
      console.log(`📋 Found ${sessions.data.length} sessions:`)
      sessions.data.forEach(session => {
        console.log(`  - ${session.id}: ${session.title} (${session.messageCount} messages)`)
      })
      return sessions.data
    } catch (error) {
      console.error(`❌ Failed to list sessions: ${error.message}`)
      throw error
    }
  }

  /**
   * Send a message to a session
   */
  async sendMessage(sessionId, message) {
    try {
      const result = await this.client.session.prompt({
        path: { id: sessionId },
        body: {
          model: CONFIG.model,
          parts: [{ type: "text", text: message }]
        }
      })
      console.log(`🤖 Response: ${result.data.parts?.[0]?.text || "No text response"}`)
      return result.data
    } catch (error) {
      console.error(`❌ Failed to send message: ${error.message}`)
      throw error
    }
  }

  /**
   * Search for text in files
   */
  async searchText(pattern) {
    try {
      const results = await this.client.find.text({
        query: { pattern }
      })
      console.log(`🔍 Found ${results.data.length} matches for pattern: ${pattern}`)
      results.data.forEach(match => {
        console.log(`  - ${match.path}:${match.lineNumber}`)
      })
      return results.data
    } catch (error) {
      console.error(`❌ Failed to search text: ${error.message}`)
      throw error
    }
  }

  /**
   * Read a file
   */
  async readFile(path) {
    try {
      const file = await this.client.file.read({
        query: { path }
      })
      console.log(`📄 Read file: ${path}`)
      return file.data.content
    } catch (error) {
      console.error(`❌ Failed to read file ${path}: ${error.message}`)
      throw error
    }
  }

  /**
   * Check server health
   */
  async checkHealth() {
    try {
      const health = await this.client.global.health()
      console.log(`🏥 Server health: ${health.data.healthy ? "OK" : "NOT OK"}`)
      console.log(`📦 Version: ${health.data.version}`)
      return health.data
    } catch (error) {
      console.error(`❌ Failed to check health: ${error.message}`)
      throw error
    }
  }
}

/**
 * Create and connect to OpenCode client
 */
async function createClient() {
  try {
    // Option 1: Connect to existing server
    const client = createOpencodeClient({
      baseUrl: CONFIG.baseUrl
    })
    
    // Option 2: Start new server and client (comment out above and uncomment below)
    // const { client } = await createOpencode({
    //   hostname: "127.0.0.1",
    //   port: 4096,
    //   config: {
    //     model: "anthropic/claude-3-5-sonnet-20241022"
    //   }
    // })
    
    return new BasicOpenCodeClient(client)
  } catch (error) {
    console.error(`❌ Failed to create client: ${error.message}`)
    throw error
  }
}

/**
 * Example usage
 */
async function main() {
  console.log("🚀 Starting OpenCode Basic Client Example\n")

  try {
    const openCode = await createClient()
    
    await openCode.checkHealth()
    console.log()
    
    await openCode.listSessions()
    console.log()
    
    const session = await openCode.createSession("Basic Client Demo")
    console.log()
    
    await openCode.sendMessage(session.id, "Hello! Can you help me understand the OpenCode SDK?")
    console.log()
    
    await openCode.searchText("function.*client")
    console.log()
    
    try {
      await openCode.readFile("README.md")
    } catch (error) {
      console.log("ℹ️  File read failed as expected (file may not exist)")
    }
    
    console.log("\n✅ Example completed successfully!")
    
  } catch (error) {
    console.error("\n💥 Example failed:", error.message)
    process.exit(1)
  }
}


if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error)
}

export { BasicOpenCodeClient, createClient }