import json
import logging
import os

from pymongo import MongoClient

from flask_authnz import FlaskAuthnz, MongoDBRoles, UserGroups

logger = logging.getLogger(__name__)

__author__ = 'mshankar@slac.stanford.edu'

# Application context.
app = None

# Set up the Mongo connection.
# For best results, connect using a user account with only read only permissions
MONGODB_HOST=os.environ['MONGODB_HOST'] or localhost
MONGODB_PORT=int(os.environ['MONGODB_PORT']) or 27017
MONGODB_USERNAME=os.environ['MONGODB_USERNAME'] or 'reader'
MONGODB_PASSWORD=os.environ['MONGODB_PASSWORD'] or 'readerpassword'
mongoclient = MongoClient(host=MONGODB_HOST, port=MONGODB_PORT, username=MONGODB_USERNAME, password=MONGODB_PASSWORD, authSource="admin", tz_aware=True)

ROLEDB_URL=os.environ.get("ROLEDB_URL", None)
roledbclient = mongoclient
if ROLEDB_URL:
    logger.info("Using a different database for the roles")
    roledbclient = MongoClient(host=ROLEDB_URL, tz_aware=True)

# Set up the security manager
usergroups = UserGroups()
roleslookup = MongoDBRoles(roledbclient, usergroups)
security = FlaskAuthnz(roleslookup, "LogBook")
