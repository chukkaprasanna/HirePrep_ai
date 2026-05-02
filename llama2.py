import ollama
import json
import re
import psycopg2




MODEL_NAME = "llava-llama3:8b"




def store_in_db(all_data):
    appti = all_data["aptitude"]
    reasoning = all_data["reasoning"]
    verbal = all_data["verbal"]

    apptiquestions = appti["questions"]
    reason_ques = reasoning["questions"]
    verbalques = verbal["questions"]

    apptians = appti["answers"]
    reason_ans = reasoning["answers"]
    verbal_ans = verbal["answers"]







def generate_questions(company, package, role, skills):

    prompt = f"""
You are HirePrep-AI, an elite technical recruitment exam generator.

Candidate Profile:
Skills: {skills}
Target Company: {company}
Desired Package: {package} Lakhs Per Annum
Target Role: {role}

Determine difficulty internally:
Package >= 20 LPA or top-tier company → HARD
Package 10–20 LPA → INTERMEDIATE
Package < 10 LPA → EASY

Generate EXACTLY 30 corporate-level multiple choice questions.

Strict Distribution:
- 12 Quantitative Aptitude
- 12 Logical Reasoning
- 6 Verbal Ability

Rules:
- Not school-level questions
- 4 options per question
- 1 correct answer
- Correct answer must match one option exactly
- No explanations
- No commentary
- No markdown
- Output ONLY valid JSON

Format:

{{
  "aptitude": {{
  "questions":"[--generated questions--]",
  "answers": "[__generated answers--]"
  }},
  "reasoning": {{
  "questions":"[--generated questions--]",
  "answers": "[__generated answers--]"
  }},
  "verbal":{{
  "questions":"[--generated questions--]",
  "answers": "[__generated answers--]"
  }}
}}
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 0.1,
        }
    )

    raw_output = response["message"]["content"]
    clean_json = re.search(r"\{.*\}", raw_output, re.DOTALL).group(0)
    store_in_db(json.loads(clean_json))
    return json.loads(clean_json)


if __name__ == "__main__":

    company = input("Enter Company Name: ")
    role = input("Enter Role Name: ")
    package = float(input("Enter Desired Package (in LPA): "))
    skills = input("Enter Your Skills (comma separated): ")

    questions = generate_questions(company, package, role, skills)

    print(json.dumps(questions, indent=4))