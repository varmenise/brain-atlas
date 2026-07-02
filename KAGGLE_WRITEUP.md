# BrainAtlas: An Adaptive Multi-Agent System for Personalized Technical Education
**Advancing education through real-time knowledge gap analysis and interactive curriculum mapping**

**Track:** Agents for Good

## 1. Introduction and Vision
In the modern landscape of technical education, 1-on-1 tutoring and mock interviewing remain the gold standard for learning. However, human expert time is scarce, expensive, and inaccessible to the vast majority of learners globally. 

**BrainAtlas** is a multi-agent educational platform designed to democratize access to high-quality, personalized technical mentorship. By leveraging the Google Agent Development Kit (ADK) and Gemini models, BrainAtlas simulates a real technical interview environment. Instead of just giving a pass/fail grade, the system intelligently extracts specific "knowledge gaps" from the user's answers and dynamically generates a personalized, interactive knowledge graph (using Cytoscape.js). This graph maps out exactly what the user needs to study, accompanied by targeted learning resources.

This submission directly targets the **Agents for Good** track by advancing education—providing scalable, accessible, and highly targeted technical tutoring for individuals preparing for careers in software engineering and system design.

## 2. Multi-Agent Architecture

BrainAtlas relies on a collaborative multi-agent architecture to separate concerns, reduce hallucination, and ensure strict, rubric-based grading. The system is built using the **Google Agent Development Kit (ADK)** and consists of three core components:

### A. The Interviewer Agent (The Orchestrator)
Powered by `gemini-3.5-flash`, the Interviewer Agent drives the conversation. 
- It fetches questions from a curated bank via a Model Context Protocol (MCP) server.
- It asks the user a question and waits for their response.
- Behind the scenes, it delegates the user's answer to the Evaluator Agent.
- If the Evaluator Agent returns a score below a passing threshold (5/10), the Interviewer Agent dynamically generates a targeted drill-down question to probe the specific concepts the user missed, adapting the interview organically just like a human would.

### B. The Evaluator Agent (The Grader)
The Evaluator is a specialized "Task" agent designed purely for objective assessment. 
- It takes the user's answer and compares it against a strict rubric (fetched via MCP).
- It returns structured JSON containing dimensional scores, a justification, and a definitive list of `missed_concepts` (knowledge gaps). 
- By separating the Evaluator from the Interviewer, BrainAtlas prevents the "sympathetic interviewer" bias where an LLM might overly praise a poor answer.

### C. The Knowledge Mapper & MCP Server
Instead of an LLM hallucinating study materials, BrainAtlas uses a deterministic pipeline and an MCP Server to handle domain knowledge:
- The MCP server acts as the source of truth, providing the question bank, evaluation rubrics, and curated study resources.
- At the end of the session, the aggregated knowledge gaps are persisted to a database.
- A deterministic Knowledge Mapper reads this database, calculates the frequency and co-occurrence of missed concepts across multiple sessions, and compiles this into a Cytoscape.js compatible JSON structure.

## 3. Technical Implementation

- **Framework**: Google Agent Development Kit (ADK) 0.5.
- **Frontend**: Vanilla Javascript and HTML, utilizing **Cytoscape.js** for rendering the interactive knowledge graph. Dark mode, glassmorphism, and dynamic animations provide a premium, engaging user experience.
- **Backend**: FastAPI. The monolithic backend natively hosts the ADK `/run` streaming endpoints, manages the session state, and mounts the static frontend.
- **Tooling**: Heavy utilization of ADK's `ToolContext` for native session injection and background database persistence without exposing internal IDs to the LLM. 
- **Models**: Built to run efficiently on `gemini-3.5-flash` and `gemini-2.0-flash-lite`, optimizing for low latency (crucial for a conversational interview format) and low cost.

## 4. Evaluation and Quality Assurance

To ensure the agents behave correctly, BrainAtlas utilizes the ADK's Trajectory Evaluation framework. We synthesized a multi-turn evaluation dataset (`tests/eval/datasets/delegation.json`) that tests the system's ability to:
1. Ask a question.
2. Gracefully handle a poor answer.
3. Automatically trigger a drill-down follow-up question.
4. Correctly identify the missing concepts.

By employing LLM-as-a-judge methodologies during development, we iteratively refined the system prompts to prevent the Interviewer Agent from revealing scores to the user or breaking character.

## 5. Impact & "Agents for Good"

Education is the ultimate equalizer, but the gap between theoretical knowledge and practical interview readiness keeps many talented individuals out of the tech industry. BrainAtlas solves this by creating a highly patient, endlessly available technical mentor. 

Unlike standard chatbots that simply converse, BrainAtlas creates a **persistent knowledge artifact** (the Atlas). Over time, as the user completes more mock interviews, the graph grows. Nodes become larger based on the frequency of the mistakes, visually highlighting the user's weakest areas. Clicking a node opens a drawer with highly curated, MCP-provided study resources tailored to that specific gap.

By turning abstract failures into a concrete, interactive study roadmap, BrainAtlas empowers users to learn efficiently and enter the workforce with confidence.

## 6. Future Improvements

- **Real-Time Graph Updates**: Transitioning the append-only JSON database to support upserts, allowing the frontend graph to animate and update in real-time as the user answers questions, rather than waiting for the session to conclude.
- **Expanded Domains**: Currently focused on System Design and Software Engineering, the MCP server can easily be expanded to support medical exams, bar exams, and language learning.
- **Voice Integration**: Leveraging Gemini's multimodal capabilities to conduct the interview entirely over voice for a more authentic testing environment.
