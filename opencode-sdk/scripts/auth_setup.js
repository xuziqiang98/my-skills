#!/usr/bin/env node

import fs from 'fs'

const authPatterns = {
  anthropic: `// Set up Anthropic authentication
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

await client.auth.set({
  path: { id: "anthropic" },
  body: { 
    type: "api", 
    key: process.env.ANTHROPIC_API_KEY 
  },
})

console.log("✅ Anthropic authentication configured")`,

  openai: `// Set up OpenAI authentication
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

await client.auth.set({
  path: { id: "openai" },
  body: { 
    type: "api", 
    key: process.env.OPENAI_API_KEY 
  },
})

console.log("✅ OpenAI authentication configured")`,

  multiple: `// Set up multiple provider authentication
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const providers = [
  {
    id: "anthropic",
    key: process.env.ANTHROPIC_API_KEY
  },
  {
    id: "openai", 
    key: process.env.OPENAI_API_KEY
  },
  {
    id: "google",
    key: process.env.GOOGLE_API_KEY
  }
]

for (const provider of providers) {
  if (provider.key) {
    await client.auth.set({
      path: { id: provider.id },
      body: { 
        type: "api", 
        key: provider.key 
      },
    })
    console.log(\`✅ \${provider.id} authentication configured\`)
  }
}`,

  withValidation: `// Set up authentication with validation
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

async function setupAuth(providerId, apiKey) {
  if (!apiKey) {
    throw new Error(\`Missing API key for \${providerId}\`)
  }

  try {
    await client.auth.set({
      path: { id: providerId },
      body: { 
        type: "api", 
        key: apiKey 
      },
    })
    
    console.log(\`✅ \${providerId} authentication configured\`)
    
    // Test the configuration
    const testSession = await client.session.create({
      body: { title: "Auth Test" }
    })
    
    await client.session.delete({
      path: { id: testSession.id }
    })
    
    console.log(\`✅ \${providerId} authentication verified\`)
    
  } catch (error) {
    console.error(\`❌ Failed to configure \${providerId}:\`, error.message)
    throw error
  }
}

await setupAuth("anthropic", process.env.ANTHROPIC_API_KEY)`,

  configBased: `// Authentication from configuration file
import { createOpencode } from "@opencode-ai/sdk"
import { readFileSync } from 'fs'

const { client } = await createOpencode()

// Read auth config from JSON file
const authConfig = JSON.parse(readFileSync('./auth-config.json'))

for (const [providerId, config] of Object.entries(authConfig.providers)) {
  if (config.apiKey) {
    await client.auth.set({
      path: { id: providerId },
      body: { 
        type: config.type || "api", 
        key: config.apiKey 
      },
    })
    console.log(\`✅ \${providerId} authentication configured\`)
  }
}`,

  envBased: `// Environment-based authentication setup
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const authEnvVars = {
  "anthropic": "ANTHROPIC_API_KEY",
  "openai": "OPENAI_API_KEY", 
  "google": "GOOGLE_API_KEY",
  "azure": "AZURE_API_KEY",
  "cohere": "COHERE_API_KEY"
}

let configuredCount = 0

for (const [providerId, envVar] of Object.entries(authEnvVars)) {
  const apiKey = process.env[envVar]
  
  if (apiKey) {
    await client.auth.set({
      path: { id: providerId },
      body: { 
        type: "api", 
        key: apiKey 
      },
    })
    console.log(\`✅ \${providerId} authentication configured from \${envVar}\`)
    configuredCount++
  }
}

console.log(\`🎯 Configured \${configuredCount} providers\`)
`
}

function generateAuthCode(pattern = 'anthropic', options = {}) {
  const template = authPatterns[pattern]
  if (!template) {
    throw new Error(`Unknown pattern: ${pattern}. Available: ${Object.keys(authPatterns).join(', ')}`)
  }

  let code = template
  
  if (options.providerId) {
    code = code.replace(/anthropic/g, options.providerId)
  }
  if (options.envVar) {
    code = code.replace(/ANTHROPIC_API_KEY/g, options.envVar)
  }

  return code
}

function main() {
  const args = process.argv.slice(2)
  const pattern = args[0] || 'anthropic'
  
  try {
    const code = generateAuthCode(pattern)
    
    if (args.includes('--save')) {
      const filename = \`auth-\${pattern}.js\`
      fs.writeFileSync(filename, code)
      console.log(\`✅ Generated \${filename}\`)
    } else {
      console.log(code)
    }
  } catch (error) {
    console.error('❌ Error:', error.message)
    process.exit(1)
  }
}

if (import.meta.url === \`file://\${process.argv[1]}\`) {
  main()
}

export { generateAuthCode, authPatterns }