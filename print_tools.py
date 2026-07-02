import sys
from app.interviewer.agent import interviewer_agent

for tool in interviewer_agent.tools:
    print(tool.name if hasattr(tool, 'name') else tool.__name__)
