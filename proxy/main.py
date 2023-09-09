import proxy.llm as llm
from proxy.utils import getenv

from fastapi import FastAPI, Request, Response, status

app = FastAPI()


@app.get("/health", status_code=status.HTTP_200_OK)
async def health(response: Response):
    return


@app.post("/chat/completions", status_code=status.HTTP_200_OK)
async def completion(request: Request, response: Response):
    if request.headers.get("Authorization") != getenv("AUTH_TOKEN", ""):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return

    data = await request.json()

    data["cache_params"] = {}
    for k, v in request.headers.items():
        if k.startswith("X-FASTREPL"):
            data["cache_params"][k] = v

    return llm.completion(**data)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=getenv("PORT", 8080))
