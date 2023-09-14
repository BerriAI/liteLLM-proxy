from typing import Dict

import requests

FASTREPL_PROXY_URL_BASE = "https://fastrepl-proxy-o8ph.zeet-berri.zeet.app"
FASTREPL_PROXY_ADMIN_KEY = "sk-fastrepl-YWp4Yw0-3_g8eaHLK3EJLw"  # TODO


def new_user(monthly_budget: int) -> str:
    resp = requests.post(
        f"{FASTREPL_PROXY_URL_BASE}/key/new",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {FASTREPL_PROXY_ADMIN_KEY}",
        },
        json={"total_budget": monthly_budget},
    )
    print(resp.json())
    return resp.json()


def cost_reset(user_api_key: str):
    requests.get(
        f"{FASTREPL_PROXY_URL_BASE}/cost/reset",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {user_api_key}",
        },
        json={"api_key": user_api_key},
    )


def cost_current(user_api_key: str) -> Dict[str, str]:
    resp = requests.get(
        f"{FASTREPL_PROXY_URL_BASE}/cost/current",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {user_api_key}",
        },
        json={"api_key": user_api_key},
    )
    return resp.json()


def completion_request(user_api_key):
    resp = requests.post(
        f"{FASTREPL_PROXY_URL_BASE}/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {user_api_key}",
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [
                            { 
                                "content": "what is YC?",
                                "role": "user"
                            }
                        ]

        }
    )
    return resp.json()


if __name__ == "__main__":
    key = new_user(100)["api_key"]
    print("new key", key)

    for _ in range(20):
        print(cost_current(key))
    
    response = completion_request(key)
    print(response)
    





"""
Using the Proxy:
# Step1 Get a key


# Step 2 Make a completion request
playground_api_key = "sk-fastrepl-vSvPSy5YLQxeODhi__GSww"

    resp = requests.post(
        f"https://fastrepl-proxy-o8ph.zeet-berri.zeet.app/chat/completions",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer sk-fastrepl-vSvPSy5YLQxeODhi__GSww",
        },
        json={
            "model": "gpt-3.5-turbo",
            "messages": [
                            { 
                                "content": "what is YC?",
                                "role": "user"
                            }
                        ]

        }
    )
    return resp.json()


"""

