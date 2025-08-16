import os
import json
import requests
from PyPDF2 import PdfReader

# --------------------------
# CONFIGURATION
# --------------------------
COURSE_FOLDER = "past_papers/csse2310"
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
        if file.endswith(".pdf"):
            path = os.path.join(folder, file)
            reader = PdfReader(path)
            text = ""
            for i, page in enumerate(reader.pages):
                if i == 0:  # skip first page
                    continue
                text += page.extract_text() + "\n"
            papers.append(text)
    return papers

def split_into_questions(text):
    questions = []
    lines = text.splitlines()
    current_question = []
    for line in lines:
        if line.strip().upper().startswith("QUESTION"):
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
# MAIN
# --------------------------
if __name__ == "__main__":
    print("Reading past papers...")
    papers = read_past_paper_files(COURSE_FOLDER)
    
    if not papers:
        raise FileNotFoundError(f"No PDF files found in {COURSE_FOLDER}")
    
    first_paper = papers[0]
    questions = split_into_questions(first_paper)
    
    # Build prompt for analysis + mock generation
    prompt = (
        "You are an academic assistant. Your job has two parts:\n"
        "IGNORE any pages that do not contain actual exam questions "
        "(for example, title page, instructions, or venue info). Only include real questions in the 'questions' output."
        "1. For each original question, create an entry with:\n"
        "   - 'question_text': include ALL content exactly as in the original question, "
        "including instructions, paragraphs, and code.\n"
        "   - 'topic': main subject area of the question.\n"
        "   - 'question_type': 'multiple_choice', 'short_answer', 'essay', or 'calculation'.\n"
        "   - DO NOT include 'options' or 'correct_answer' for original questions.\n"
        "   - If the question is unrelated to the main subject, IGNORE it completely.\n"
        "2. Generate a mock exam of about "
        f"{NUM_MOCK_QUESTIONS} questions:\n"
        "   - Keep the same question type as the originals.\n"
        "   - Include code, paragraphs, or instructions as appropriate.\n"
        "   - For multiple choice, generate 4 options labeled A–D, with one correct answer.\n"
        "   - Maintain similar style and difficulty.\n"
        "IMPORTANT: Output STRICTLY valid JSON, nothing outside the JSON object.\n"
        "JSON structure:\n"
        "{\n"
        '  "questions": [\n'
        '    {"question_text": "...", "topic": "...", "question_type": "..."},\n'
        "    ...\n"
        "  ],\n"
        '  "mock_exam": [\n'
        '    {"question_text": "...", "topic": "...", "question_type": "...", '
        '"options": ["A) ...", "B) ...", "C) ...", "D) ..."], "correct_answer": "B"},\n'
        "    ...\n"
        "  ]\n"
        "}\n\n"
        "Here are the original questions:\n"
    )

    for idx, q in enumerate(questions, 1):
        prompt += f"\n--- QUESTION {idx} START ---\n{q}\n--- QUESTION {idx} END ---\n"


    print(f"Sending API request for {len(questions)} questions...")
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
