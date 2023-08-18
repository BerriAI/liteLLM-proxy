#### What this does ####
#    If an error occurs capture it + it's breadcrumbs with Sentry

import dotenv, os
import requests
dotenv.load_dotenv() # Loading env variables using dotenv
import traceback
import datetime, subprocess, sys

class Sentry: 
    def __init__(self):
        # Instance variables
        try:
            import sentry_sdk
        except ImportError:
            self.print_verbose("Package 'sentry_sdk' is missing. Installing it...")
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'sentry_sdk'])
            import sentry_sdk
        sentry_sdk_instance = sentry_sdk
        self.sentry_trace_rate = os.environ.get("SENTRY_API_TRACE_RATE") if "SENTRY_API_TRACE_RATE" in os.environ else "1.0"
        sentry_sdk_instance.init(dsn=os.environ.get("SENTRY_API_URL"), traces_sample_rate=float(os.environ.get("SENTRY_API_TRACE_RATE")))
        self.capture_exception = sentry_sdk_instance.capture_exception
        self.add_breadcrumb = sentry_sdk_instance.add_breadcrumb 
