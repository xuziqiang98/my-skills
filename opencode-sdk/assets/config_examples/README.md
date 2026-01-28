# Configuration Examples

This directory contains configuration examples for different use cases and environments. Each subdirectory shows how to configure the OpenCode SDK integration for specific scenarios.

## Available Examples

### 1. Development (`development/`)
Optimized for local development with:
- Verbose debugging logs
- Fast, cost-effective models (Claude Haiku)
- Aggressive retry settings
- Local server configuration

### 2. Production (`production/`)
Optimized for production deployment with:
- Minimal logging (warn level)
- Reliable models (Claude Sonnet)
- Conservative retry settings
- Security and monitoring features
- Rate limiting and metrics

### 3. Testing (`testing/`)
Optimized for automated testing with:
- Mock responses when possible
- Minimal retry attempts
- Fast, cheap models
- Test database configuration
- Coverage reporting

### 4. Multi-Provider (`multi_provider/`)
Shows how to use multiple AI providers with:
- Provider fallback strategies
- Load balancing
- Cost management
- Health checks and failover
- Provider-specific configurations

### 5. Custom Models (`custom_models/`)
Demonstrates integration with custom or local models:
- Local model hosting (Ollama)
- Hugging Face integration
- Custom API endpoints
- Intent-based model routing
- Performance monitoring

## Usage

Copy the appropriate example to your project root and customize:

```bash
# For development
cp assets/config_examples/development/.env .env

# For production
cp assets/config_examples/production/.env .env

# For multi-provider setup
cp assets/config_examples/multi_provider/.env .env
```

## Configuration Categories

### Server Settings
- `OPENCODE_BASE_URL`: OpenCode server URL
- `OPENCODE_HOSTNAME`: Server hostname
- `OPENCODE_PORT`: Server port

### Model Configuration
- `DEFAULT_PROVIDER`: Primary AI provider
- `DEFAULT_MODEL`: Default model ID
- Provider-specific API keys and settings

### Logging
- `LOG_LEVEL`: Logging verbosity (error, warn, info, debug)
- `LOG_FILE_PATH`: Log file location

### Application
- `APP_NAME`: Application name
- `NODE_ENV`: Environment (development, production, test)
- `SESSION_TIMEOUT`: Session timeout in milliseconds

### Retry Logic
- `MAX_RETRIES`: Maximum retry attempts
- `RETRY_DELAY_BASE`: Base delay for exponential backoff

### Advanced Features
- Rate limiting
- Cost management
- Health monitoring
- Load balancing
- Failover configuration

## Security Considerations

1. **Never commit API keys** to version control
2. **Use environment variables** for sensitive data
3. **Enable SSL/TLS** in production
4. **Implement rate limiting** for public deployments
5. **Use key management services** in production environments

## Performance Optimization

1. **Choose appropriate models** for each environment
2. **Configure timeouts** based on model performance
3. **Enable caching** for repeated requests
4. **Monitor usage patterns** and adjust configurations
5. **Use load balancing** for high-traffic applications

## Cost Management

1. **Set budget limits** in multi-provider configurations
2. **Choose cost-effective models** for development
3. **Implement usage tracking** and alerts
4. **Use model routing** to optimize costs
5. **Monitor token usage** patterns

## Environment-Specific Best Practices

### Development
- Use fast, cheap models
- Enable verbose logging
- Configure aggressive retrying
- Use local instances when possible

### Production
- Use reliable, proven models
- Implement monitoring and alerting
- Configure conservative retrying
- Enable security features

### Testing
- Use mock responses when possible
- Configure minimal retrying
- Use deterministic test data
- Enable coverage reporting

### Multi-Provider
- Implement proper fallback logic
- Monitor provider health
- Balance costs and performance
- Configure provider-specific settings