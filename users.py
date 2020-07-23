from google.cloud import datastore
from flask import Blueprint, request, make_response
import json
import constants
import status
import helpers

client = datastore.Client()
bp = Blueprint('users', __name__, url_prefix='/users')

# Unused route, defined because it is on the path to a defined route
@bp.route('/', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], strict_slashes=False)
def users():
    return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, constants.json_header)


# Unused route, defined because it is on the path to a defined route
@bp.route('/<id>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def users_id(id):
    return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, constants.json_header)


# GET /users/<uid>/unicorns returns a list of unicorns created by the user
@bp.route('/<id>/unicorns', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def users_unicorns(id):
    if request.method == 'GET':
        # check valid user id
        user = helpers.get_from_store(constants.users, id)
        if not user:
            return make_response(json.dumps({"Error": "No user with this user_id exists"}), status.NOT_FOUND,
                                 constants.json_header)
        elif not helpers.has_acceptable_mimetype(request.accept_mimetypes):
            return make_response(json.dumps({"Error": "The service does not support the specified response media type(s)"}),
                                     status.NOT_ACCEPTABLE, constants.json_header)
        else:
            return make_response(helpers.get_all_by_user_from_store(id, constants.unicorns, request.url_root), status.OK, constants.json_header)
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, constants.json_header)


# GET /users/<uid>/blessings returns a list of blessings created by the user
@bp.route('/<id>/blessings', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def users_blessings(id):
    if request.method == 'GET':
        # check valid user id
        user = helpers.get_from_store(constants.users, id)
        if not user:
            return make_response(json.dumps({"Error": "No user with this user_id exists"}), status.NOT_FOUND,
                                 constants.json_header)
        elif not helpers.has_acceptable_mimetype(request.accept_mimetypes):
            return make_response(
                json.dumps({"Error": "The service does not support the specified response media type(s)"}),
                status.NOT_ACCEPTABLE, constants.json_header)
        else:
            return make_response(helpers.get_all_by_user_from_store(id, constants.blessings, request.url_root),
                                 status.OK, constants.json_header)
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED,
                             constants.json_header)