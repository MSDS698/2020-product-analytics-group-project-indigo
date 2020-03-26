from flask import Flask
import os

# Initialization
# Create an application instance (an object of class Flask)  which handles all requests.
application = Flask(__name__)
application.secret_key = os.urandom(24)

from app import routes_3 # routes.py needs to import "application" variable in __init__.py (Altough it violates PEP8 standards)

