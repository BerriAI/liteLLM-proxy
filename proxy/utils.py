import os
import functools
from dotenv import load_dotenv

load_dotenv()

@functools.lru_cache(maxsize=None)
def getenv(key, default=0):
    return type(default)(os.getenv(key, default))
