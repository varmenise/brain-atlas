# BrainAtlas 🧠🗺️

An AI-powered technical interviewer and cognitive aid that creates a persistent, interactive knowledge graph of your weak areas. Built for the Kaggle "AI Agents: Intensive Vibe Coding Capstone" (Agents for Good Track).

## Features

- **Multi-Agent Architecture**: Uses the Google Agent Development Kit (ADK) to coordinate an Interviewer Agent, a silent Evaluator Agent, and a Knowledge Mapper.
- **MCP Server Knowledge Base**: Uses a FastMCP server as the ground-truth for questions, rubrics, and curated study resources, eliminating LLM hallucination.
- **Persistent Knowledge Graph**: Gaps identified during the interview are plotted on a Cytoscape.js interactive graph, scaling in size based on your historical struggles.
- **Dual UI Demonstration**:
  - **ADK Trace Visualizer** (`/`): View the internal tool calls, multi-agent orchestration, and thought processes of the agents in real time.
  - **BrainAtlas Graph Interface** (`/atlas`): View the end-user chat interface and the interactive Cytoscape knowledge graph with sliding study resource drawers.

## Reproduction Steps (Local)

1. **Clone and Install**
   ```bash
   git clone https://github.com/your-username/brain-atlas-antigravity.git
   cd brain-atlas-antigravity
   uv sync
   ```

2. **Environment Setup**
   Create a `.env` file in the root directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   ```

3. **Run the Application**
   ```bash
   agents-cli playground
   ```
   *(Alternatively, run `uv run uvicorn app.fast_api_app:app --host 0.0.0.0 --port 8080`)*

4. **Experience the Application**
   - Open [http://localhost:8080/](http://localhost:8080/) to watch the agents communicate in the ADK Agent Playground.
   - Open [http://localhost:8080/atlas](http://localhost:8080/atlas) to take the interview and see your Knowledge Graph grow!

## Architecture

```
User (role + experience level)
        │
   Orchestrator (Antigravity / ADK)
   ┌────┴──────────────────────┐
   │                           │
Interviewer Agent        Evaluator Agent   ← runs after every answer, silently
   │                           │
   └──────────┬────────────────┘
              │
     Knowledge Mapper Agent   ← runs once at session end
              │
     Graph JSON + Study Plan
```

## Security & "Agents for Good"

BrainAtlas acts as a patient, endlessly available cognitive sparring partner for those who struggle with high-pressure context retrieval (e.g., neurodivergent individuals, those with anxiety). By turning abstract memory blanks into a concrete, interactive roadmap, it empowers users to strengthen their mental models. Security features include sanitization of all LLM inputs against injection, and server-side-only storage of API keys and session data.
