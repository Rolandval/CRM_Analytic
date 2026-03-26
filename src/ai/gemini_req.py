import google.generativeai as genai
from dotenv import load_dotenv
import os
import json
import re


load_dotenv()


async def gemini_request(prompt):
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
#     grounding_tool = genai.Tool.from_google_search_retrieval(
#     google_search_retrieval=genai.GoogleSearchRetrieval()
# )

    # Використовуємо доступну модель gemini-1.5-flash або gemini-pro
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro",
        generation_config={
            "temperature": 0.3,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 600000
        },
        # tools=[grounding_tool]
    )
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        if response_text.startswith("```json"):
            response_text = response_text.replace("```json", "", 1)
        if response_text.endswith("```"):
            response_text = response_text.rsplit("```", 1)[0]
        response_text = response_text.strip()
        print(response_text)

        response_text = re.sub(r'\\(?!["\\/bfnrt]|u[0-9a-fA-F]{4})', r'\\\\', response_text)
                
        # Парсимо JSON
        json_data = json.loads(response_text)
        
        return json_data
    except Exception as e:
        print(f"Помилка аналізу: {e}")
        return "Помилка аналізу"