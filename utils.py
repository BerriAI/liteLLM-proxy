import time, random, sys, subprocess, threading
from copy import deepcopy
import litellm
from litellm import completion, embedding 
import os, dotenv, traceback
import json
dotenv.load_dotenv()
from integrations.tinydb import TinyDB
from integrations.sentry import Sentry
######### ENVIRONMNET VARIABLES ##########
callback_list = []
tinyDBClient = None
backup_keys = {key: "" for key in litellm.provider_list}
for key in backup_keys: 
    if key == "openai": 
        backup_keys[key] = os.getenv("OPENAI_BACKUP_API_KEY")
    elif key == "cohere":
        backup_keys[key] = os.getenv("COHERE_BACKUP_API_KEY")
    elif key == "anthropic":
        backup_keys[key] = os.getenv("ANTHROPIC_BACKUP_API_KEY")
    elif key == "replicate":
        backup_keys[key] = os.getenv("REPLICATE_BACKUP_API_KEY")
    elif key == "huggingface":
        backup_keys[key] = os.getenv("HUGGINGFACE_BACKUP_API_KEY")
    elif key == "together_ai":
        backup_keys[key] = os.getenv("TOGETHERAI_BACKUP_API_KEY")
    elif key == "vertex_ai":
        backup_keys[key] = os.getenv("VERTEXAI_BACKUP_API_KEY")
    elif key == "ai21":
        backup_keys[key] = os.getenv("AI21_BACKUP_API_KEY")
########### streaming ############################
def generate_responses(response):
    for chunk in response:
        yield json.dumps({"response": chunk}) + "\n"

################ ERROR HANDLING #####################
# implement model fallbacks, cooldowns, and retries
# if a model fails assume it was rate limited and let it cooldown for 60s
def handle_error(data, request_logging, auth_headers, start_time):
    # retry completion() request with fallback models
    response = None
    data.pop("model") 
    rate_limited_models = set()
    model_expiration_times = {}
    fallback_strategy=['claude-instant-1', 'gpt-3.5-turbo', 'command-nightly']
    for model in fallback_strategy:
        response = None
        attempt = 0 
        new_data = deepcopy(data)
        execution_complete = False
        for attempt in range(2):
            try:
                if model in rate_limited_models: # check if model is currently cooling down
                    if model_expiration_times.get(model) and time.time() >= model_expiration_times[model]:
                        rate_limited_models.remove(model) # check if it's been 60s of cool down and remove model
                    else:
                        continue # skip model
                ## PREPARE FOR CALL    
                if isinstance(model, str):
                    new_data["model"] = model
                elif isinstance(model, dict):
                    new_data["model"] = model["model"]
                    new_data["custom_llm_provider"] = model["custom_llm_provider"] if "custom_llm_provider" in model else None
                    new_data["custom_api_base"] = model["custom_api_base"] if "custom_api_base" in model else None
                print("model type: ", type(model))
                print(f"new_data[model]: {new_data['model']}")
                ## COMPLETION CALL
                response = completion(**new_data)
            except Exception as e:
                print(f"Got Error handle_error(): {e}")
                end_time = time.time()
                traceback_exception = traceback.format_exc()
                request_logging.on_request_failure(e, traceback_exception, data, auth_headers, start_time, end_time) # don't do this threaded - else sentry's capture exception will save the wrong input params (since we're doing model fallbacks)
                error_type = type(e).__name__
                print(f"error_type handle_error(): {error_type}")
                llm_provider = e.llm_provider
                if "AuthenticationError" in error_type and attempt < 1: # don't retry twice with a bad model key 
                    print(f"handle_error() - Input new_data: {new_data} \n Environment Variables: {os.environ}")
                    # switch to the next key
                    new_data["api_key"] = backup_keys[llm_provider] # dynamically set the backup key - litellm checks this before checking os.environ - https://github.com/BerriAI/litellm/blob/cff26b1d08ba240dcecea7df78a7833990336e6b/litellm/main.py#L112
                elif attempt > 0: # wait a random period before retrying
                    # wait a random period before retrying
                    wait_time = random.randint(1, 10)
                    time.sleep(wait_time)
                elif attempt == 2:
                    rate_limited_models.add(model)
            if response != None:
                break
        if response != None:
            end_time = time.time()
            ## LOGGING SUCCESS
            threading.Thread(target=request_logging.on_request_success, args=(new_data, auth_headers, response, start_time, end_time)).start() # don't block execution of main thread
            break
    return response


########### Pricing is tracked in Supabase ############



import uuid
cache_collection = None
# Add a response to the cache
def add_cache(messages, model_response):
    global cache_collection
    if cache_collection is None:
        make_collection()

    user_question = message_to_user_question(messages)

    # Add the user question and model response to the cache
    cache_collection.add(
        documents=[user_question],
        metadatas=[{"model_response": str(model_response)}],
        ids=[str(uuid.uuid4())]
    )
    return

# Retrieve a response from the cache if similarity is above the threshold
def get_cache(messages, similarity_threshold):
    try:
        global cache_collection
        if cache_collection is None:
            make_collection()

        user_question = message_to_user_question(messages)

        # Query the cache for the user question
        results = cache_collection.query(
            query_texts=[user_question],
            n_results=1
        )

        if len(results['distances'][0]) == 0:
            return None  # Cache is empty

        distance = results['distances'][0][0]
        sim = (1 - distance)

        if sim >= similarity_threshold:
            return results['metadatas'][0][0]["model_response"]  # Return cached response
        else:
            return None  # No cache hit
    except Exception as e:
        print("Error in get cache", e)
        raise e

# Initialize the cache collection
def make_collection():
    import chromadb
    global cache_collection
    client = chromadb.Client()
    cache_collection = client.create_collection("llm_responses")

# HELPER: Extract user's question from messages
def message_to_user_question(messages):
    user_question = ""
    for message in messages:
        if message['role'] == 'user':
            user_question += message["content"]
    return user_question


class Logging:
    def __init__(self, successful_callbacks, failure_callbacks, verbose, verbose_level=1):
        # Constructor
        self.verbose = verbose
        self.verbose_level = verbose_level
        self.successful_callbacks = successful_callbacks
        self.failure_callbacks = failure_callbacks
        self.callback_list = list(set(successful_callbacks + failure_callbacks))
        self.tinyDBClient = None
        self.sentryClient = None
        self.init_callbacks()
    
    def print_verbose(self, print_statement, level):
        if self.verbose and self.verbose_level == level:
            print(print_statement)

    def init_callbacks(self):
        for callback in self.callback_list:
            if callback == "tinydb":
                self.tinyDBClient = TinyDB()
            if callback == "sentry":
                self.sentryClient = Sentry()


    def on_request_start(self, data):
        # Any logging to be done before function is executed - Non-blocking
        try:
            if self.sentryClient:
                self.sentryClient.add_breadcrumb(
                    category="litellm.proxy.llm_call",
                    message=f"Input Data: {data} \n Environment Variables: {os.environ}",
                    level="info",
                )
            pass
        except:
            traceback.print_exc()
            self.print_verbose(f"Got Error on_request_start: {traceback.format_exc()}", level=1)
    
    def on_request_success(self, data, request_key, result, start_time, end_time):
        # log event on success - Non-blocking
        try:
            for callback in self.successful_callbacks:
                if callback == "tinydb":
                    model = data["model"]
                    messages = data["messages"]
                    user = data["user"] if "user" in data else None
                    request_key = request_key
                    self.tinyDBClient.log_event(model=model, messages=messages, user=user, request_key=request_key, response_obj = result, start_time=start_time, end_time=end_time, print_verbose=self.print_verbose)
        except:
            traceback.print_exc()
            self.print_verbose(f"Got Error on_request_success: {traceback.format_exc()}", level=1)
            pass

    def on_request_failure(self, exception, traceback_exception, data, request_key, start_time, end_time):
        # log event on failure - Non-blocking
        try:
            self.print_verbose(f"failure callbacks: {self.failure_callbacks}", level=2)
            for callback in self.failure_callbacks:
                if callback == "tinydb":
                    model = data["model"]
                    messages = data["messages"]
                    request_key = request_key
                    user = data["user"] if "user" in data else None
                    result = {
                        "model": model,
                        "created": time.time(),
                        "error": traceback_exception,
                        "usage": {
                            "prompt_tokens": litellm.token_counter(model, text=" ".join(message["content"] for message in messages)),
                            "completion_tokens": 0
                        }
                    }
                    self.tinyDBClient.log_event(model=model, messages=messages, user=user, request_key=request_key, response_obj = result, start_time=start_time, end_time=end_time, print_verbose=self.print_verbose)
                if callback == "sentry":
                    self.sentryClient.capture_exception(exception)
        except:
            self.print_verbose(f"Got Error on_request_failure: {traceback.format_exc()}", level=1)
            pass