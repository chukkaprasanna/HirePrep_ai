from sambanova import SambaNova
import json
import psycopg2
import time
from insertintodb import insert_bulk_questions, insert_bulk_coding_questions,insert_interview_questions
from flask import Flask,request


MODEL_NAME = "llava-llama3:8b"

client = SambaNova(
    base_url="https://api.sambanova.ai/v1",
    api_key="e3a9716a-164e-42b6-b297-df6404e208e7",
    timeout=120.0 
)
app = Flask(__name__)
# ----------------------------
# RECURSIVE NEWLINE PARSER
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


@app.route("/")
def home():
    return "Flask is running successfully 🚀"

@app.route('/get_interview_questions',methods=["POST"])
def get_interview_questions():
    return None # random three questions




# ----------------------------
# EVALUATE CODING QUESTION
# ----------------------------
@app.route('/evaluate_coding_answer',methods = ["POST"])
def evaluate_coding_question():

    answer = request.form.get("answer","")
    language = request.form.get("language","")
    question_data = request.form.get("question_data")

    prompt = f"""
            You are a coding evaluator.
            Evaluate the candidate solution.

            Language: {language}
            Problem: {question_data}
            Answer: {answer}

            Return STRICT JSON:
            {{
                "score":"<number(0-100)>",
                "suggestions":["point1","point2"]
            }}
            """

    
    print(f"Evaluating answer...")

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

    try:
        parsed_data = json.loads(clean_json)
        parsed_data = parse_all_newlines(parsed_data)
        return parsed_data
    except:
        time.sleep(1)
    return clean_json



# ----------------------------
# GENERATE CODING QUESTIONS
# ----------------------------
@app.route('/generate_coding_questions',methods = ["POST"])
def generate_coding_questions():
    company = request.form.get("company")
    package = request.form.get("package")
    role = request.form.get("role")
    skills = request.form.get("skills")
    prompt = f"""
You are HirePrep-AI, an elite recruitment exam generator.

Candidate Profile:
Skills: {skills}
Target Company: {company}
Desired Package: {package} LPA
Target Role: {role}

Generate EXACTLY ONE coding question.

STRICT JSON FORMAT ONLY:

{{
    "coding languages":"",
    "question title":"",
    "description":"",
    "sample cases": {{
        "first": {{
            "input1":"",
            "output1":"",
            "explanation1":""
        }},
        "second": {{
            "input2":"",
            "output2":"",
            "explanation2":""
        }}
    }},
    "testcases": {{
        "testcase1":"",
        "testcase2":"",
        "testcase3":""
    }}
}}
"""

    for attempt in range(3):

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

        try:
            parsed_data = json.loads(clean_json)
            parsed_data = parse_all_newlines(parsed_data)    
            print("Parsed Data:", parsed_data)   # 👈 DEBUG
            insert_bulk_coding_questions(parsed_data)   # 👈 MUST BE HERE
            print("Inserted into DB")   # 👈 DEBUG
            return parsed_data
    
        except:
            time.sleep(1)

    raise ValueError("❌ Failed to generate coding question.")


# ----------------------------
# GENERATE MCQ QUESTIONS
# ----------------------------
@app.route('/generate_general_questions',methods = ["POST","GET"])
def generate_questions():
    company = request.form.get("company")
    package = request.form.get("package")
    role = request.form.get("role")
    skills = request.form.get("skills")
    prompt = f"""
You are HirePrep-AI, an elite recruitment exam generator. 
You will need to generate questions and respective answers. 
Candidate Profile: Skills: {skills} 
Target Company: {company} 
Desired Package: {package} 
LPA Target Role: {role} 
Generate EXACTLY: 
 
- 12 Quantitative Aptitude 
- 12 Logical Reasoning 
- 6 Verbal Ability 
Rules: 
- Corporate-level questions only 
- 4 options per question 
- 1 correct answer 
- Correct answer must match one option EXACTLY 
- No explanation 
- No markdown 
- No commentary 
- Output STRICT VALID JSON only 
- JSON must start with {{ and end with }} 
- Donot produce any other text just give plain json format only since we need to parse it. 
Format: {{ 
    "aptitude": 
    {{
          "questions": [], 
          "options":[], 
          "answers": [] 
          }}, 
    "reasoning":
      {{ 
        "questions": [], 
        "options":[], 
        "answers": [] 
        }}, 
    "verbal": {{
          "questions": [], 
          "options":[], 
          "answers": [] 
          }}
     }}
"""

    for attempt in range(3):

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

        try:
            parsed_data = json.loads(clean_json)
            parsed_data = parse_all_newlines(parsed_data)
            store_in_db(parsed_data)
            insert_bulk_questions(parsed_data)
            return parsed_data
        
   
        except:
            time.sleep(1)

    raise ValueError("❌ Failed to generate MCQ questions.")


# ----------------------------
# DATABASE STORAGE
# ----------------------------
def store_in_db(all_data):

    conn = psycopg2.connect(
        host="localhost",
        database="hireprep1",
        user="postgres",
        password="1234",
        port=5432
    )

    cursor = conn.cursor()

    try:
        for section in ["aptitude", "reasoning", "verbal"]:

            if section not in all_data:
                continue

            questions = all_data[section].get("questions", [])
            answers = all_data[section].get("answers", [])

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
    app.run(host="0.0.0.0",debug=True,port=6700)

    # company = input("Enter Company Name: ")
    # role = input("Enter Role Name: ")
    # package = float(input("Enter Desired Package (in LPA): "))
    # skills = input("Enter Your Skills (comma separated): ")

    # questions = generate_questions(company, package, role, skills)
    # coding = generate_coding_questions(company, package, role, skills)

    # print("\n📘 Generated Questions Preview:")
    # print(json.dumps(questions, indent=4, ensure_ascii=False))

    # print("\n💻 Generated Coding Question:")
    # print(json.dumps(coding, indent=4, ensure_ascii=False))


#     coding_ans = """import sys
# import math

# def cosine_similarity(vec1, vec2):
#     dot = sum(a * b for a, b in zip(vec1, vec2))
#     norm1 = math.sqrt(sum(a * a for a in vec1))
#     norm2 = math.sqrt(sum(b * b for b in vec2))
#     if norm1 == 0 or norm2 == 0:
#         return 0.0
#     return dot / (norm1 * norm2)


# def main():
#     data = sys.stdin.read().strip().split('\n')
    
#     # First line: N and D
#     N, D = map(int, data[0].split())
    
#     words = []
#     vectors = []
    
#     # Next N lines: word + embedding
#     for i in range(1, N + 1):
#         parts = data[i].split()
#         word = parts[0]
#         embedding = list(map(float, parts[1:]))
#         words.append(word)
#         vectors.append(embedding)
    
#     # Query vector
#     query_vector = list(map(float, data[N + 1].split()))
    
#     # k value
#     k = int(data[N + 2])
    
#     similarities = []
    
#     for word, vec in zip(words, vectors):
#         sim = cosine_similarity(vec, query_vector)
#         similarities.append((word, sim))
    
#     # Sort by similarity (descending), then lexicographically
#     similarities.sort(key=lambda x: (-x[1], x[0]))
    
#     # Take top k words
#     top_k_words = [word for word, _ in similarities[:k]]
    
#     print(" ".join(top_k_words))


# if __name__ == "__main__":
#     main()"""

#     question_data = """
#     {
#     "coding languages": "Python, Java, C++",
#     "question title": "Top\u2011K Similar Words Using Cosine Similarity",
#     "description": "You are given a list of N words, each associated with a D\u2011dimensional embedding vector of real numbers. After the list, a query embedding vector of the s    "coding languages": "Python, Java, C++",
#     "question title": "Top\u2011K Similar Words Using Cosine Similarity",
#     "description": "You are given a list of N words, each associated with a D\u2011dimensional embedding vector of real numbers. After the list, a query embedding vector of the same dimension D is provided, followed by an integer k. Your task is to compute the cosine similarity between the query vector and each word's embedding, then output the k words wame dimension D is provided, followed by an integer k. Your task is to compute the cosine similarity between the query vector and each word's embedding, then output the k words with the highest similarity, sorted from highest to lowest similarity. If two words have the same similarity, order them lexicographically (alphabetically).",
#     "sample cases": {
#         "first": {
#             "input1": "3 3\napple 0.1 0.2 0.3\nbanana 0.0 0.1 0.0\ncherry 0.2 0.2 0.2\n0.1 0.2 0.3\n2",
#             "output1": "apple cherry",
#             "output1": "apple cherry",
#             "explanation1": "Cosine similarities are: apple\u202f=\u202f1.0, cherry\u202f\u2248\u202f0.927, banana\u202f\u2248\u202f0.535. The top 2 words are apple and cherry." 
#         },
#             "explanation1": "Cosine similarities are: apple\u202f=\u202f1.0, cherry\u202f\u2248\u202f0.927, banana\u202f\u2248\u202f0.535. The top 2 words are apple and cherry." 
#         },
#         "second": {
#             "input2": "4 2\ndog 1 0\ncat 0 1\nmouse 0.6 0.8\nbird 0.8 0.6\n0.6 0.8\n3",
#             "output2": "mouse bird cat",
#             "explanation2": "Similarities: mouse\u202f=\u202f1.0, bird\u202f=\u202f0.96, cat\u202f=\u202f0.8, dog\u202f=\u202f0.6. The three most similar words are mouse, bird and cat."
#         }
#             "output2": "mouse bird cat",
#             "explanation2": "Similarities: mouse\u202f=\u202f1.0, bird\u202f=\u202f0.96, cat\u202f=\u202f0.8, dog\u202f=\u202f0.6. The three most similar words are mouse, bird and cat."
#         }
#             "explanation2": "Similarities: mouse\u202f=\u202f1.0, bird\u202f=\u202f0.96, cat\u202f=\u202f0.8, dog\u202f=\u202f0.6. The three most similar words are mouse, bird and cat."
#         }
#         }
#     },
#     "testcases": {
#         "testcase1": "5 3\nalpha 0.1 0.0 0.0\nbeta 0.0 0.1 0.0\ngamma 0.0 0.0 0.1\ndelta 0.1 0.1 0.1\nepsilon 0.2 0.2 0.2\n0.1 0.1 0.1\n2",
#         "testcase2": "2 4\nx 1 0 0 0\ny 0 1 0 0\n0 0 1 0\n1",
#         "testcase3": "3 5\np 0 0 0 0 1\nq 0 0 0 1 0\nr 0 0 1 0 0\n0 0 0 0 1\n3"
#     }
# }
# """
#     language_sel = "python"

#     print(evaluate_coding_question(answer=coding_ans,question_data=question_data,language=language_sel))