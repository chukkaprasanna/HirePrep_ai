import requests

response = requests.get("http://127.0.0.1:5000/generate_general_questions?company=Google&package=15&role=Software%20Engineer&skills=Python,DSA")
print(response.json())
