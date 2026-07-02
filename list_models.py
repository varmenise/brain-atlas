import os
from google import genai
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"), vertexai=False)
for m in client.models.list():
    if "flash" in m.name:
        print(m.name)
