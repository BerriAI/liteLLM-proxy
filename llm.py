from typing import Dict
from collections import defaultdict
import threading

from fastapi import HTTPException

from utils import getenv

import backoff
import openai.error

import litellm
import litellm.exceptions
from litellm.caching import Cache

litellm.telemetry = False
litellm.cache = Cache(
    type="redis",
    host=getenv("REDISHOST", ""),
    port=getenv("REDISPORT", ""),
    password=getenv("REDISPASSWORD", ""),
)

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
    LONGER_CONTEXT_MAPPING = {
        "gpt-3.5-turbo": "gpt-3.5-turbo-16k",
        "gpt-3.5-turbo-0613": "gpt-3.5-turbo-16k-0613",
        "gpt-4": "gpt-4-32k",
        "gpt-4-0314": "gpt-4-32k-0314",
        "gpt-4-0613": "gpt-4-32k-0613",
    }
    
    model = str(kwargs.get("model", ""))

    def _completion(overide_model=None):
        try:
            if overide_model is not None:
                kwargs["model"] = overide_model

            response = litellm.completion(**kwargs)

            return response
        except Exception as e:
            handle_llm_exception(e)

    try:
        return _completion()
    except litellm.exceptions.ContextWindowExceededError as e:
        if LONGER_CONTEXT_MAPPING.get(model) is None:
            raise e
        return _completion(LONGER_CONTEXT_MAPPING[model])
