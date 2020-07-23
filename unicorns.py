from google.cloud import datastore
from flask import Blueprint, request, make_response
import json
import constants
import status
import helpers

client = datastore.Client()
bp = Blueprint('unicorns', __name__, url_prefix='/unicorns')

# POST /unicorns given name, color, and magic, creates a unicorn and returns it
# GET /unicorns returns a list of unicorns
@bp.route('/', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'], strict_slashes=False)
def unicorns_get_post():
    data_type = constants.unicorns
    if request.method == 'GET':
        # check Accept header
        if not helpers.has_acceptable_mimetype(request.accept_mimetypes):
            return make_response(json.dumps({"Error": "The service does not support the specified response media type(s)"}),
                                 status.NOT_ACCEPTABLE, constants.json_header)
        # return results
        q_limit = int(request.args.get('limit', '5'))
        q_offset = int(request.args.get('offset', '0'))
        return make_response(helpers.get_all_from_store_json(data_type, request.url_root, q_limit, q_offset), status.OK, constants.json_header)
    if request.method == 'POST':
        # check valid JWT for existing user
        user = helpers.verify(request.headers.get('Authorization'))
        if not user:
            return make_response(constants.invalid_jwt)
        # check valid request body
        is_valid, content, code = helpers.is_valid_request_body(request, constants.unicorns_attr, True)
        if is_valid:
            content.update({'friend': {'id': str(user.key.id)}, 'blessing': None})
            unicorn = helpers.add_to_store(data_type, content)
            return make_response(json.dumps(helpers.from_datastore(unicorn, data_type, request.url_root)),
                                 status.CREATED, constants.json_header)
        else:
            return make_response(json.dumps(content), code, constants.json_header)
    else:
        # PUT or DELETE on root URL return 405 status
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, constants.json_header)


# GET /unicorns/<id> returns details of specific unicorn
# DELETE /unicorns/<id> deletes unicorn
@bp.route('/<id>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def unicorns_get_put_patch_delete(id):
    if request.method in {'GET', 'PUT', 'PATCH', 'DELETE'}:
        # check valid JWT for existing user
        user = helpers.verify(request.headers.get('Authorization'))
        if request.method != 'GET' and not user:
            return make_response(constants.invalid_jwt)
        # check valid unicorn id
        unicorn = helpers.get_from_store(constants.unicorns, id)
        if not unicorn:
            return make_response(json.dumps({"Error": "No unicorn with this unicorn_id exists"}), status.NOT_FOUND,
                                 constants.json_header)
        # check if the JWT user is the same as the unicorn's creator/friend
        if request.method != 'GET' and str(user.key.id) != unicorn['friend']['id']:
            return make_response(json.dumps({"Error": "The provided credentials do not have permission to perform that action"}),
                                     status.FORBIDDEN, constants.json_header)
        # route-specific application behavior
        if request.method == 'GET':
            if not helpers.has_acceptable_mimetype(request.accept_mimetypes):
                return make_response(json.dumps({"Error": "The service does not support the specified response media type(s)"}),
                                     status.NOT_ACCEPTABLE, constants.json_header)
            else:
                return make_response(json.dumps(helpers.from_datastore(unicorn, constants.unicorns, request.url_root)), status.OK,
                                     constants.json_header)
        elif request.method == 'PUT':
            is_valid, content, code = helpers.is_valid_request_body(request, constants.unicorns_attr, True)
            if is_valid:
                unicorn.update({"name": content["name"], "color": content["color"], "magic": content["magic"]})
                client.put(unicorn)
                return make_response(json.dumps(helpers.from_datastore(unicorn, constants.unicorns, request.url_root)),
                                     status.OK, constants.json_header)
            else:
                return make_response(json.dumps(content), code, constants.json_header)
        elif request.method == 'PATCH':
            is_valid, content, code = helpers.is_valid_request_body(request, constants.unicorns_attr, False)
            if is_valid:
                for attribute in constants.unicorns_attr:
                    if attribute in content:
                        unicorn.update({attribute: content[attribute]})
                client.put(unicorn)
                return make_response(json.dumps(helpers.from_datastore(unicorn, constants.unicorns, request.url_root)),
                                     status.OK, constants.json_header)
            else:
                return make_response(json.dumps(content), code, constants.json_header)
        elif request.method == 'DELETE':
            if unicorn['blessing']:
                blessing_id = unicorn["blessing"]["id"]
                helpers.remove_unicorn(blessing_id, id)
            client.delete(unicorn.key)
            return make_response("", status.NO_CONTENT, constants.json_header)
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, constants.json_header)


@bp.route('/<uid>/blessings/<bid>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE'])
def unicorns_put_delete(uid, bid):
    if request.method in {'PUT', 'DELETE'}:
        # check valid JWT for existing user
        user = helpers.verify(request.headers.get('Authorization'))
        if not user:
            return make_response(constants.invalid_jwt)
        # check valid unicorn and blessing id
        unicorn = helpers.get_from_store(constants.unicorns, uid)
        blessing = helpers.get_from_store(constants.blessings, bid)
        if not unicorn or not blessing:
            return make_response(json.dumps({"Error": "The specified unicorn and/or blessing do not exist"}), status.NOT_FOUND,
                                 constants.json_header)
        # check if the JWT user is the same as the unicorn's creator/friend
        if str(user.key.id) != unicorn['friend']['id']:
            return make_response(
                json.dumps({"Error": "The provided credentials do not have permission to perform that action"}),
                status.FORBIDDEN, constants.json_header)
        if request.method == 'PUT':
            if unicorn['blessing']:
                return make_response(json.dumps({"Error": "The unicorn is already assigned to a blessing"}),
                                     status.CONFLICT, constants.json_header)
            # add to unicorn
            unicorn.update({"blessing": {'id': bid}})
            client.put(unicorn)
            # add to blessing
            blessing['unicorns'].append({'id': uid})
            client.put(blessing)
            return make_response('', status.NO_CONTENT, constants.json_header)
        elif request.method == 'DELETE':
            if unicorn['blessing'] and unicorn['blessing']['id'] == bid:
                unicorn.update({'blessing': None})
                client.put(unicorn)
                helpers.remove_unicorn(bid, uid)
                return make_response("", status.NO_CONTENT, constants.json_header)
            else:
                return make_response(json.dumps({"Error": "No unicorn with this unicorn_id is assigned to the blessing with this blessing_id"}),
                                     status.NOT_FOUND, constants.json_header)
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED,
                             constants.json_header)
