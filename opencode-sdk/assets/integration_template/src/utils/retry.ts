interface RetryOptions {
  maxAttempts?: number
  baseDelay?: number
  shouldRetry?: (error: Error) => boolean
}

export class RetryManager {
  private maxAttempts: number
  private baseDelay: number

  constructor(options: RetryOptions = {}) {
    this.maxAttempts = options.maxAttempts || 3
    this.baseDelay = options.baseDelay || 1000
  }

  async execute<T>(
    operation: () => Promise<T>,
    operationName: string,
    context?: Record<string, any>
  ): Promise<T> {
    let lastError: Error
    
    for (let attempt = 1; attempt <= this.maxAttempts; attempt++) {
      try {
        return await operation()
      } catch (error) {
        lastError = error as Error
        
        if (attempt === this.maxAttempts) {
          break
        }
        
        const shouldRetry = this.shouldRetryError(lastError)
        if (!shouldRetry) {
          break
        }
        
        const delay = this.calculateDelay(attempt)
        logger.warn(`${operationName} failed, retrying...`, {
          attempt,
          maxAttempts: this.maxAttempts,
          delay,
          error: lastError.message,
          context
        })
        
        await this.delay(delay)
      }
    }
    
    logger.error(`${operationName} failed after ${this.maxAttempts} attempts`, {
      error: lastError.message,
      context
    })
    
    throw lastError
  }

  private shouldRetryError(error: Error): boolean {
    const retryablePatterns = [
      /ECONNREFUSED/,
      /timeout/,
      /ENOTFOUND/,
      /ECONNRESET/,
      /502/,
      /503/,
      /504/
    ]
    
    return retryablePatterns.some(pattern => pattern.test(error.message))
  }

  private calculateDelay(attempt: number): number {
    return this.baseDelay * Math.pow(2, attempt - 1)
  }

  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms))
  }
}