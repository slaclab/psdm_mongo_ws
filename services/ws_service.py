'''
We only implement GET's.
'''

import os
import json
import logging
from datetime import datetime

import requests
from bson import ObjectId
from gridfs import GridFS
from flask import Blueprint, jsonify, request, url_for, Response, send_file

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

@ws_service_blueprint.route("/", methods=["GET"])
def svc_list_of_databases():
    """
    Get list of databases; skip the admin/local and other special databases.
    """
    databases = mongoclient.database_names()
    databases.remove("admin")
    databases.remove("local")
    return JSONEncoder().encode(databases)


@ws_service_blueprint.route("/<database>", methods=["GET"])
def svc_collections_in_database(database):
    """
    Get a list of collections in a database.
    """
    expdb = mongoclient[database]
    return JSONEncoder().encode(expdb.list_collection_names())


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

@ws_service_blueprint.route("/<database>/gridfs/<file_id>", methods=["GET"])
def get_gridfs_document_by_id(database, file_id ) :
    """
    Return the data in a GridFS document as specified by the id
    """
    expdb = mongoclient[database]
    fs = GridFS(expdb)
    out = fs.get(ObjectId(file_id))
    return send_file(out, mimetype='application/octet-stream')

@ws_service_blueprint.route("/<database>/<collection>/gridfs/<object_id>", methods=["GET"])
def get_gridfs_document(database, collection, object_id ) :
    """
    Return the data in a GridFS document.
    We first determine the id of the GridFS doc using the id_data attribute.

    """
    expdb = mongoclient[database]
    fs = GridFS(expdb)
    parent_doc = expdb[collection].find_one({"_id": ObjectId(object_id)})
    gridfs_id = parent_doc.get('id_data', None)
    out = fs.get(gridfs_id)
    return send_file(out, mimetype='application/octet-stream')
