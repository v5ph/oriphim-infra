import React, { useState, useEffect } from 'react';
import type { IntegrationPattern } from './PatternSelector';
import type { ProgrammingLanguage } from './LanguageSelector';

interface CodeGeneratorProps {
  pattern: IntegrationPattern;
  language: ProgrammingLanguage;
  apiKey?: string;
}

export const CodeGenerator: React.FC<CodeGeneratorProps> = ({ pattern, language, apiKey = 'YOUR_API_KEY_HERE' }) => {
  const [code, setCode] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    setCode(generateCode(pattern, language, apiKey));
  }, [pattern, language, apiKey]);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy code:', err);
    }
  };

  return (
    <div className="card">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-bold text-carbon-black">Generated Code</h3>
        <button
          onClick={handleCopy}
          className="btn-secondary px-4 py-2 rounded font-medium text-sm"
        >
          {copied ? 'Copied!' : 'Copy Code'}
        </button>
      </div>

      <div className="bg-carbon-black rounded-lg p-4 overflow-x-auto">
        <pre className="text-sm text-floral-white font-mono">
          <code>{code}</code>
        </pre>
      </div>

      <div className="mt-4 text-sm text-charcoal-brown">
        <p className="font-medium mb-2">Integration Notes:</p>
        <ul className="list-disc list-inside space-y-1">
          {pattern === 'sync' && (
            <>
              <li>Validation runs synchronously and blocks until complete</li>
              <li>Response includes full validation results immediately</li>
              <li>Best for real-time decision workflows</li>
            </>
          )}
          {pattern === 'async' && (
            <>
              <li>POST request returns immediately with request_id</li>
              <li>Poll GET endpoint with request_id to retrieve results</li>
              <li>Recommended polling interval: 500ms</li>
            </>
          )}
          {pattern === 'webhook' && (
            <>
              <li>Provide callback URL in request headers</li>
              <li>Server POSTs validation results to your callback URL</li>
              <li>Ensure webhook endpoint accepts POST requests</li>
            </>
          )}
        </ul>
      </div>
    </div>
  );
};

function generateCode(
  pattern: IntegrationPattern,
  language: ProgrammingLanguage,
  apiKey: string
): string {
  const templates: Record<IntegrationPattern, Record<ProgrammingLanguage, string>> = {
    sync: {
      python: `import requests

API_KEY = "${apiKey}"
BASE_URL = "http://localhost:8000"

def validate_sync(agent_id: str, user_prompt: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "agent_id": agent_id,
        "user_prompt": user_prompt,
        "context": {},
        "variables": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/v3/intent",
        json=payload,
        headers=headers
    )
    
    response.raise_for_status()
    return response.json()

# Example usage
result = validate_sync("agent-123", "Transfer $1000 to external account")
print(f"Action: {result['action_label']}")
print(f"Violations: {result['violations']}")
print(f"Confidence: {result['confidence']['score']}")`,

      typescript: `import axios from 'axios';

const API_KEY = '${apiKey}';
const BASE_URL = 'http://localhost:8000';

interface ValidationRequest {
  agent_id: string;
  user_prompt: string;
  context?: Record<string, any>;
  variables?: Record<string, any>;
}

async function validateSync(request: ValidationRequest) {
  const response = await axios.post(
    \`\${BASE_URL}/v3/intent\`,
    request,
    {
      headers: {
        'Authorization': \`Bearer \${API_KEY}\`,
        'Content-Type': 'application/json',
      },
    }
  );
  
  return response.data;
}

// Example usage
const result = await validateSync({
  agent_id: 'agent-123',
  user_prompt: 'Transfer $1000 to external account',
});

console.log('Action:', result.action_label);
console.log('Violations:', result.violations);
console.log('Confidence:', result.confidence.score);`,

      curl: `#!/bin/bash

API_KEY="${apiKey}"
BASE_URL="http://localhost:8000"

curl -X POST "\${BASE_URL}/v3/intent" \\
  -H "Authorization: Bearer \${API_KEY}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "agent_id": "agent-123",
    "user_prompt": "Transfer $1000 to external account",
    "context": {},
    "variables": {}
  }' | jq '{
    action: .action_label,
    violations: .violations,
    confidence: .confidence.score
  }'`,
    },

    async: {
      python: `import requests
import time

API_KEY = "${apiKey}"
BASE_URL = "http://localhost:8000"

def validate_async(agent_id: str, user_prompt: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Submit validation request
    payload = {
        "agent_id": agent_id,
        "user_prompt": user_prompt,
        "context": {},
        "variables": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/v3/intent",
        json=payload,
        headers=headers
    )
    response.raise_for_status()
    request_id = response.json()["request_id"]
    
    # Poll for results
    while True:
        poll_response = requests.get(
            f"{BASE_URL}/v3/intent/{request_id}",
            headers=headers
        )
        
        if poll_response.status_code == 200:
            return poll_response.json()
        elif poll_response.status_code == 202:
            time.sleep(0.5)  # Wait 500ms before retry
            continue
        else:
            poll_response.raise_for_status()

# Example usage
result = validate_async("agent-123", "Transfer $1000 to external account")
print(f"Action: {result['action_label']}")
print(f"Violations: {result['violations']}")`,

      typescript: `import axios from 'axios';

const API_KEY = '${apiKey}';
const BASE_URL = 'http://localhost:8000';

async function validateAsync(
  agentId: string,
  userPrompt: string
): Promise<any> {
  const headers = {
    'Authorization': \`Bearer \${API_KEY}\`,
    'Content-Type': 'application/json',
  };

  // Submit validation request
  const submitResponse = await axios.post(
    \`\${BASE_URL}/v3/intent\`,
    { agent_id: agentId, user_prompt: userPrompt },
    { headers }
  );

  const requestId = submitResponse.data.request_id;

  // Poll for results
  while (true) {
    const pollResponse = await axios.get(
      \`\${BASE_URL}/v3/intent/\${requestId}\`,
      { headers, validateStatus: (status) => status === 200 || status === 202 }
    );

    if (pollResponse.status === 200) {
      return pollResponse.data;
    }

    // Wait 500ms before retry
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

// Example usage
const result = await validateAsync(
  'agent-123',
  'Transfer $1000 to external account'
);
console.log('Action:', result.action_label);`,

      curl: `#!/bin/bash

API_KEY="${apiKey}"
BASE_URL="http://localhost:8000"

# Submit validation request
RESPONSE=$(curl -X POST "\${BASE_URL}/v3/intent" \\
  -H "Authorization: Bearer \${API_KEY}" \\
  -H "Content-Type: application/json" \\
  -d '{
    "agent_id": "agent-123",
    "user_prompt": "Transfer $1000 to external account"
  }')

REQUEST_ID=$(echo "$RESPONSE" | jq -r '.request_id')

# Poll for results
while true; do
  RESULT=$(curl -s -w "\\n%{http_code}" \\
    -H "Authorization: Bearer \${API_KEY}" \\
    "\${BASE_URL}/v3/intent/\${REQUEST_ID}")
  
  HTTP_CODE=$(echo "$RESULT" | tail -n1)
  BODY=$(echo "$RESULT" | sed '$d')
  
  if [ "$HTTP_CODE" = "200" ]; then
    echo "$BODY" | jq '.action_label, .violations'
    break
  fi
  
  sleep 0.5
done`,
    },

    webhook: {
      python: `import requests

API_KEY = "${apiKey}"
BASE_URL = "http://localhost:8000"
WEBHOOK_URL = "https://your-domain.com/webhook/validation"

def validate_webhook(agent_id: str, user_prompt: str):
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "X-Webhook-Callback": WEBHOOK_URL
    }
    
    payload = {
        "agent_id": agent_id,
        "user_prompt": user_prompt,
        "context": {},
        "variables": {}
    }
    
    response = requests.post(
        f"{BASE_URL}/v3/intent",
        json=payload,
        headers=headers
    )
    
    response.raise_for_status()
    return response.json()["request_id"]

# Example webhook handler (Flask)
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/webhook/validation', methods=['POST'])
def handle_validation_callback():
    result = request.json
    print(f"Received validation: {result['action_label']}")
    print(f"Violations: {result['violations']}")
    return jsonify({"status": "received"}), 200

# Submit validation
request_id = validate_webhook("agent-123", "Transfer $1000")
print(f"Request ID: {request_id}")`,

      typescript: `import axios from 'axios';
import express from 'express';

const API_KEY = '${apiKey}';
const BASE_URL = 'http://localhost:8000';
const WEBHOOK_URL = 'https://your-domain.com/webhook/validation';

async function validateWebhook(
  agentId: string,
  userPrompt: string
): Promise<string> {
  const response = await axios.post(
    \`\${BASE_URL}/v3/intent\`,
    { agent_id: agentId, user_prompt: userPrompt },
    {
      headers: {
        'Authorization': \`Bearer \${API_KEY}\`,
        'Content-Type': 'application/json',
        'X-Webhook-Callback': WEBHOOK_URL,
      },
    }
  );

  return response.data.request_id;
}

// Example webhook handler (Express)
const app = express();
app.use(express.json());

app.post('/webhook/validation', (req, res) => {
  const result = req.body;
  console.log('Received validation:', result.action_label);
  console.log('Violations:', result.violations);
  res.json({ status: 'received' });
});

app.listen(3000, () => {
  console.log('Webhook server listening on port 3000');
});

// Submit validation
const requestId = await validateWebhook(
  'agent-123',
  'Transfer $1000 to external account'
);
console.log('Request ID:', requestId);`,

      curl: `#!/bin/bash

API_KEY="${apiKey}"
BASE_URL="http://localhost:8000"
WEBHOOK_URL="https://your-domain.com/webhook/validation"

# Submit validation with webhook callback
curl -X POST "\${BASE_URL}/v3/intent" \\
  -H "Authorization: Bearer \${API_KEY}" \\
  -H "Content-Type: application/json" \\
  -H "X-Webhook-Callback: \${WEBHOOK_URL}" \\
  -d '{
    "agent_id": "agent-123",
    "user_prompt": "Transfer $1000 to external account",
    "context": {},
    "variables": {}
  }' | jq '.request_id'

# Note: Results will be POSTed to your webhook URL
# Example webhook handler:
# while true; do
#   nc -l 8080 < response.txt
# done`,
    },
  };

  return templates[pattern][language];
}
