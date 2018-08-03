from flask import Flask, current_app
import logging
import os
import sys
import json
import requests

from context import app
from services.ws_service import ws_service_blueprint

__author__ = 'mshankar@slac.stanford.edu'


# Initialize application.
app = Flask("psdm_mongo_ws")
# Set the expiration for static files
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 300;
app.secret_key = "This is a secret key that is somewhat temporary."
app.debug = bool(os.environ.get('DEBUG', "False"))

if app.debug:
    print("Sending all debug messages to the console")
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)
    root.addHandler(ch)


# Register routes.
app.register_blueprint(ws_service_blueprint)

if __name__ == '__main__':
    print("Please use gunicorn for development as well.")
    sys.exit(-1)
