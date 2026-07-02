# BrainAtlas: An Adaptive Multi-Agent Cognitive Mapping System
**A conversational brain aid for context retrieval, concept strengthening, and personalized knowledge mapping under stress**

**Track:** Agents for Good

## 1. Introduction and Vision
Human memory is inherently fallible. For many, context retrieval—especially under high-stress situations like job interviews, university exams, or intense technical environments—can be a debilitating struggle. 

**BrainAtlas** is a multi-agent cognitive aid designed to act as a personalized sparring partner and external memory map. While our prototype uses technical interviewing as a high-stress test case, the system's true purpose is far broader: helping individuals strengthen conceptual understanding, feel sharper in their daily lives, and overcome retrieval anxiety.

By leveraging the Google Agent Development Kit (ADK) and Gemini models, BrainAtlas engages the user in deep conversation. Instead of just giving a pass/fail grade, the system intelligently extracts specific "knowledge gaps" from the user's answers. It then dynamically generates a persistent, interactive cognitive map (using Cytoscape.js) that visualizes exactly where the user's mental model is breaking down, accompanied by targeted resources to rebuild that confidence.

This submission directly targets the **Agents for Good** track by advancing education and cognitive support—providing a scalable, accessible, and highly patient tool to help humanity learn, retain, and recall information when it matters most.

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
- A deterministic Knowledge Mapper reads this database to generate a massive, interconnected **Global Atlas View**. Rather than just showing the results of a single interview, it plots every single concept missed across *all* of the user's historical sessions. It elegantly scales the visual weight (size) of those nodes by aggregating the frequency of failures over time, allowing the user to seamlessly navigate their weakest areas and proactively strengthen their mental models.

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

The ability to recall information under pressure is a critical factor in academic, professional, and personal success. However, neurodivergent individuals, those with anxiety, or anyone simply overwhelmed by the volume of modern information often struggle to bridge the gap between what they know and what they can retrieve on demand. 

BrainAtlas solves this by creating a highly patient, endlessly available cognitive sparring partner. Unlike standard chatbots that simply converse, BrainAtlas creates a **persistent knowledge artifact** (the Atlas). Over time, as the user completes more sessions, the graph grows. Nodes become larger based on the frequency of retrieval failures, visually highlighting the user's weakest links. Clicking a node opens a drawer with highly curated, MCP-provided study resources tailored to that specific gap.

By turning abstract memory blanks into a concrete, interactive roadmap, BrainAtlas empowers users to strengthen their mental models, master complex subjects, and enter high-stress situations with renewed confidence.

## 6. Future Improvements

- **Real-Time Graph Updates**: Transitioning the append-only JSON database to support upserts, allowing the frontend graph to animate and update in real-time as the user answers questions, rather than waiting for the session to conclude.
- **Expanded Domains**: Currently focused on System Design and Software Engineering, the MCP server can easily be expanded to support medical exams, bar exams, and language learning.
- **Voice Integration**: Leveraging Gemini's multimodal capabilities to conduct the interview entirely over voice for a more authentic testing environment.
- **Custom Context API**: Adding an API that allows users to upload their own context (documents, notes, etc.) and tag them as personalized study resources.
- **Session Saving & Replay**: Enabling users to save exceptionally good interview sessions as "model answer" study resources so they can replay and learn from their own past successes.
- **Spaced Repetition & Memory Decay**: Implementing a time-decay algorithm for the knowledge graph where older, unpracticed gaps slowly grow in visual weight to remind the user that their memory of the concept is decaying.
- **Multi-Tenant User Isolation**: Upgrading the local session database to a production-ready system (like Supabase) to partition and filter the Knowledge Graph by `user_id`, ensuring a fully personalized atlas for each individual user.
- **Advanced Graph Filtering**: Adding dashboard UI toggles that allow users to filter their massive Global Atlas by specific domains (e.g., engineering vs. medical), by time periods (e.g., last 30 days vs. all-time), and by gap severity to easily isolate the most critical weak points.
