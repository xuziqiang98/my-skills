#!/usr/bin/env node

import fs from 'fs'

const clientTemplates = {
  basic: `// Basic OpenCode client setup
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()
console.log("OpenCode client ready")`,

  withConfig: `// OpenCode client with custom configuration
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode({
  hostname: "127.0.0.1",
  port: 4096,
  config: {
    model: "anthropic/claude-3-5-sonnet-20241022",
    // Add your custom config here
  },
})

console.log(\`Server running at \${server.url}\`)
server.close()`,

  clientOnly: `// Connect to existing OpenCode server
import { createOpencodeClient } from "@opencode-ai/sdk"

const client = createOpencodeClient({ 
  baseUrl: "http://localhost:4096",
  // Optional custom fetch implementation
  // fetch: customFetch,
  // responseStyle: "data" // or "fields"
})`,

  withAuth: `// OpenCode client with authentication
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode({
  config: {
    model: "anthropic/claude-3-5-sonnet-20241022",
  },
})

// Set up authentication
await client.auth.set({
  path: { id: "anthropic" },
  body: { 
    type: "api", 
    key: process.env.ANTHROPIC_API_KEY 
  },
})`,

  typescript: `// TypeScript client setup with types
import { createOpencode } from "@opencode-ai/sdk"
import type { Session, Message, Part } from "@opencode-ai/sdk"

const { client } = await createOpencode({
  config: {
    model: "anthropic/claude-3-5-sonnet-20241022",
  },
})

// Example typed usage
const session: Session = await client.session.create({
  body: { title: "Typed session" }
})

const message = await client.session.prompt({
  path: { id: session.id },
  body: {
    model: { providerID: "anthropic", modelID: "claude-3-5-sonnet-20241022" },
    parts: [{ type: "text", text: "Hello!" }] as Part[]
  }
})`
}

function generateClient(type = 'basic', options = {}) {
  const template = clientTemplates[type]
  if (!template) {
    throw new Error(`Unknown client type: ${type}. Available: ${Object.keys(clientTemplates).join(', ')}`)
  }

  let code = template
  
  if (options.hostname) {
    code = code.replace('hostname: "127.0.0.1"', `hostname: "${options.hostname}"`)
  }
  if (options.port) {
    code = code.replace('port: 4096', `port: ${options.port}`)
  }
  if (options.model) {
    code = code.replace('model: "anthropic/claude-3-5-sonnet-20241022"', `model: "${options.model}"`)
  }
  if (options.baseUrl) {
    code = code.replace('baseUrl: "http://localhost:4096"', `baseUrl: "${options.baseUrl}"`)
  }

  return code
}

function main() {
  const args = process.argv.slice(2)
  const type = args[0] || 'basic'
  
  try {
    const code = generateClient(type)
    
    if (args.includes('--save')) {
      const filename = `client-${type}.js`
      fs.writeFileSync(filename, code)
      console.log(`✅ Generated ${filename}`)
    } else {
      console.log(code)
    }
  } catch (error) {
    console.error('❌ Error:', error.message)
    process.exit(1)
  }
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main()
}

export { generateClient, clientTemplates }