from dotenv import load_dotenv

load_dotenv()
import os
import json
import requests

OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL_NAME = "meta-llama/llama-3.2-3b-instruct:free"


def openrouter_chat(prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an academic assistant."},
            {"role": "user", "content": prompt},
        ],
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
    }
    try:
        res = requests.post(
            f"{OPENROUTER_BASE}/chat/completions", json=payload, headers=headers
        )
        res.raise_for_status()
        data = res.json()
        # Defensive: check structure
        if "choices" in data and data["choices"] and "message" in data["choices"][0]:
            return data["choices"][0]["message"]["content"]
        else:
            raise ValueError(f"Unexpected OpenRouter response: {data}")
    except Exception as e:
        print(f"OpenRouter API error: {e}")
        return "{}"


def check_answers_with_ai(input_json, output_filename="checked_answers.json"):
    answers = input_json["answers"]
    prompt = (
        "You are an academic assistant. For each user answer, check if it is correct. "
        "Return a JSON array with objects containing: id, question, userAnswer, user_id, quiz_id, result (correct/wrong), and realAnswer (the correct answer). "
        "If the answer is partially correct, mark as 'wrong' and provide the correct answer. "
        "Output ONLY valid JSON. Do NOT include any text, comments, or code block markers.\n\n"
        "Input format:\n"
        "{\n  'answers': [\n    { 'id': '...', 'question': '...', 'user_answer': '...', 'user_id': '...', 'quiz_id': '...' }, ... ]\n}\n\n"
        "Output format:\n"
        "[\n  { 'id': '...', 'question': '...', 'userAnswer': '...', 'user_id': '...', 'quiz_id': '...', 'result': 'correct', 'realAnswer': '...' }, ... ]\n]"
    )
    # Build question list for prompt
    for a in answers:
        prompt += f"\nID: {a.get('id', '')}\nQuestion: {a.get('question', '')}\nUser Answer: {a.get('user_answer', '')}\nUser ID: {a.get('user_id', '')}\nQuiz ID: {a.get('quiz_id', '')}"
    print(f"Sending {len(answers)} answers to AI for checking...")
    response = openrouter_chat(prompt)
    print("Raw AI response:")
    print(response)
    # Clean and parse response
    cleaned = response.replace("```json", "").replace("```", "").strip()
    print("Cleaned AI response:")
    print(cleaned)
    import re

    match = re.search(r"\[.*\]", cleaned, re.DOTALL)
    json_str = match.group(0) if match else cleaned
    json_str = json_str.replace("'", '"')
    json_str = (
        json_str.replace("“", '"').replace("”", '"').replace("‘", '"').replace("’", '"')
    )
    json_str = re.sub(r",\s*([}\]])", r"\1", json_str)  # Remove trailing commas
    print("JSON string to be parsed:")
    print(json_str)
    try:
        result = json.loads(json_str)
        # Post-process to ensure result is 'correct' or 'wrong'
        for item in result:
            res = str(item.get("result", "")).strip().lower()
            # Treat empty, unknown, incorrect, invalid, or anything not 'correct' as 'wrong'
            if res == "correct":
                item["result"] = "correct"
            else:
                item["result"] = "wrong"
        with open(output_filename, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print("Checked answers saved to:", output_filename)
        return result
    except Exception as e:
        print("Failed to parse AI response:", e)
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(cleaned)
        print(f"Raw AI response saved to: {output_filename}")
        return None


# Example usage:
if __name__ == "__main__":
    # Load answers from a file or dict
    with open("user_answers.json", "r", encoding="utf-8") as f:
        input_json = json.load(f)
    check_answers_with_ai(input_json)
