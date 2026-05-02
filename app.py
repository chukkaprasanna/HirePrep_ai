from flask import Flask, request, jsonify
import psycopg2
from werkzeug.security import generate_password_hash
from werkzeug.security import check_password_hash
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# DATABASE CONNECTION
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="1234",
        port=5432
    )

def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="hireprep1",
        user="postgres",
        password="1234",
        port=5432
    )

#db home
@app.route("/")
def home():
    return "HirePrepAI Backend Running"

# GET APTITUDE QUESTIONS (GET)
@app.route("/get_aptitude_questions", methods=["GET"])
def get_aptitude_questions():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, question, option_a, option_b, option_c, option_d
        FROM aptitude_questions
        ORDER BY RANDOM()
        LIMIT 10
    """)

    rows = cursor.fetchall()

    questions = []

    for row in rows:
        questions.append({
            "id": row[0],
            "question": row[1],
            "options": {
                "A": row[2],
                "B": row[3],
                "C": row[4],
                "D": row[5]
            }
        })

    cursor.close()
    conn.close()

    return jsonify({
        "status": "success",
        "total_questions": len(questions),
        "data": questions
    })

# GET ONE TECHNICAL QUESTION (GET)
@app.route("/get_technical_questions", methods=["GET"])
def get_technical_question():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, title, problem_statement,
               input_format, output_format,
               sample_input, sample_output,
               constraints, difficulty
        FROM technical_questions
        ORDER BY RANDOM()
        LIMIT 1
    """)

    row = cursor.fetchone()

    cursor.close()
    conn.close()

    if row is None:
        return jsonify({
            "status": "error",
            "message": "No technical questions found"
        }), 404

    question = {
        "id": row[0],
        "title": row[1],
        "problem_statement": row[2],
        "input_format": row[3],
        "output_format": row[4],
        "sample_input": row[5],
        "sample_output": row[6],
        "constraints": row[7],
        "difficulty": row[8]
    }

    return jsonify({
        "status": "success",
        "data": question
    })

# SUBMIT CODE (GET VERSION)
@app.route("/submit_code", methods=["GET"])
def submit_code():

    user_id = request.args.get("user_id")
    question_id = request.args.get("question_id")
    code = request.args.get("code")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO user_code_submissions (user_id, question_id, code)
        VALUES (%s, %s, %s)
    """, (user_id, question_id, code))

    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({
        "status": "success",
        "message": "Code submitted successfully"
    })


# sign in page
@app.route('/signup', methods=["POST"])
def signup():
    try:
        email = request.form.get("email")
        password = request.form.get("password")

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO users (email, password) VALUES (%s, %s)",
            (email, hashed_password)
        )

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"success": True})

    except Exception as e:
        print("SIGNUP ERROR:", e)
        return jsonify({"success": False, "error": str(e)})
    
# login
@app.route('/login', methods=["POST"])
def login():
    try:
        email = request.form.get("email")
        password = request.form.get("password")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, password FROM users WHERE email = %s
        """, (email,))

        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user is None:
            return jsonify({
                "status": "error",
                "message": "User not found"
            })

        user_id, stored_password = user

        if check_password_hash(stored_password, password):
            return jsonify({
                "status": "success",
                "user_id": user_id
            })
        else:
            return jsonify({
                "status": "error",
                "message": "Incorrect password"
            })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

# ===============================
# RUN SERVER
# ===============================
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)

