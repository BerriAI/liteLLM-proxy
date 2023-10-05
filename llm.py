from typing import Dict
from collections import defaultdict
import threading

from fastapi import HTTPException

from utils import getenv

import backoff
import openai.error

import litellm
import os
import litellm.exceptions
from litellm.caching import Cache

# litellm.cache = Cache( # optional if you want to use cache
#     type="redis",
#     host=getenv("REDISHOST", ""),
#     port=getenv("REDISPORT", ""),
#     password=getenv("REDISPASSWORD", ""),
# )

cost_dict: Dict[str, Dict[str, float]] = defaultdict(dict)
cost_dict_lock = threading.Lock()


def _update_costs_thread(budget_manager: litellm.BudgetManager):
    thread = threading.Thread(target=budget_manager.save_data)
    thread.start()


class RetryConstantError(Exception):
    pass


class RetryExpoError(Exception):
    pass


class UnknownLLMError(Exception):
    pass


def handle_llm_exception(e: Exception):
    if isinstance(
        e,
        (
            openai.error.APIError,
            openai.error.TryAgain,
            openai.error.Timeout,
            openai.error.ServiceUnavailableError,
        ),
    ):
        raise RetryConstantError from e
    elif isinstance(e, openai.error.RateLimitError):
        raise RetryExpoError from e
    elif isinstance(
        e,
        (
            openai.error.APIConnectionError,
            openai.error.InvalidRequestError,
            openai.error.AuthenticationError,
            openai.error.PermissionError,
            openai.error.InvalidAPIType,
            openai.error.SignatureVerificationError,
        ),
    ):
        raise e
    else:
        raise UnknownLLMError from e


@backoff.on_exception(
    wait_gen=backoff.constant,
    exception=RetryConstantError,
    max_tries=3,
    interval=3,
)
@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=RetryExpoError,
    jitter=backoff.full_jitter,
    max_value=100,
    factor=1.5,
)
def completion(**kwargs) -> litellm.ModelResponse:

    user_key = kwargs.pop("user_key")
    master_key = kwargs.pop("master_key")
    budget_manager: litellm.BudgetManager = kwargs.pop("budget_manager")

    def _completion():
        try:
            default_model = os.getenv("DEFAULT_MODEL", None)
            if default_model is not None and default_model != "":
                kwargs["model"] = default_model

            if user_key == master_key:
                # use as admin of the server
                response = litellm.completion(**kwargs)
            else:
                # for end user based rate limiting
                if budget_manager.get_current_cost(
                    user=user_key
                ) > budget_manager.get_total_budget(user=user_key):
                    raise HTTPException(
                        status_code=429, detail={"error": "budget exceeded"}
                    )
                response = litellm.completion(**kwargs)

            if "stream" not in kwargs or kwargs["stream"] is not True:
                print(f"user_key: {user_key}")
                print(f"master_key: {master_key}")
                if user_key != master_key: # no budget on master key
                    # updates both user
                    budget_manager.update_cost(completion_obj=response, user=user_key)
                    _update_costs_thread(budget_manager)  # Non-blocking

            return response
        except Exception as e:
            print(f"LiteLLM Server: Got exception {e}")
            handle_llm_exception(e) # this tries fallback requests

    try:
        return _completion()
    except Exception as e:
        raise e


# LiteLLM Config
# config = {
#     "function": "completion",
#     "default_fallback_models": ["gpt-3.5-turbo", "claude-instant-1", "j2-ultra"],
#     "available_models": litellm.utils.get_valid_models(),
#     "adapt_to_prompt_size": True,
#     "model": {
#         "claude-instant-1": {
#             "needs_moderation": True
#         },
#         "claude-2": {
#             "needs_moderation": True
#         },
#         "gpt-3.5-turbo": {
#             "error_handling": {
#                 "ContextWindowExceededError": {"fallback_model": "gpt-3.5-turbo-16k"} 
#             }
#         },
#         "gpt-3.5-turbo-0613": {
#             "error_handling": {
#                 "ContextWindowExceededError": {"fallback_model": "gpt-3.5-turbo-16k-0613"} 
#             }
#         }, 
#         "gpt-4": {
#             "error_handling": {
#                 "ContextWindowExceededError": {"fallback_model": "claude-2"} 
#             }
#         }
#     }
# }