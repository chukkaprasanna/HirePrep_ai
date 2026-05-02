import ollama

MODEL_NAME = "llava-llama3:8b"   

def analyze_photo(img_path):

    prompt = """
You are an AI Interview Confidence Evaluator.

Analyze the given image carefully.

Evaluate based only on:
- Facial expression
- Eye contact
- Posture
- Professional appearance
- Visible confidence level

Give output strictly in this format:

Score: (1-10)
Confidence: (1-100%)
Posture Review:
Facial Expression Review:
Professional Appearance Review:
Suggestions:
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": prompt,
                "images": [img_path]
            }
        ],
        options={
            "temperature": 0.2
        }
    )

    print(response['message']['content'])
    return response['message']['content']


# Example usage
if __name__ == "__main__":
    analyze_photo("sample.jpg")