import sys
import requests
import json

# Usage: python get_all_answers_to_json.py <user_id> <quiz_id>

if len(sys.argv) != 3:
    print("Usage: python get_all_answers_to_json.py <user_id> <quiz_id>")
    sys.exit(1)

user_id = sys.argv[1]
quiz_id = sys.argv[2]
output_file = "user_answers.json"

url = "http://localhost:8000/api/v1/all/answers"
params = {"user_id": user_id, "quiz_id": quiz_id}

resp = requests.get(url, params=params)
if resp.status_code != 200:
    print(f"Failed to fetch answers: {resp.status_code} {resp.text}")
    sys.exit(1)

answers_json = resp.json()

# Ensure the output format is {"answers": [...]}
if isinstance(answers_json, dict) and "answers" in answers_json:
    output = answers_json
else:
    output = {"answers": answers_json}

# Print the output to terminal
print(json.dumps(output, ensure_ascii=False, indent=2))

# Save the output to user_answers.json
with open("user_answers.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)
print("Saved answers to user_answers.json")
