'''
We only implement GET's.
'''

import os
import json
import logging
from datetime import datetime

import requests
from bson import ObjectId
from flask import Blueprint, jsonify, request, url_for, Response

from context import mongoclient


__author__ = 'mshankar@slac.stanford.edu'

ws_service_blueprint = Blueprint('ws_service_api', __name__)

logger = logging.getLogger(__name__)

class JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        elif isinstance(o, float) and not math.isfinite(o):
            return str(o)
        elif isinstance(o, datetime):
            # Use var d = new Date(str) in JS to deserialize
            # d.toJSON() in JS to convert to a string readable by datetime.strptime(str, '%Y-%m-%dT%H:%M:%S.%fZ')
            return o.isoformat()
        return json.JSONEncoder.default(self, o)


@ws_service_blueprint.route("/<database>/<collection>/<object_id>", methods=["GET"])
def svc_get_object_by_id(database, collection, object_id):
    """
    Get an object from a collection given the object id.
    We assume that the object_id is a BSON ObjectId.
    If there is a need for other types, we can add a query parameter supporting different types.
    """
    logger.debug("Looking for OID %s in collection %s in database %s", object_id, collection, database)
    expdb = mongoclient[database]
    oid = ObjectId(object_id)
    return JSONEncoder().encode(expdb[collection].find_one({ "_id": oid }))

@ws_service_blueprint.route("/<database>/<collection>", methods=["GET"])
def svc_get_objects_in_collection(database, collection):
    """
    Get objects from a collection.
    These forms of query strings are supported
    * No query string implies all objects in a collection are returned
    * A query string with a single "query_string" parameter results in the value of this parameter being used as the query in the find call
    * All other query strings are converted into a dict which is then used as the query in the find call.
    """
    expdb = mongoclient[database]
    if not len(request.args):
        logger.debug("Returning all objects in the collection %s in the database %s", collection, database)
        return JSONEncoder().encode([x for x in expdb[collection].find()])
    elif 'query_string' in request.args:
        query_string = request.args['query_string']
        logger.debug("Returning all objects in the collection %s in the database %s matching query %s", collection, database, query_string)
        return JSONEncoder().encode([x for x in expdb[collection].find(json.loads(query_string))])
    else:
        logger.debug("Returning all objects in the collection %s in the database %s matching query %s", collection, database, json.dumps(request.args))
        return JSONEncoder().encode([x for x in expdb[collection].find(request.args)])
