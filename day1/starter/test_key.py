from dotenv import load_dotenv
import os
load_dotenv()
key = os.getenv("GEMINI_API_KEY")
if key:
    print("Gemini API key valid!")
else:
    print("Gemini API key not provided")