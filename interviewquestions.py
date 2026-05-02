import time

from flask import Flask, request, jsonify
import json
from sambanova import SambaNova

client = SambaNova(
    base_url="https://api.sambanova.ai/v1",
    api_key="3467a5c9-60ec-4f24-8916-8b626105be24",
    timeout=120.0
)

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


def parse_all_newlines(data):
    if isinstance(data, dict):
        return {k: parse_all_newlines(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [parse_all_newlines(item) for item in data]
    elif isinstance(data, str):
        return data.encode().decode("unicode_escape")
    else:
        return data
app = Flask(__name__)

@app.route('/generate_general_questions', methods=["POST", "GET"])
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

if __name__ == "__main__":
    app.run(debug=True)