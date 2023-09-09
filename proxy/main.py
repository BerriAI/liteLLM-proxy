import proxy.llm as llm
from proxy.utils import getenv

import secrets, os
from dotenv import dotenv_values, set_key, load_dotenv

load_dotenv(".env")
config = dotenv_values(".env")

from fastapi import FastAPI, Request, Response, status

app = FastAPI()


@app.get("/health", status_code=status.HTTP_200_OK)
async def health(response: Response):
    return


@app.post("/chat/completions", status_code=status.HTTP_200_OK)
async def completion(request: Request, response: Response):
    tokens_string = os.getenv("AUTH_TOKEN", "")
    tokens = tokens_string.split(",")

    if request.headers.get("Authorization") not in tokens:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return

    data = await request.json()
    data["cache_params"] = {}
    for k, v in request.headers.items():
        if k.startswith("X-FASTREPL"):
            data["cache_params"][k] = v

    return llm.completion(**data)


@app.get("/key/new", status_code=status.HTTP_200_OK)
async def generate_key(response: Response):
    api_key = f"sk-fastrepl-{secrets.token_urlsafe(16)}"

    # Append the new API key to the existing list in the Auth_Token variable
    tokens_string = os.getenv("AUTH_TOKEN", "")
    auth_tokens = [tokens_string] if tokens_string != "" else []
    auth_tokens.append(api_key)

    # Update the Auth_Token variable in the .env file
    set_key(".env", "AUTH_TOKEN", ",".join(auth_tokens))
    load_dotenv()  # reload the values into the .env
    return {"api_key": api_key}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=getenv("PORT", 8080))
