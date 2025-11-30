import google.genai as genai
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

client = genai.Client(api_key=API_KEY)

def call_gemini(prompt, model="models/gemini-2.5-flash"):
    response = client.models.generate_content(
        model=model,
        contents=prompt
    )
    return response.text
