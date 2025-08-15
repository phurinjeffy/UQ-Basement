import os
import json
import requests

# --------------------------
# CONFIGURATION
# --------------------------
COURSE_FOLDER = "past_papers/csse2310"
NUM_TEST_QUESTIONS = 5
NUM_MOCK_QUESTIONS = 10
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL_NAME = "meta-llama/llama-3.2-3b-instruct:free"

if not OPENROUTER_KEY:
    raise ValueError("OPENROUTER_KEY environment variable not set.")

# --------------------------
# HELPERS
# --------------------------
def read_past_paper_files(folder):
    papers = []
    for file in os.listdir(folder):
        if file.endswith(".txt"):
            path = os.path.join(folder, file)
            with open(path, "r", encoding="utf-8") as f:
                papers.append(f.read())
    return papers

def split_into_questions(text):
    questions = []
    lines = text.splitlines()
    current_question = []
    for line in lines:
        if line.startswith("QUESTION"):
            if current_question:
                questions.append("\n".join(current_question))
            current_question = [line]
        else:
            current_question.append(line)
    if current_question:
        questions.append("\n".join(current_question))
    return questions

def openrouter_chat(prompt):
    payload = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "You are an academic assistant."},
            {"role": "user", "content": prompt}
        ]
    }
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json"
    }
    res = requests.post(f"{OPENROUTER_BASE}/chat/completions", json=payload, headers=headers)
    res.raise_for_status()
    return res.json()["choices"][0]["message"]["content"]

# --------------------------
# MAIN TEST
# --------------------------
if __name__ == "__main__":
    print("Reading past papers...")
    papers = read_past_paper_files(COURSE_FOLDER)
    
    # Take only first paper for testing
    first_paper = papers[0]
    questions = split_into_questions(first_paper)
    
    # Take only first 5 questions
    test_questions = questions[:NUM_TEST_QUESTIONS]
    
    # Build prompt for analysis + mock generation
    prompt = (
        "You are an academic assistant. Do two things:\n"
        "1. For each question, identify 'topic' and 'question_type'.\n"
        "2. Generate a mock exam of about {NUM_MOCK_QUESTIONS} questions, "
        "where questions are similar to the originals in style and wording. "
        "If a topic appears frequently, include it more often in the mock exam.\n\n"
        "Return a single JSON object like this:\n"
        "{\n"
        "  'questions': [\n"
        "      {'question_text': '...', 'topic': '...', 'question_type': '...'},\n"
        "      ...\n"
        "  ],\n"
        "  'mock_exam': [\n"
        "      'Mock question 1', 'Mock question 2', ...\n"
        "  ]\n"
        "}\n\n"
        "Here are the questions:\n"
    )
    for idx, q in enumerate(test_questions, 1):
        prompt += f"{idx}. {q}\n"

    print(f"Sending API request for {len(test_questions)} questions...")
    response = openrouter_chat(prompt)

    print("AI response:\n")
    print(response)

    # Try to parse JSON
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        result = json.loads(response[start:end].replace("'", '"'))
        output_file = os.path.join(COURSE_FOLDER, "past_paper_analysis_with_mock.json")
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print("Analysis + mock exam saved to:", output_file)
    except Exception as e:
        print("Failed to parse JSON:", e)
