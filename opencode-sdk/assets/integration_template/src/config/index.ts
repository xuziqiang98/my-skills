import dotenv from "dotenv"
import { OpenCodeConfig, AppConfig } from "../types/config.js"

dotenv.config()

export const openCodeConfig: OpenCodeConfig = {
  baseUrl: process.env.OPENCODE_BASE_URL || "http://localhost:4096",
  hostname: process.env.OPENCODE_HOSTNAME || "127.0.0.1",
  port: parseInt(process.env.OPENCODE_PORT || "4096"),
  model: {
    providerID: process.env.DEFAULT_PROVIDER || "anthropic",
    modelID: process.env.DEFAULT_MODEL || "claude-3-5-sonnet-20241022"
  },
  timeout: parseInt(process.env.TIMEOUT || "5000"),
  retries: {
    maxAttempts: parseInt(process.env.MAX_RETRIES || "3"),
    baseDelay: parseInt(process.env.RETRY_DELAY_BASE || "1000")
  }
}

export const appConfig: AppConfig = {
  name: process.env.APP_NAME || "OpenCode Integration",
  version: process.env.APP_VERSION || "1.0.0",
  sessionTimeout: parseInt(process.env.SESSION_TIMEOUT || "300000"),
  logLevel: (process.env.LOG_LEVEL as any) || "info",
  logFilePath: process.env.LOG_FILE_PATH || "./logs/app.log",
  environment: (process.env.NODE_ENV as any) || "development"
}

export const authConfigs = {
  anthropic: {
    provider: "anthropic",
    credentials: {
      type: "api",
      key: process.env.ANTHROPIC_API_KEY
    }
  },
  openai: {
    provider: "openai",
    credentials: {
      type: "api",
      key: process.env.OPENAI_API_KEY
    }
  }
}