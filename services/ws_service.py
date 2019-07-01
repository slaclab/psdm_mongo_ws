'''
We only implement GET's.
'''

import os
import json
import logging
from datetime import datetime
from functools import wraps

import requests
from bson import ObjectId
from gridfs import GridFS
from flask import Blueprint, jsonify, request, url_for, Response, send_file, abort

from context import mongoclient
import context


__author__ = 'mshankar@slac.stanford.edu'

ws_service_blueprint = Blueprint('ws_service_api', __name__)

logger = logging.getLogger(__name__)
system_databases = ["admin", "local", "config"]

def logAndAbort(error_msg):
    logger.error(error_msg)
    return Response(error_msg, status=500)

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


def privilege_required(*params):
    '''
    Based on the flask_authnz decorator.
    '''
    if len(params) < 1:
        raise Exception("Application privilege not specified when specifying the authorization")
    priv_name = params[0]
    if priv_name not in context.security.priv2roles:
        raise Exception("Please specify an appropriate application privilege for the authorization_required decorator " + ",".join(context.security.priv2roles.keys()))
    def wrapper(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            database_name = kwargs.get("database", None)
            experiment_name = database_name
            if database_name and database_name.startswith("cdb_"):
                experiment_name = database_name[4:]
            logger.info("Looking to authorize %s for app %s for privilege %s for experiment %s" % (context.security.get_current_user_id(), context.security.application_name, priv_name, experiment_name))
            if not context.security.check_privilege_for_experiment(priv_name, experiment_name):
                abort(403)
                return None
            return f(*args, **kwargs)
        return wrapped
    return wrapper

@ws_service_blueprint.route("/", methods=["GET"])
def svc_list_of_databases():
    """
    Get list of databases; skip the admin/local and other special databases.
    """
    databases = [x for x in mongoclient.database_names() if x not in system_databases]
    return JSONEncoder().encode(databases)


@ws_service_blueprint.route("/<database>", methods=["GET"])
def svc_collections_in_database(database):
    """
    Get a list of collections in a database.
    """
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
    expdb = mongoclient[database]
    return JSONEncoder().encode(expdb.list_collection_names())


@ws_service_blueprint.route("/<database>/<collection>/<object_id>", methods=["GET"])
def svc_get_object_by_id(database, collection, object_id):
    """
    Get an object from a collection given the object id.
    We assume that the object_id is a BSON ObjectId.
    If there is a need for other types, we can add a query parameter supporting different types.
    """
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
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
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
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
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
    expdb = mongoclient[database]
    fs = GridFS(expdb)
    out = fs.get(ObjectId(file_id))
    return send_file(out, mimetype='application/octet-stream')


@ws_service_blueprint.route("/<database>/<collection>/", methods=["POST"])
@context.security.authentication_required
@privilege_required("post")
def svc_create_object(database, collection):
    """
    Create a new object in the specified collection
    """
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
    incoming = request.get_json(force=True, silent=False)
    expdb = mongoclient[database]
    inserted_id = expdb[collection].insert_one(incoming).inserted_id
    return JSONEncoder().encode(expdb[collection].find_one({ "_id": inserted_id }))

@ws_service_blueprint.route("/<database>/<collection>/<object_id>", methods=["PUT", "POST"])
@context.security.authentication_required
@privilege_required("post")
def svc_replace_object(database, collection, object_id):
    """
    Replace an existing object in the specified collection. We use the _id as the identifier and upsert the document into the collection.
    """
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
    oid = ObjectId(object_id)
    incoming = request.get_json(force=True, silent=False)
    if "_id" in incoming:
        if incoming["_id"] != oid:
            return logAndAbort("The _id in the call %s and in the object %s do not match." % (oid, incoming["_id"]))
    else:
        incoming["_id"] = oid
    expdb = mongoclient[database]
    expdb[collection].replace_one({"_id": oid}, incoming, upsert=True)
    return JSONEncoder().encode(expdb[collection].find_one({ "_id": oid }))

@ws_service_blueprint.route("/<database>/<collection>/<object_id>", methods=["DELETE"])
@context.security.authentication_required
@privilege_required("post")
def svc_delete_object(database, collection, object_id):
    """
    Delete an existing object from the collection.
    """
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
    oid = ObjectId(object_id)
    expdb = mongoclient[database]
    expdb[collection].delete_one({"_id": oid})
    return JSONEncoder().encode({"status": True})


@ws_service_blueprint.route("/<database>/gridfs/", methods=["PUT", "POST"])
@context.security.authentication_required
@privilege_required("post")
def put_gridfs_document(database ) :
    """
    Insert a gridfs document and return the id of the inserted document.
    """
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
    expdb = mongoclient[database]
    upload = request.files.getlist("files")[0]
    fs = GridFS(expdb)
    oid = fs.put(upload.stream)
    return JSONEncoder().encode({"_id": oid})

@ws_service_blueprint.route("/<database>/gridfs/<object_id>", methods=["DELETE"])
@context.security.authentication_required
@privilege_required("post")
def delete_gridfs_document(database, object_id) :
    """
    Delete a gridfs document
    """
    if database in system_databases:
        return logAndAbort("Cannot get data for system databases")
    expdb = mongoclient[database]
    oid = ObjectId(object_id)
    fs = GridFS(expdb)
    fs.delete(oid)
    return JSONEncoder().encode({"status": True})
