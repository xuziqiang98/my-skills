#!/usr/bin/env node

import fs from 'fs'

const eventPatterns = {
  basicListener: `// Basic event listener
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const events = await client.event.subscribe()

console.log("🎧 Listening for events...")

for await (const event of events.stream) {
  console.log("Event:", event.type, event.properties)
  
  // Handle specific event types
  switch (event.type) {
    case "session.created":
      console.log("🆕 New session created")
      break
    case "message.added":
      console.log("💬 New message added")
      break
    case "file.changed":
      console.log("📁 File modified")
      break
  }
}`,

  filteredListener: `// Filtered event listener
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const events = await client.event.subscribe()

const eventFilters = [
  "session.created",
  "session.deleted", 
  "message.added",
  "file.changed"
]

console.log("🎧 Listening for filtered events...")

for await (const event of events.stream) {
  if (eventFilters.includes(event.type)) {
    console.log(\`🔔 \${event.type}:\`, event.properties)
  }
}`,

  withHandlers: `// Event listener with custom handlers
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const eventHandlers = {
  "session.created": (properties) => {
    console.log(\`🆕 Session created: \${properties.id}\`)
    // Send welcome message
    client.session.prompt({
      path: { id: properties.id },
      body: {
        noReply: true,
        parts: [{ type: "text", text: "Welcome! How can I help you today?" }]
      }
    })
  },
  
  "message.added": (properties) => {
    console.log(\`💬 Message in session \${properties.sessionId}\`)
  },
  
  "file.changed": (properties) => {
    console.log(\`📁 File modified: \${properties.path}\`)
  }
}

const events = await client.event.subscribe()

console.log("🎧 Listening with custom handlers...")

for await (const event of events.stream) {
  const handler = eventHandlers[event.type]
  if (handler) {
    handler(event.properties)
  } else {
    console.log("ℹ️ Unhandled event:", event.type)
  }
}`,

  persistentListener: `// Persistent event listener with reconnection
import { createOpencode } from "@opencode-ai/sdk"

async function startEventListener() {
  while (true) {
    try {
      const { client } = await createOpencode()
      const events = await client.event.subscribe()

      console.log("🎧 Event listener connected")

      for await (const event of events.stream) {
        console.log(\`[\${new Date().toISOString()}] \${event.type}:\`, event.properties)
      }

    } catch (error) {
      console.error("❌ Event listener error:", error.message)
      console.log("🔄 Reconnecting in 5 seconds...")
      await new Promise(resolve => setTimeout(resolve, 5000))
    }
  }
}

startEventListener().catch(console.error)`,

  analyticsListener: `// Event analytics listener
import { createOpencode } from "@opencode-ai/sdk"

const { client } = await createOpencode()

const analytics = {
  sessions: 0,
  messages: 0,
  files: 0,
  startTime: Date.now()
}

const events = await client.event.subscribe()

console.log("📊 Analytics listener started")

for await (const event of events.stream) {
  switch (event.type) {
    case "session.created":
      analytics.sessions++
      break
    case "message.added":
      analytics.messages++
      break
    case "file.changed":
      analytics.files++
      break
  }

  // Report stats every 10 events
  if ((analytics.sessions + analytics.messages + analytics.files) % 10 === 0) {
    const duration = Date.now() - analytics.startTime
    console.log(\`📊 Stats: \${analytics.sessions} sessions, \${analytics.messages} messages, \${analytics.files} files in \${duration}ms\`)
  }
}`
}

function generateEventCode(pattern = 'basicListener', options = {}) {
  const template = eventPatterns[pattern]
  if (!template) {
    throw new Error(`Unknown pattern: ${pattern}. Available: ${Object.keys(eventPatterns).join(', ')}`)
  }

  let code = template
  
  if (options.filters) {
    const filters = options.filters.map(f => \`"\${f}"\`).join(", ")
    code = code.replace('const eventFilters = [', \`const eventFilters = [\${filters}\`)
  }

  return code
}

function main() {
  const args = process.argv.slice(2)
  const pattern = args[0] || 'basicListener'
  
  try {
    const code = generateEventCode(pattern)
    
    if (args.includes('--save')) {
      const filename = \`events-\${pattern}.js\`
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

export { generateEventCode, eventPatterns }