export interface OpenCodeConfig {
  baseUrl: string
  hostname: string
  port: number
  model: {
    providerID: string
    modelID: string
  }
  timeout?: number
  retries?: {
    maxAttempts: number
    baseDelay: number
  }
}

export interface AppConfig {
  name: string
  version: string
  sessionTimeout: number
  logLevel: 'error' | 'warn' | 'info' | 'debug'
  logFilePath: string
  environment: 'development' | 'production' | 'test'
}

export interface SessionConfig {
  title: string
  metadata?: Record<string, any>
  model?: {
    providerID: string
    modelID: string
  }
  timeout?: number
}

export interface MessageConfig {
  sessionId: string
  content: string
  model?: {
    providerID: string
    modelID: string
  }
  parts?: Array<{
    type: 'text' | 'image' | 'file'
    text?: string
    image?: string
    file?: string
  }>
}

export interface FileOperationConfig {
  path: string
  content?: string
  searchPattern?: string
  fileType?: 'file' | 'directory'
  searchType?: 'text' | 'files' | 'symbols'
}

export interface EventConfig {
  events: string[]
  handlers: Map<string, (event: any) => void | Promise<void>>
  autoReconnect?: boolean
  reconnectDelay?: number
}

export interface AuthConfig {
  provider: string
  credentials: {
    type: 'api' | 'oauth'
    key?: string
    token?: string
    [key: string]: any
  }
}