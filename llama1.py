import ollama
import json
import re

MODEL_NAME = "llava-llama3:8b"

def generate_questions(company , package, role, skills):

    prompt = f"""
You are HirePrep-AI, an aptitude exam generator for B.Tech software developer students.
the student had these skills : {skills}
the student want to get in the company : {company}
the student needs this package : {package} Lakhs per Annum*
the role student dreams of is : {role}

Generate EXACTLY 30 multiple choice questions.

Distribution:
- 12 Quantitative Aptitude
- 12 Logical Reasoning
- 6 Verbal Ability

Rules:
- Strictly follow difficulty level
- 4 options per question
- Only 1 correct answer
- Correct answer must exactly match one option
- No explanations
- No extra text
- Return ONLY valid JSON

Difficulty Guidelines:

Easy:
Basic arithmetic, percentages, averages, simple reasoning, basic grammar.

Intermediate:
Multi-step calculations, time-work, probability, logical deductions, grammar correction.

Difficult:
Multi-concept quantitative problems, analytical puzzles, advanced reasoning, professional English.

The difficulty of questions shall be dependent on the user input

Strict JSON Format:

{{
  "aptitude": [<--based on the above parameters improve the difficulty generate questions-->],
  "reasoning": [<--based on the above parameters improve the difficulty generate questions-->],
  "verbal": [<--based on the above parameters improve the difficulty generate questions-->]
}}
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": prompt}],
        options={
            "temperature": 0.3,
            "num_predict": 4500
        }
    )

    raw_output = response["message"]["content"]

    # Extract JSON safely
    match = re.search(r"\{.*\}", raw_output, re.DOTALL)
    if not match:
        print("Invalid JSON format received.")
        return None

    try:
        questions = json.loads(match.group(0))
        return questions
    except json.JSONDecodeError as e:
        print("JSON Decode Error:", e)
        return None


if __name__ == "__main__":
    company = input("Enter the comapny name :")
    role = input('Enter the role name :')
    package =  input("Enter the package amount :")
    skills = input('Enter the skills u have :               ')
    questions = generate_questions(
        company=company,
        skills= skills,
        role= role,
        package= package
    )

    if questions:
        print(json.dumps(questions, indent=4))
    else:
        print("Failed to generate questions.")