import traceback
from flask import Flask, request, jsonify, abort, Response
from flask_cors import CORS
import traceback
import litellm
import threading
from litellm import completion 
from utils import handle_error, get_cache, add_cache, Logging
import os, dotenv, time 
import json
dotenv.load_dotenv()

# TODO: set your keys in .env or here:
# os.environ["OPENAI_API_KEY"] = "" # set your openai key here
# see supported models / keys here: https://litellm.readthedocs.io/en/latest/supported/
######### ENVIRONMENT VARIABLES ##########
verbose = True

############ HELPER FUNCTIONS ###################################

def print_verbose(print_statement):
    if verbose:
        print(print_statement)

######### LOGGING ###################
# # log your data to slack, supabase
successful_callbacks = ["tinydb"]

######### ERROR MONITORING ##########
# log errors to slack, sentry, supabase
# litellm.failure_callback=["slack", "sentry", "supabase"] # .env SENTRY_API_URL
failure_callbacks = ["tinydb", "sentry"]



request_logging = Logging(successful_callbacks=successful_callbacks, failure_callbacks=failure_callbacks, verbose=verbose)

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return 'received!', 200

def data_generator(response):
    for chunk in response:
        yield f"data: {json.dumps(chunk)}\n\n"

@app.route('/chat/completions', methods=["POST"])
def api_completion():
    data = request.json
    start_time = time.time() 
    if data.get('stream') == "True":
        data['stream'] = True # convert to boolean
    try:
        ## User-based rate-limiting
        ### Check if user id passed in
        ### if so -> check key + user combination - if it's a miss, get the user's current status from the db
        ### Key based limits 
        ## Check if key has quota -> check in hot-cache, if it's a miss, get it from the db for the next call 
        ## LOGGING
        request_logging.on_request_start(data)
        # COMPLETION CALL
        print(f"data: {data}")
        response = completion(**data)
        print_verbose(f"Got Response: {response}")
        ## LOG SUCCESS
        end_time = time.time() 
        threading.Thread(target=request_logging.on_request_success, args=(data, request.headers.get('Authorization'), response, start_time, end_time)).start()
        if 'stream' in data and data['stream'] == True: # use generate_responses to stream responses
            return Response(data_generator(response), mimetype='text/event-stream')
    except Exception as e:
        # call handle_error function
        print_verbose(f"Got Error api_completion(): {traceback.format_exc()}")
        ## LOG FAILURE
        end_time = time.time() 
        traceback_exception = traceback.format_exc()
        request_logging.on_request_failure(e, traceback_exception, data, request.headers.get('Authorization'), start_time, end_time) # don't do this threaded - else sentry's capture exception will save the wrong input params (since we're doing model fallbacks)
        # raise e
        return handle_error(data, request_logging=request_logging, auth_headers=request.headers.get('Authorization'), start_time=start_time)

    print_verbose(f"final response: {response}")
    print_verbose(f"type of final response: {type(response)}")
    return response
@app.route('/get_models', methods=["POST"])
def get_models():
    try:
        return litellm.model_list
    except Exception as e:
        traceback.print_exc()
        response = {"error": str(e)}
    return response, 200

if __name__ == "__main__":
  from waitress import serve
  serve(app, host="0.0.0.0", port=4000, threads=500)

# ############ Caching ###################################
# # make a new endpoint with caching
# # This Cache is built using ChromaDB
# # it has two functions add_cache() and get_cache()
# @app.route('/chat/completions_with_cache', methods=["POST"])
# def api_completion_with_cache():
#     data = request.json
#     try:
#         cache_response = get_cache(data['messages'])
#         if cache_response!=None:
#             return cache_response
#         # pass in data to completion function, unpack data
#         response = completion(**data) 

#         # add to cache 
#     except Exception as e:
#         # call handle_error function
#         return handle_error(data)
#     return response, 200

