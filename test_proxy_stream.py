import openai
import os

os.environ["OPENAI_API_KEY"] = "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"

openai.api_key = os.environ["OPENAI_API_KEY"]
openai.api_base ="http://localhost:4000"

messages = [
    {
        "role": "user",
        "content": "write a 1 pg essay in liteLLM"
    }
]

# response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, stream=True)
response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages, user="krrish@berri.ai")
# response = openai.ChatCompletion.create(model="command-nightly", messages=messages, user="ishaan@berri.ai")
# response = openai.ChatCompletion.create(model="claude-instant-1", messages=messages, user="peter@berri.ai")
print("got response", response)
# response is a generator

# for chunk in response:
#     print(chunk)