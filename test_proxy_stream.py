import openai
from dotenv import load_dotenv
import os

# Load the environment variables from the .env file
load_dotenv()

# Access the API key
api_key = os.getenv("OPENAI_API_KEY")

# Set the API key
os.environ["OPENAI_API_KEY"] = api_key

# Now, you can use it as before
openai.api_key = api_key
openai.api_base = "http://localhost:4000"

messages = [
    {
        "role": "user",
        "content": "write a 1 pg essay in liteLLM"
    }
]

response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, user="krrish@berri.ai")

print("got response", response)
