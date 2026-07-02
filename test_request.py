import requests

session_data = {"state": {"preferred_language": "English", "visit_count": 1}}
res = requests.post("http://localhost:8000/apps/app/users/user1/sessions", json=session_data)
session_id = res.json()["id"]

data = {
  "app_name": "app",
  "user_id": "user1",
  "session_id": session_id,
  "new_message": {
    "role": "user",
    "parts": [{"text": "Hello! Let's start the interview."}]
  },
  "streaming": False
}
print("Sending request...")
response = requests.post("http://localhost:8000/run", json=data)
print("Response:", response.status_code)
print(response.json())
