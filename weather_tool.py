from groq import Groq
import json
import requests
import re
from dotenv import load_dotenv
load_dotenv()

def get_weather(location=None, lat=None, lon=None):
    if location:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={OPEN_WEATHER_APP_ID}"
    elif lat and lon:
        url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPEN_WEATHER_APP_ID}"
    else:
        return "Error: Either location or lat/lon must be provided"
    
    response = requests.get(url)
    data = response.json()
    return data["main"]["temp"]

def call_function(name, args):
    try:    
        if name == "get_weather":
            return get_weather(**args)

    except Exception as e:
        return f"Something went wrong"

def call_llm(prompt: str) -> str:
    client = Groq(api_key="GROQ_API_KEY")
    MODEL = 'openai/gpt-oss-120b'

    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_weather",
                "description": "Retrieve current weather information for a specific location using the OpenWeather API.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "The name of the city or location to get the weather for. Example: 'London, UK'. Optional if lat and lon are provided.",
                        },
                        "lat": {
                            "type": "number",
                            "description": "Latitude of the location. Example: 51.5072",
                        },
                        "lon": {
                            "type": "number",
                            "description": "Longitude of the location. Example: -0.1276",
                        },
                    },
                    "required": ["location"],
                },
            },
        }
    ]

    
    input_messages = [
        {"role": "system", "content": "Answer only with the final result. Do not show your thinking, reasoning, or process. Be extremely brief and direct."},
        {"role": "user", "content": prompt}
    ]

    response = client.chat.completions.create(
        model=MODEL,
        messages=input_messages,
        tools=tools,
        tool_choice="auto",
        temperature=0
    )

    if response.choices[0].message.tool_calls:
        for tool_call in response.choices[0].message.tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            function_result = call_function(function_name, function_args)

            input_messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [tool_call],
            })
            input_messages.append({
                "role": "function",
                "name": function_name,
                "content": str(function_result),
            })

    final_response = client.chat.completions.create(
        model=MODEL,
        messages=input_messages,
        temperature=0
    )


    text = final_response.choices[0].message.content
    cleaned = re.sub(r".*?</think>\s*", "", text, flags=re.DOTALL)
    return cleaned


result = call_llm(prompt="what is the temperature in gandhinagar?")
print(result)
