import os
import functools
from dotenv import load_dotenv

load_dotenv()


@functools.lru_cache(maxsize=None)
def getenv(key, default=0):
    return type(default)(os.getenv(key, default))


def set_env_variables(data):
    try:
        if "env_variables" in data:
            env_variables = data["env_variables"]
            for key in env_variables:
                os.environ[key] = env_variables[key]
            data.pop("env_variables")
    except:
        pass
