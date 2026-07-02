import asyncio
from app.interviewer.agent import interviewer_agent
import json

async def main():
    print("Sending message to interviewer_agent...")
    events = []
    
    # We will simulate the exact same message the frontend sends
    async for event in interviewer_agent.run_async("Ready to start the interview for system design"):
        print("\n--- NEW EVENT ---")
        # Try to print as dict if possible
        if hasattr(event, "model_dump"):
            print(json.dumps(event.model_dump(), indent=2))
        else:
            print(event)

if __name__ == "__main__":
    asyncio.run(main())
