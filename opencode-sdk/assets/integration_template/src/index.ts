import { ClientFactory } from "./services/client.js"
import { SessionService } from "./services/session.js"
import { openCodeConfig } from "./config/index.js"
import { logger } from "./utils/logger.js"

class OpenCodeIntegration {
  private sessionService: SessionService

  constructor() {
    this.sessionService = new SessionService()
  }

  async initialize(): Promise<void> {
    try {
      ClientFactory.configure(openCodeConfig)
      await ClientFactory.getClient()
      
      logger.info("OpenCode integration initialized successfully")
    } catch (error) {
      logger.error("Failed to initialize OpenCode integration", { error: error.message })
      throw error
    }
  }

  async createSession(title: string, metadata?: Record<string, any>) {
    return this.sessionService.createSession({ title, metadata })
  }

  async listSessions() {
    return this.sessionService.listSessions()
  }

  async sendMessage(sessionId: string, content: string) {
    return this.sessionService.sendMessage({
      sessionId,
      content,
      model: openCodeConfig.model
    })
  }

  async getSession(sessionId: string) {
    return this.sessionService.getSession(sessionId)
  }

  async deleteSession(sessionId: string) {
    return this.sessionService.deleteSession(sessionId)
  }
}

const integration = new OpenCodeIntegration()

if (import.meta.url === `file://${process.argv[1]}`) {
  integration.initialize()
    .then(async () => {
      const sessions = await integration.listSessions()
      console.log(`Found ${sessions.length} sessions`)

      if (sessions.length === 0) {
        const session = await integration.createSession("Demo Session")
        console.log(`Created session: ${session.id}`)
        
        const response = await integration.sendMessage(session.id, "Hello! What can you do?")
        console.log("Response:", response.parts?.[0]?.text)
      }
    })
    .catch(console.error)
}

export { OpenCodeIntegration, integration }