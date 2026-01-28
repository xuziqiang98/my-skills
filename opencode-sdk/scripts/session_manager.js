#!/usr/bin/env node

import fs from 'fs'

const sessionPatterns = {
  createAndPrompt: `// Create session and send first prompt
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const session = await client.session.create({
  body: { title: "My Session" }
})

console.log("Created session:", session.id)

const response = await client.session.prompt({
  path: { id: session.id },
  body: {
    model: { 
      providerID: "anthropic", 
      modelID: "claude-3-5-sonnet-20241022" 
    },
    parts: [{ type: "text", text: "Hello! Please help me with..." }]
  }
})

console.log("Response:", response.parts[0].text)`,

  listAndManage: `// List sessions and manage existing ones
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const sessions = await client.session.list()
console.log("Available sessions:")

for (const session of sessions.data) {
  console.log(\`- \${session.id}: \${session.title}\`)
}

// Get current session details
if (sessions.data.length > 0) {
  const currentSession = sessions.data[0]
  const details = await client.session.get({
    path: { id: currentSession.id }
  })
  
  console.log("Session details:", details)
}`,

  commandHandling: `// Send commands instead of prompts
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const session = await client.session.create({
  body: { title: "Command Session" }
})

// Send a slash command
const result = await client.session.command({
  path: { id: session.id },
  body: {
    command: "/check-file src/main.js"
  }
})

console.log("Command result:", result)`,

  contextOnly: `// Add context without triggering AI response
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const session = await client.session.create({
  body: { title: "Context-Loaded Session" }
})

// Inject context only (no AI response)
await client.session.prompt({
  path: { id: session.id },
  body: {
    noReply: true,
    parts: [{ 
      type: "text", 
      text: "You are a specialized assistant for React development. Focus on best practices and modern patterns." 
    }]
  }
})

console.log("Context injected successfully")`,

  messageHistory: `// Retrieve and analyze message history
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const sessions = await client.session.list()
const session = sessions.data[0]

if (session) {
  const messages = await client.session.messages({
    path: { id: session.id }
  })
  
  console.log("Message history:")
  for (const message of messages) {
    const role = message.info.role
    const text = message.parts.find(p => p.type === "text")?.text
    console.log(\`[\${role}]: \${text?.substring(0, 100)}...\`)
  }
}`
}

function generateSessionCode(pattern = 'createAndPrompt', options = {}) {
  const template = sessionPatterns[pattern]
  if (!template) {
    throw new Error(`Unknown pattern: ${pattern}. Available: ${Object.keys(sessionPatterns).join(', ')}`)
  }

  let code = template
  
  if (options.sessionTitle) {
    code = code.replace('title: "My Session"', `title: "${options.sessionTitle}"`)
  }
  if (options.promptText) {
    code = code.replace('text: "Hello! Please help me with..."', `text: "${options.promptText}"`)
  }
  if (options.command) {
    code = code.replace('/check-file src/main.js', options.command)
  }
  if (options.contextText) {
    code = code.replace('You are a specialized assistant for React development. Focus on best practices and modern patterns.', options.contextText)
  }

  return code
}

function main() {
  const args = process.argv.slice(2)
  const pattern = args[0] || 'createAndPrompt'
  
  try {
    const code = generateSessionCode(pattern)
    
    if (args.includes('--save')) {
      const filename = \`session-\${pattern}.js\`
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

export { generateSessionCode, sessionPatterns }