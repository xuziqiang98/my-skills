import type { SessionConfig, MessageConfig } from "../types/config.js"
import { ClientFactory } from "./client.js"
import { logger } from "../utils/logger.js"
import { RetryManager } from "../utils/retry.js"

/**
 * Session management service
 * Handles OpenCode session lifecycle operations
 */
export class SessionService {
  private retryManager: RetryManager

  constructor() {
    this.retryManager = new RetryManager()
  }

  /**
   * Create a new session
   */
  async createSession(config: SessionConfig): Promise<any> {
    const client = await ClientFactory.getClient()
    
    return this.retryManager.execute(
      async () => {
        const session = await client.session.create({
          body: {
            title: config.title,
            metadata: config.metadata
          }
        })
        
        logger.info("Session created", { 
          sessionId: session.data.id,
          title: config.title 
        })
        
        return session.data
      },
      "session.create",
      { title: config.title }
    )
  }

  /**
   * Get session by ID
   */
  async getSession(sessionId: string): Promise<any> {
    const client = await ClientFactory.getClient()
    
    return this.retryManager.execute(
      async () => {
        const session = await client.session.get({
          path: { id: sessionId }
        })
        
        logger.debug("Session retrieved", { sessionId })
        return session.data
      },
      "session.get",
      { sessionId }
    )
  }

  /**
   * List all sessions
   */
  async listSessions(): Promise<any[]> {
    const client = await ClientFactory.getClient()
    
    return this.retryManager.execute(
      async () => {
        const sessions = await client.session.list()
        
        logger.debug("Sessions listed", { 
          count: sessions.data.length 
        })
        
        return sessions.data
      },
      "session.list"
    )
  }

  /**
   * Update session
   */
  async updateSession(sessionId: string, updates: Partial<SessionConfig>): Promise<any> {
    const client = await ClientFactory.getClient()
    
    return this.retryManager.execute(
      async () => {
        const session = await client.session.update({
          path: { id: sessionId },
          body: {
            title: updates.title,
            metadata: updates.metadata
          }
        })
        
        logger.info("Session updated", { sessionId })
        return session.data
      },
      "session.update",
      { sessionId, updates }
    )
  }

  /**
   * Delete session
   */
  async deleteSession(sessionId: string): Promise<boolean> {
    const client = await ClientFactory.getClient()
    
    return this.retryManager.execute(
      async () => {
        const result = await client.session.delete({
          path: { id: sessionId }
        })
        
        logger.info("Session deleted", { sessionId })
        return result.data
      },
      "session.delete",
      { sessionId }
    )
  }

  /**
   * Send message to session
   */
  async sendMessage(config: MessageConfig): Promise<any> {
    const client = await ClientFactory.getClient()
    
    return this.retryManager.execute(
      async () => {
        const message = await client.session.prompt({
          path: { id: config.sessionId },
          body: {
            model: config.model,
            parts: config.parts || [{ type: "text", text: config.content }]
          }
        })
        
        logger.info("Message sent", { 
          sessionId: config.sessionId,
          responseLength: message.data.parts?.[0]?.text?.length || 0
        })
        
        return message.data
      },
      "session.prompt",
      { sessionId: config.sessionId }
    )
  }

  /**
   * Get session messages
   */
  async getSessionMessages(sessionId: string): Promise<any[]> {
    const client = await ClientFactory.getClient()
    
    return this.retryManager.execute(
      async () => {
        const messages = await client.session.messages({
          path: { id: sessionId }
        })
        
        logger.debug("Messages retrieved", { 
          sessionId,
          count: messages.data.length 
        })
        
        return messages.data
      },
      "session.messages",
      { sessionId }
    )
  }

  /**
   * Abort session
   */
  async abortSession(sessionId: string): Promise<boolean> {
    const client = await ClientFactory.getClient()
    
    return this.retryManager.execute(
      async () => {
        const result = await client.session.abort({
          path: { id: sessionId }
        })
        
        logger.info("Session aborted", { sessionId })
        return result.data
      },
      "session.abort",
      { sessionId }
    )
  }
}