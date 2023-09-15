import secrets
import traceback
import llm as llm
from utils import getenv
import json
import litellm
from litellm import BudgetManager
litellm.max_budget = 1000 

budget_manager = BudgetManager(project_name="fastrepl_proxy", client_type="hosted")

from fastapi import FastAPI, Request, status, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer

app = FastAPI()

# supabase
from supabase import create_client, Client
import os
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")

supabase: Client = create_client(url, key)

user_api_keys = set(budget_manager.get_users())
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

USERS_KEYS = [
    "sk-fastrepl-YWp4Yw0-3_g8eaHLK3EJLw",
    "sk-liteplayground",
    "sk-ishaantest"
]

# Utils for Auth 
def user_api_key_auth(api_key: str = Depends(oauth2_scheme)):
    if api_key not in user_api_keys:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid user key"},
            # TODO: this will be {'detail': {'error': 'something'}}
        )


def fastrepl_auth(api_key: str = Depends(oauth2_scheme)):
    print(api_key)
    if api_key not in USERS_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": "invalid admin key"},
            # TODO: this will be {'detail': {'error': 'something'}}
        )
# end of utils for auth

# for streaming
def data_generator(response):
    for chunk in response:
        yield f"data: {json.dumps(chunk)}\n\n"

# for completion
@app.post("/chat/completions")
async def completion(request: Request):
    data = await request.json()
    # handle how users send streaming
    if 'stream' in data:
        if type(data['stream']) == str: # if users send stream as str convert to bool
            # convert to bool
            if data['stream'].lower() == "true":
                data['stream'] = True # convert to boolean
    
    response = llm.completion(**data)
    if 'stream' in data and data['stream'] == True: # use generate_responses to stream responses
            return StreamingResponse(data_generator(response), media_type='text/event-stream')
    return response


# Endpoint for adding new LLMs
# use this to store your openai key
# expects data to be {'provider': '', 'key': ''}
@app.post("/litellm/add_key", dependencies=[Depends(fastrepl_auth)])
async def save(request: Request):
    try:
        print("got add key")
        litellm_user_key = request.headers.get("Authorization").replace("Bearer ", "")  # type: ignore
        data = await request.json()
        print(data)
        provider = data.get("provider", "")
        key = data.get("key", "")
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    provider = provider.upper() + "_API_KEY"
    try:
        data = supabase.table('llm_api_keys').select("llm_keys").eq("admin_key", litellm_user_key).execute().data
        if len(data)>0:
            # need to update existing json for user:
            llm_keys = data[0].get('llm_keys', {})
            llm_keys[provider] = key
            supabase_data_obj = {
                "llm_keys": llm_keys
            }
            supabase.table("llm_api_keys").update(supabase_data_obj).eq("admin_key", litellm_user_key).execute()
        else:
            supabase_data_obj = {
                "admin_key": litellm_user_key,
                "llm_keys": { provider: key}
            }
            supabase.table("llm_api_keys").insert(supabase_data_obj).execute()
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return {"status": "saved key", "key_name": provider}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/cost/reset", dependencies=[Depends(user_api_key_auth)])
async def report_reset(request: Request):
    key = request.headers.get("Authorization").replace("Bearer ", "")  # type: ignore
    return budget_manager.reset_cost(key)


@app.get("/cost/current", dependencies=[Depends(user_api_key_auth)])
async def report_current(request: Request):
    key = request.headers.get("Authorization").replace("Bearer ", "")  # type: ignore
    return budget_manager.get_model_cost(key)


@app.post("/key/new", dependencies=[Depends(fastrepl_auth)])
async def generate_key(request: Request):
    try:
        data = await request.json()
        data.get("total_budget")
    except:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)

    total_budget = data["total_budget"]

    api_key = f"sk-fastrepl-{secrets.token_urlsafe(16)}"

    try:
        budget_manager.create_budget(
            total_budget=total_budget, user=api_key, duration="monthly"
        )
        user_api_keys.add(api_key)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return {"api_key": api_key, "total_budget": total_budget, "duration": "monthly"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=getenv("PORT", 8080))
