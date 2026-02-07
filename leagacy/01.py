import google.generativeai as genai
import os

# PASTE YOUR API KEY HERE
GEMINI_API_KEY = "AIzaSyDQOo6e_gWY8Wx9gEO14oiqIWgtzLG23kI"

genai.configure(api_key=GEMINI_API_KEY)

print("Checking available models...")
try:
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"- {m.name}")
except Exception as e:
    print(f"Error: {e}")