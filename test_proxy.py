from typing import Dict

import requests

FASTREPL_PROXY_URL_BASE = "https://fastrepl-proxy.fly.dev"
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


if __name__ == "__main__":
    key = new_user(40)["api_key"]

    for _ in range(20):
        print(cost_current(key))