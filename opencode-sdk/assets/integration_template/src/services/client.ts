import { createOpencode, createOpencodeClient } from "@opencode-ai/sdk"
import type { OpenCodeConfig } from "../types/config.js"
import { logger } from "../utils/logger.js"

/**
 * OpenCode client factory
 * Creates and configures OpenCode client instances
 */
export class ClientFactory {
  private static instance: any = null
  private static config: OpenCodeConfig

  /**
   * Configure the client factory
   */
  static configure(config: OpenCodeConfig): void {
    this.config = config
    logger.info("Client factory configured", { baseUrl: config.baseUrl })
  }

  /**
   * Get singleton client instance
   */
  static async getClient(): Promise<any> {
    if (!this.instance) {
      if (!this.config) {
        throw new Error("Client factory not configured. Call configure() first.")
      }

      try {
        this.instance = createOpencodeClient({
          baseUrl: this.config.baseUrl,
          throwOnError: true
        })
        
        logger.info("OpenCode client created successfully")
        
        const health = await this.instance.global.health()
        logger.info("Server health check passed", { 
          healthy: health.data.healthy,
          version: health.data.version 
        })
        
      } catch (error) {
        logger.error("Failed to create OpenCode client", { error: error.message })
        this.instance = null
        throw error
      }
    }

    return this.instance
  }

  /**
   * Create new server and client instance
   */
  static async createServerAndClient(): Promise<{ client: any; server: any }> {
    if (!this.config) {
      throw new Error("Client factory not configured. Call configure() first.")
    }

    try {
      const { client, server } = await createOpencode({
        hostname: this.config.hostname,
        port: this.config.port,
        config: {
          model: `${this.config.model.providerID}/${this.config.model.modelID}`
        },
        timeout: this.config.timeout || 5000
      })

      logger.info("OpenCode server and client created", {
        url: server.url,
        hostname: this.config.hostname,
        port: this.config.port
      })

      return { client, server }
    } catch (error) {
      logger.error("Failed to create OpenCode server", { error: error.message })
      throw error
    }
  }

  /**
   * Reset singleton instance
   */
  static reset(): void {
    this.instance = null
    logger.info("Client factory reset")
  }

  /**
   * Check if client is initialized
   */
  static isInitialized(): boolean {
    return this.instance !== null
  }
}