from utils import getenv

import backoff
import openai.error

import litellm
import litellm.exceptions
from litellm import ModelResponse
from litellm.caching import Cache

litellm.telemetry = False
litellm.cache = Cache(
    type="redis",
    host=getenv("REDISHOST", ""),
    port=getenv("REDISPORT", ""),
    password=getenv("REDISPASSWORD", ""),
)

def custom_get_cache_key(*args, **kwargs):
    model = str(kwargs.get("model", ""))
    messages = str(kwargs.get("messages", ""))
    temperature = str(kwargs.get("temperature", ""))
    logit_bias = str(kwargs.get("logit_bias", ""))

    return f"{model}:{messages}:{temperature}:{logit_bias}"

litellm.cache.get_cache_key = custom_get_cache_key

class RetryConstantException(Exception):
    pass


class RetryExpoException(Exception):
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
        raise RetryConstantException from e
    elif isinstance(e, openai.error.RateLimitError):
        raise RetryExpoException from e
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
        raise e


@backoff.on_exception(
    wait_gen=backoff.constant,
    exception=(RetryConstantException),
    max_tries=3,
    interval=3,
)
@backoff.on_exception(
    wait_gen=backoff.expo,
    exception=(RetryExpoException),
    jitter=backoff.full_jitter,
    max_value=100,
    factor=1.5,
)
def completion(**kwargs) -> ModelResponse:
    try:
        return litellm.completion(**kwargs)
    except Exception as e:
        handle_llm_exception(e)
