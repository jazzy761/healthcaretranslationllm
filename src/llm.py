from groq import Groq
import os
import re
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GROQ_API_KEY")

def format_response(text):
    text = re.sub(r'(?<=[.!?])\s+', '\n\n', text.strip())
    text = re.sub(r'(?<=\n)(\w[\w\s]{1,20}):', r'**\1:**', text)
    text = re.sub(r'^\d+\.\s', r'- ', text, flags=re.MULTILINE)
    return text.strip()

class LLM:
    def __init__(self, prompt):
        self.prompt = prompt
        self.client = Groq(api_key=api_key)

    def translate(self, prompt):
        system_instruction = f"""
        You're an intelligent medical assistant. Your purpose is simple: 
        1.) Translate the user prompt into the language of the user's choice and then output the user request nothing more nothing less.
        2.) Be sure to identify the users medical condition if discussed by user 
        User Input: {prompt}
        Translated:
        """

        response = self.client.chat.completions.create(
            model="llama3-8b-8192",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt}
            ]
        )

        output = response.choices[0].message.content
        return format_response(output)
