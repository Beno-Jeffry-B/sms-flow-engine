import os
from groq import Groq

# Initialize Groq client
# Provide a dummy string if the API key is not set so the app doesn't crash on startup
groq_api_key = os.getenv("GROQ_API_KEY", "")
client = Groq(api_key=groq_api_key)

def process_incoming_message(text: str) -> dict:
    """
    Calls Groq to classify the message intent and generate a reply.
    """
    if not groq_api_key:
        return {
            "classification": "api_key_missing",
            "reply": "Error: GROQ_API_KEY is not configured."
        }

    prompt = f"""
Classify the intent of this SMS and generate a short helpful reply.

Message:
"{text}"

Return exactly valid JSON with the following format:
{{
    "classification": "<short 1-3 word intent>",
    "reply": "<the short suggested reply message>"
}}
"""
    try:
        completion = client.chat.completions.create(
            model="llama3-8b-8192",  # Fast and robust model
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Always respond with only valid JSON based on the prompt's schema requirements."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_tokens=150
        )
        response_content = completion.choices[0].message.content
        import json
        result = json.loads(response_content)
        return {
            "classification": result.get("classification", "unknown"),
            "reply": result.get("reply", "I'm sorry, I couldn't understand that.")
        }
    except Exception as e:
        print(f"Error calling Groq: {e}")
        return {
            "classification": "error",
            "reply": "Error processing message via AI."
        }
