// App State
const state = {
  sessionId: crypto.randomUUID(),
  isTyping: false
};

// DOM Elements
const chatHistory = document.getElementById('chat-history');
const chatForm = document.getElementById('chat-form');
const chatInput = document.getElementById('chat-input');
const refreshBtn = document.getElementById('refresh-map-btn');

// Cytoscape Instance
let cy;

function initCytoscape() {
  cy = cytoscape({
    container: document.getElementById('cy'),
    elements: [],
    style: [
      {
        selector: 'node',
        style: {
          'background-color': '#1e2028',
          'border-width': 2,
          'border-color': '#6366f1',
          'label': 'data(label)',
          'color': '#f0f2f5',
          'font-family': 'Inter',
          'font-size': '12px',
          'text-valign': 'center',
          'text-halign': 'center',
          'width': 'mapData(size, 1, 10, 40, 100)',
          'height': 'mapData(size, 1, 10, 40, 100)',
          'text-wrap': 'wrap',
          'text-max-width': '80px'
        }
      },
      {
        selector: 'edge',
        style: {
          'width': 'mapData(weight, 1, 10, 1, 5)',
          'line-color': 'rgba(99, 102, 241, 0.4)',
          'curve-style': 'bezier'
        }
      }
    ],
    layout: {
      name: 'cose',
      padding: 50,
      nodeRepulsion: 400000,
      idealEdgeLength: 100,
      edgeElasticity: 100,
      gravity: 250,
      numIter: 1000
    }
  });
}

function appendMessage(role, text) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message ${role}-message`;
  
  const bubble = document.createElement('div');
  bubble.className = 'bubble';
  
  // Basic markdown-like formatting (bolding)
  let formattedText = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  formattedText = formattedText.replace(/\n/g, '<br>');
  
  bubble.innerHTML = role === 'ai' ? `<strong>Interviewer:</strong><br>${formattedText}` : formattedText;
  
  msgDiv.appendChild(bubble);
  chatHistory.appendChild(msgDiv);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function showTypingIndicator() {
  const msgDiv = document.createElement('div');
  msgDiv.className = 'message ai-message';
  msgDiv.id = 'typing-indicator';
  
  const bubble = document.createElement('div');
  bubble.className = 'bubble typing-indicator';
  bubble.innerHTML = '<div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div>';
  
  msgDiv.appendChild(bubble);
  chatHistory.appendChild(msgDiv);
  chatHistory.scrollTop = chatHistory.scrollHeight;
}

function removeTypingIndicator() {
  const indicator = document.getElementById('typing-indicator');
  if (indicator) indicator.remove();
}

async function sendMessage(text) {
  if (!text.trim() || state.isTyping) return;
  
  appendMessage('user', text);
  chatInput.value = '';
  
  state.isTyping = true;
  showTypingIndicator();
  
  try {
    const payload = {
      app_name: "app",
      user_id: "web_user",
      userId: "mock_user",
      session_id: state.sessionId,
      new_message: {
        role: "user",
        parts: [{ text: text }]
      },
      streaming: false
    };

    const response = await fetch('/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    
    const data = await response.json();
    removeTypingIndicator();
    
    if (data.error) {
      appendMessage('system', 'Error: ' + data.error);
    } else if (data.detail) {
      // FastAPI validation error
      appendMessage('system', 'API Error: ' + JSON.stringify(data.detail));
    } else {
      let reply = "No text returned.";
      let allText = [];
      
      // If data is an array, loop through it to find the text parts
      const events = Array.isArray(data) ? data : [data];
      
      for (const event of events) {
        if (event.content && event.content.parts) {
          for (const part of event.content.parts) {
            if (part.text) {
              allText.push(part.text);
            }
          }
        }
      }
      
      if (allText.length > 0) {
        reply = allText.join('\n\n');
      }
      
      appendMessage('ai', reply);
      
      // Auto-refresh map if the agent mentioned a summary or gaps
      if (reply.toLowerCase().includes('summary') || reply.toLowerCase().includes('gap')) {
        refreshGraph();
      }
    }
  } catch (err) {
    removeTypingIndicator();
    appendMessage('system', 'Connection failed: ' + err.message);
  } finally {
    state.isTyping = false;
  }
}

async function refreshGraph() {
  try {
    const response = await fetch(`/api/graph/${state.sessionId}`);
    if (!response.ok) throw new Error('Graph not found or no gaps recorded yet.');
    const data = await response.json();
    
    cy.elements().remove();
    if (data.nodes && data.nodes.length > 0) {
      cy.add(data);
      cy.layout({
        name: 'cose',
        padding: 50,
        nodeRepulsion: 400000,
        idealEdgeLength: 100,
        edgeElasticity: 100,
        gravity: 250,
        numIter: 1000
      }).run();
    }
  } catch (err) {
    console.warn("Graph refresh failed:", err);
  }
}

// Event Listeners
chatForm.addEventListener('submit', (e) => {
  e.preventDefault();
  sendMessage(chatInput.value);
});

refreshBtn.addEventListener('click', refreshGraph);

// Startup
document.addEventListener('DOMContentLoaded', () => {
  initCytoscape();
});
