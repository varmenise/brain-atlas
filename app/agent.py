from google.adk.apps import App
from app.interviewer.agent import interviewer_agent

# Export the main application entrypoint for the ADK framework.
# This explicitly binds the Interviewer as the root agent for both the agents-cli eval runner and the live FastAPI server.
app = App(
    name="app",
    root_agent=interviewer_agent,
)
