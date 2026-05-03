import psycopg2
import json


def get_connection():
    return psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="1234",
        port=5432
    )


# -------------------------------
# INSERT MCQ QUESTIONS
# -------------------------------
def insert_bulk_questions(data):

    try:
        conn = get_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO aptitude
            (question, option_a, option_b, option_c, option_d, correct_answer)
            VALUES (%s, %s, %s, %s, %s, %s)
        """

        all_records = []

        for section in ["aptitude", "reasoning", "verbal"]:

            if section not in data:
                continue

            questions = data[section]["questions"]
            options_list = data[section]["options"]
            answers = data[section]["answers"]

            for q, opts, ans in zip(questions, options_list, answers):

                if len(opts) != 4:
                    continue

                record = (
                    q.strip(),
                    opts[0].strip(),
                    opts[1].strip(),
                    opts[2].strip(),
                    opts[3].strip(),
                    ans.strip()
                )

                all_records.append(record)

        if all_records:
            cursor.executemany(insert_query, all_records)
            conn.commit()
            print(f"✅ {len(all_records)} MCQs inserted successfully!")

    except Exception as e:
        print("❌ MCQ Insert Error:", e)

    finally:
        cursor.close()
        conn.close()


# -------------------------------
# INSERT CODING QUESTION
# -------------------------------
def insert_bulk_coding_questions(data):

    try:
        conn = get_connection()
        cursor = conn.cursor()

        insert_query = """
            INSERT INTO coding_questions
            (coding_languages, question_title, description, sample_cases, testcases)
            VALUES (%s, %s, %s, %s, %s)
        """

        record = (
            data["coding languages"].strip(),
            data["question title"].strip(),
            data["description"].strip(),
            json.dumps(data["sample cases"]),
            json.dumps(data["testcases"])
        )

        cursor.execute(insert_query, record)
        conn.commit()

        print("✅ Coding question inserted successfully!")

    except Exception as e:
        print("❌ Coding Insert Error:", e)

    finally:
        cursor.close()
        conn.close()

def insert_interview_questions(questions):

    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="1234",
        port=5432
    )

    cursor = conn.cursor()

    try:
        insert_query = """
            INSERT INTO interview_questions (question)
            VALUES (%s)
            ON CONFLICT (question) DO NOTHING
        """

        records = [(q.strip(),) for q in questions]
        cursor.executemany(insert_query, records)

        conn.commit()
        print("✅ Interview questions inserted safely (no duplicates).")

    except Exception as e:
        conn.rollback()
        print("❌ Interview Insert Error:", e)

    finally:
        cursor.close()
        conn.close()