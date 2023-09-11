import secrets

import proxy.llm as llm
from proxy.utils import getenv

from dotenv import load_dotenv

load_dotenv(".env")

from fastapi import FastAPI, Request, Response, status, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()
valid_api_keys = set(["FASTREPL_INITIAL_KEY"]) # TODO: Should persist

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def api_key_auth(api_key: str = Depends(oauth2_scheme)):
    if api_key not in valid_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "Unauthorized"},
        )


@app.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "OK"}


@app.get("/cost/reset", dependencies=[Depends(api_key_auth)])
async def report_reset(request: Request):
    key = request.headers.get("Authorization").replace("Bearer ", "")  # type: ignore
    llm.reset_costs(key)


@app.get("/cost/current", dependencies=[Depends(api_key_auth)])
async def report_current(request: Request):
    key = request.headers.get("Authorization").replace("Bearer ", "")  # type: ignore
    return llm.get_costs(key)


@app.post("/chat/completions", dependencies=[Depends(api_key_auth)])
async def completion(request: Request, response: Response):
    key = request.headers.get("Authorization").replace("Bearer ", "")  # type: ignore

    data = await request.json()
    data["api_key"] = key
    data["cache_params"] = {}

    for k, v in request.headers.items():
        if k.startswith("X-FASTREPL"):
            data["cache_params"][k] = v

    return llm.completion(**data)


@app.get("/key/new", dependencies=[Depends(api_key_auth)])
async def generate_key():
    api_key = f"sk-fastrepl-{secrets.token_urlsafe(16)}"
    valid_api_keys.add(api_key)
    valid_api_keys.discard("FASTREPL_INITIAL_KEY")
    return {"api_key": api_key}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=getenv("PORT", 8080))
