from sambanova import SambaNova
import json
import psycopg2
import time
import random
from insertintodb import insert_bulk_questions, insert_bulk_coding_questions, insert_interview_questions
from flask import Flask, request, jsonify
from flask_bcrypt import Bcrypt
import psycopg2
from flask_cors import CORS

MODEL_NAME = "llava-llama3:8b"

# ----------------------------
# SAMBANOVA CLIENT
# ----------------------------
client = SambaNova(
    base_url="https://api.sambanova.ai/v1",
    api_key="1d83e163-aea1-4079-ae16-6f9c3074b7e8",
    timeout=120.0
)


app = Flask(__name__)
CORS(app)   # Allow all origins (required for local HTML files calling Flask)

# ----------------------------
# INTERVIEW QUESTIONS LIST
# ----------------------------
interview_questions = [
    "Tell me about yourself.",
    "What are your strengths and weaknesses?",
    "Why should we hire you?",
    "Where do you see yourself in 5 years?",
    "Why did you choose this field (B.Tech / your branch)?",
    "Describe a challenging situation you faced and how you handled it.",
    "Are you comfortable working in a team? Tell me about a team experience.",
    "How do you handle stress or pressure?",
    "What motivates you?",
    "Do you have any questions for us?"
]

# ----------------------------
# RECURSIVE NEWLINE PARSER
# ----------------------------
def parse_all_newlines(data):
    if isinstance(data, dict):
        return {k: parse_all_newlines(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [parse_all_newlines(item) for item in data]
    elif isinstance(data, str):
        return data.encode().decode("unicode_escape")
    else:
        return data

# ----------------------------
# SAFE JSON EXTRACTOR
# ----------------------------
def extract_valid_json(text):
    stack = []
    start_index = None

    for i, char in enumerate(text):
        if char == "{":
            if not stack:
                start_index = i
            stack.append(char)
        elif char == "}":
            if stack:
                stack.pop()
                if not stack:
                    return text[start_index:i + 1]
    return None

# ----------------------------
# HOME ROUTE
# ----------------------------
@app.route("/")
def home():
    return "HirePrep AI Flask backend is running 🚀"

# ----------------------------
# GET RANDOM INTERVIEW QUESTIONS
# ----------------------------
@app.route('/get_interview_questions', methods=["POST","GET"])
def generate_questions():

    company = request.form.get("company", "Google")
    package = request.form.get("package", "10")
    role    = request.form.get("role",    "Software Engineer")
    skills  = request.form.get("skills",  "Python, DSA")

    prompt = f"""
You are HirePrep-AI, an elite recruitment interview questions generator.
You will now need to generate 3 interview questions to be asked to the candidate based on the following profile:
Candidate Profile:
Skills: {skills}
Target Company: {company}
Desired Package: {package} Lakhs Per Annum
Target Role: {role}


STRICT JSON FORMAT ONLY — no markdown, no extra text:
{{
    "questions": [
        "Question 1",
        "Question 2",
        "Question 3"
    ]
}}
"""

    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                top_p=0.1,
                model="gpt-oss-120b"
            )
            raw_output = completion.choices[0].message.content
            clean_json = extract_valid_json(raw_output)

            if not clean_json:
                time.sleep(1)
                continue

            parsed_data = json.loads(clean_json)
            parsed_data = parse_all_newlines(parsed_data)
            print("Generated Questions:", parsed_data["questions"])
            return jsonify(parsed_data["questions"])

        except Exception as e:
            print("Error occurred:", e)
            time.sleep(1)

    return jsonify({"error": "Failed to generate MCQs"})

# ----------------------------
# EVALUATE INTERVIEW ANSWER (AI feedback for interview page)
# ----------------------------
@app.route('/analyze', methods=["POST"])
def analyze_interview():
    data = request.get_json()
    answers = data.get("answers", [])

    prompt = f"""
You are an expert HR evaluator. Analyze these interview answers and provide structured feedback.

Interview Answers:
{json.dumps(answers, indent=2)}

Return STRICT JSON only:
{{
    "overall_score": "<number 0-100>",
    "communication": "<number 0-100>",
    "confidence": "<number 0-100>",
    "relevance": "<number 0-100>",
    "strengths": ["strength1", "strength2", "strength3"],
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "summary": "<2 sentence overall summary>"
}}
"""
    try:
        completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            top_p=0.1,
            model="gpt-oss-120b"
        )
        raw_output = completion.choices[0].message.content
        clean_json = extract_valid_json(raw_output)
        parsed_data = json.loads(clean_json)
        return jsonify(parse_all_newlines(parsed_data))
    except Exception as e:
        return jsonify({"error": str(e), "overall_score": "65", "summary": "Evaluation failed, please try again."})

# ----------------------------
# EVALUATE CODING ANSWER
# ----------------------------
@app.route('/evaluate_coding_answer', methods=["POST"])
def evaluate_coding_question():

    answer        = request.form.get("answer", "")
    language      = request.form.get("language", "")
    question_data = request.form.get("question_data", "")

    prompt = f"""
You are an expert coding evaluator for a technical interview platform.
Evaluate the candidate's solution below.

Language: {language}
Problem: {question_data}
Candidate's Code:
{answer}

Evaluate on: correctness, time complexity, code quality, readability, and edge case handling.

Return STRICT JSON only:
{{
    "score": "<number 0-100>",
    "time_complexity": "<e.g. O(n)>",
    "space_complexity": "<e.g. O(1)>",
    "correctness": "<High/Medium/Low>",
    "suggestions": ["suggestion1", "suggestion2", "suggestion3"]
}}
"""

    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                top_p=0.1,
                model="gpt-oss-120b"
            )
            raw_output = completion.choices[0].message.content
            clean_json = extract_valid_json(raw_output)
            if not clean_json:
                time.sleep(1)
                continue
            parsed_data = json.loads(clean_json)
            return jsonify(parse_all_newlines(parsed_data))
        except Exception:
            time.sleep(1)

    return jsonify({"error": "Evaluation failed", "score": "60"})

# ----------------------------
# GENERATE CODING QUESTIONS
# ----------------------------
@app.route('/generate_coding_questions', methods=["POST"])
def generate_coding_questions():

    company = request.form.get("company", "Google")
    package = request.form.get("package", "10")
    role    = request.form.get("role",    "Software Engineer")
    skills  = request.form.get("skills",  "Python, DSA")

    prompt = f"""
You are HirePrep-AI, an elite technical interview question generator.

Candidate Profile:
- Skills: {skills}
- Target Company: {company}
- Desired Package: {package} LPA
- Target Role: {role}

Generate EXACTLY ONE original coding question suitable for a technical interview at {company}.
The difficulty should match a {package} LPA role.

STRICT JSON FORMAT ONLY — no markdown, no extra text:
{{
    "coding languages": "Python, JavaScript, Java, C++",
    "question title": "<concise title>",
    "description": "<clear problem statement with constraints>",
    "sample cases": {{
        "first": {{
            "input1": "<sample input>",
            "output1": "<expected output>",
            "explanation1": "<why this output>"
        }},
        "second": {{
            "input2": "<sample input>",
            "output2": "<expected output>",
            "explanation2": "<why this output>"
        }}
    }},
    "testcases": {{
        "testcase1": "<input> → <expected output>",
        "testcase2": "<input> → <expected output>",
        "testcase3": "<input> → <expected output>"
    }}
}}
"""

    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                top_p=0.1,
                model="gpt-oss-120b"
            )
            raw_output = completion.choices[0].message.content
            clean_json = extract_valid_json(raw_output)

            if not clean_json:
                time.sleep(1)
                continue

            parsed_data = json.loads(clean_json)
            parsed_data = parse_all_newlines(parsed_data)
            insert_bulk_coding_questions(parsed_data)
            return jsonify(parsed_data)

        except Exception:
            time.sleep(1)

    return jsonify({"error": "Failed to generate coding question"})

# ----------------------------
# GENERATE MCQ QUESTIONS  ← APTITUDE PAGE
# ----------------------------
@app.route('/generate_general_questions', methods=["POST", "GET"])
def generate_general_questions():
    company = request.form.get("company", "Google")
    package = request.form.get("package", "10")
    role    = request.form.get("role",    "Software Engineer")
    skills  = request.form.get("skills",  "Python, DSA")

    prompt = f"""
You are HirePrep-AI, an elite recruitment exam generator.

Candidate Profile:
- Skills: {skills}
- Target Company: {company}
- Desired Package: {package} LPA
- Target Role: {role}

Generate a complete aptitude test with:
- 12 Quantitative Aptitude questions
- 12 Logical Reasoning questions
- 6 Verbal Ability questions

Each question must have exactly 4 options and one correct answer (A/B/C/D).

STRICT JSON FORMAT ONLY — no markdown, no extra text:
{{
    "aptitude": {{
        "questions": ["Q1 text", "Q2 text", ..., "Q12 text"],
        "options": [["A option","B option","C option","D option"], ...],
        "answers": ["A", "B", ...]
    }},
    "reasoning": {{
        "questions": ["Q1 text", ..., "Q12 text"],
        "options": [["A option","B option","C option","D option"], ...],
        "answers": ["A", "C", ...]
    }},
    "verbal": {{
        "questions": ["Q1 text", ..., "Q6 text"],
        "options": [["A option","B option","C option","D option"], ...],
        "answers": ["B", "A", ...]
    }}
}}
"""

    for attempt in range(3):
        try:
            completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
                top_p=0.1,
                model="gpt-oss-120b"
            )
            raw_output = completion.choices[0].message.content
            clean_json = extract_valid_json(raw_output)

            if not clean_json:
                time.sleep(1)
                continue

            parsed_data = json.loads(clean_json)
            parsed_data = parse_all_newlines(parsed_data)
            insert_bulk_questions(parsed_data)
            return jsonify(parsed_data)

        except Exception:
            time.sleep(1)

    return jsonify({"error": "Failed to generate MCQs"})

# ----------------------------
# FETCH STORED APTITUDE QUESTIONS (from DB)
# ----------------------------
@app.route('/get_aptitude_questions', methods=["GET"])
def get_aptitude_questions():
    """Fetch saved MCQs from DB for the aptitude page (alternative to generating fresh ones)."""
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost", database="postgres",
            user="postgres", password="1234", port=5432
        )
        cursor = conn.cursor()
        cursor.execute("SELECT question, option_a, option_b, option_c, option_d, correct_answer FROM aptitude ORDER BY RANDOM() LIMIT 30")
        rows = cursor.fetchall()
        result = [
            {
                "question": r[0],
                "options": [r[1], r[2], r[3], r[4]],
                "answer": r[5]
            }
            for r in rows
        ]
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        if conn:
            conn.close()

# ----------------------------
# FETCH STORED CODING QUESTIONS (from DB)
# ----------------------------
@app.route('/get_coding_question', methods=["GET"])
def get_coding_question():
    """Fetch a random saved coding question from DB."""
    conn = None
    try:
        conn = psycopg2.connect(
            host="localhost", database="postgres",
            user="postgres", password="1234", port=5432
        )
        cursor = conn.cursor()
        cursor.execute("""
            SELECT coding_languages, question_title, description, sample_cases, testcases
            FROM coding_questions ORDER BY RANDOM() LIMIT 1
        """)
        row = cursor.fetchone()
        if not row:
            return jsonify({"error": "No coding questions found"})
        return jsonify({
            "coding languages": row[0],
            "question title":   row[1],
            "description":      row[2],
            "sample cases":     row[3],
            "testcases":        row[4]
        })
    except Exception as e:
        return jsonify({"error": str(e)})
    finally:
        if conn:
            conn.close()

# ----------------------------
# DATABASE STORAGE (legacy helper)
# ----------------------------
def store_in_db(all_data):
    conn = psycopg2.connect(
        host="localhost", database="postgres",
        user="postgres", password="1234", port=5432
    )
    cursor = conn.cursor()
    try:
        for section in ["aptitude", "reasoning", "verbal"]:
            if section not in all_data:
                continue
            questions = all_data[section].get("questions", [])
            answers   = all_data[section].get("answers", [])
            for q, ans in zip(questions, answers):
                lines = q.strip().split("\n")
                if len(lines) < 5:
                    continue
                cursor.execute("""
                    INSERT INTO questions
                    (section, question, option_a, option_b, option_c, option_d, correct_answer)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    section,
                    lines[0].strip(),
                    lines[1].replace("A)", "").strip(),
                    lines[2].replace("B)", "").strip(),
                    lines[3].replace("C)", "").strip(),
                    lines[4].replace("D)", "").strip(),
                    ans.strip()
                ))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("❌ Database Error:", e)
    finally:
        cursor.close()
        conn.close()


# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    insert_interview_questions(interview_questions)
    app.run(host="0.0.0.0", debug=True, port=6700)