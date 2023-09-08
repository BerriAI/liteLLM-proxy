import llm
from utils import getenv

from fastapi import FastAPI, Request, Response, status
app = FastAPI()

import redis
r = redis.from_url(getenv("REDIS_URL", ""))

@app.get("/health", status_code=status.HTTP_200_OK)
async def health(response: Response):
    try:
        res = r.ping()
        if res:
            response.status_code = status.HTTP_200_OK
            return
        else:
            response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            return
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return {"error": str(e)}
    

@app.post("/chat/completions", status_code=status.HTTP_200_OK)
async def completion(request: Request, response: Response):
    if request.headers.get("Authorization") != getenv("AUTH_TOKEN", ""):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return

    data = await request.json()
    return llm.completion(**data)
