from google.cloud import datastore
from flask import Blueprint, request, make_response
import json
import constants
import status
import helpers

client = datastore.Client()
bp = Blueprint('blessings', __name__, url_prefix='/blessings')

# POST /blessings given name, habitat, and description, creates a blessing and returns it
# GET /blessings returns a list of blessings
@bp.route('/', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], strict_slashes=False)
def blessings_get_post():
    data_type = constants.blessings
    if request.method == 'GET':
        # check Accept header
        if not helpers.has_acceptable_mimetype(request.accept_mimetypes):
            return make_response(
                json.dumps({"Error": "The service does not support the specified response media type(s)"}),
                status.NOT_ACCEPTABLE, constants.json_header)
        # return results
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        return make_response(helpers.get_all_from_store_json(data_type, request.url_root, q_limit, q_offset), status.OK,
                             constants.json_header)
    elif request.method == 'POST':
        # check valid JWT for existing user
        user = helpers.verify(request.headers.get('Authorization'))
        if not user:
            return make_response(constants.invalid_jwt)
        # check valid request body
        is_valid, content, code = helpers.is_valid_request_body(request, constants.blessings_attr, True)
        if is_valid:
            content.update({'founder': {'id': str(user.key.id)}, 'unicorns': []})
            blessing = helpers.add_to_store(data_type, content)
            return make_response(json.dumps(helpers.from_datastore(blessing, data_type, request.url_root)),
                                 status.CREATED, constants.json_header)
        else:
            return make_response(json.dumps(content), code, constants.json_header)
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, constants.json_header)


# GET /blessings/<id> returns a list of blessings
# PUT, PATCH to edit blessing in full or part respectively
# DELETE /blessings/<id> deletes blessing
@bp.route('/<id>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def blessings_get_put_patch_delete(id):
    if request.method in {'GET', 'PUT', 'PATCH', 'DELETE'}:
        # check valid JWT for existing user
        user = helpers.verify(request.headers.get('Authorization'))
        if request.method != 'GET' and not user:
            return make_response(constants.invalid_jwt)
        # check valid blessing id
        blessing = helpers.get_from_store(constants.blessings, id)
        if not blessing:
            return make_response(json.dumps({"Error": "No blessing with this blessing_id exists"}), status.NOT_FOUND,
                                 constants.json_header)
        # check if the JWT user is the same as the blessing's creator/founder
        if request.method != 'GET' and str(user.key.id) != blessing['founder']['id']:
            return make_response(json.dumps({"Error": "The provided credentials do not have permission to perform that action"}),
                                     status.FORBIDDEN, constants.json_header)
        # route-specific application behavior
        if request.method == 'GET':
            if not helpers.has_acceptable_mimetype(request.accept_mimetypes):
                return make_response(json.dumps({"Error": "The service does not support the specified response media type(s)"}),
                                     status.NOT_ACCEPTABLE, constants.json_header)
            else:
                return make_response(json.dumps(helpers.from_datastore(blessing, constants.blessings, request.url_root)), status.OK,
                                     constants.json_header)
        elif request.method == 'PUT':
            is_valid, content, code = helpers.is_valid_request_body(request, constants.blessings_attr, True)
            if is_valid:
                blessing.update({"name": content["name"], "habitat": content["habitat"], "description": content["description"]})
                client.put(blessing)
                return make_response(json.dumps(helpers.from_datastore(blessing, constants.blessings, request.url_root)),
                                     status.OK, constants.json_header)
            else:
                return make_response(json.dumps(content), code, constants.json_header)
        elif request.method == 'PATCH':
            is_valid, content, code = helpers.is_valid_request_body(request, constants.blessings_attr, False)
            if is_valid:
                for attribute in constants.blessings_attr:
                    if attribute in content:
                        blessing.update({attribute: content[attribute]})
                client.put(blessing)
                return make_response(json.dumps(helpers.from_datastore(blessing, constants.blessings, request.url_root)),
                                     status.OK, constants.json_header)
            else:
                return make_response(json.dumps(content), code, constants.json_header)
        elif request.method == 'DELETE':
            for u in blessing['unicorns']:
                unicorn = helpers.get_from_store(constants.unicorns, u['id'])
                unicorn['blessing'] = None
                client.put(unicorn)
            client.delete(blessing.key)
            return make_response("", status.NO_CONTENT, constants.json_header)
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, constants.json_header)
