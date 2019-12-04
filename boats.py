from google.cloud import datastore
from flask import Blueprint, request, make_response
import json
import constants
import status
import helpers

client = datastore.Client()
bp = Blueprint('boats', __name__, url_prefix='/boats')

# POST /boats given name, type, and length, creates a boat and returns it
# GET /boats returns a list of boats
@bp.route('/', methods=['POST', 'PUT', 'DELETE'], strict_slashes=False)
def boats_post():
    if request.method == 'POST':
        is_valid, content, code = helpers.is_valid_request_body(request, [constants.json_type], constants.boat_attr, True)
        if is_valid:
            boat = helpers.add_to_store(constants.boats, content)
            return make_response(json.dumps(helpers.from_datastore(boat, constants.boats, request.url_root)),
                                 status.CREATED, {"Content-Type": constants.json_type})
        else:
            return make_response(json.dumps(content), code, {"Content-Type": constants.json_type})
    else:
        # PUT or DELETE on root URL return 405 status
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, {"Content-Type": constants.json_type})


# GET /boats/<id> returns details of specific boat
# DELETE /boats/<id> deletes boat
@bp.route('/<id>', methods=['GET', 'DELETE', 'PUT', 'PATCH'])
def boats_get_put_patch_delete(id):
    boat = helpers.get_from_store(constants.boats, id)
    if not boat:
        return make_response(json.dumps({"Error": "No boat with this boat_id exists"}), status.NOT_FOUND,
                             {"Content-Type": constants.json_type})
    elif request.method == 'GET':
        if constants.json_type in request.accept_mimetypes:
            return make_response(json.dumps(helpers.from_datastore(boat, constants.boats, request.url_root)), status.OK,
                                 {"Content-Type": constants.json_type})
        # elif constants.html_type in request.accept_mimetypes:
        #     return make_response(json2html.convert(json=json.dumps(helpers.from_datastore(boat, constants.boats, request.url_root))),
        #                          status.OK, {"Content-Type": constants.html_type})
        else:
            return make_response(
                json.dumps({"Error": "The service does not support the specified response media type(s)"}),
                status.NOT_ACCEPTABLE, {"Content-Type": constants.json_type})
    elif request.method == 'PUT':
        is_valid, content, code = helpers.is_valid_request_body(request, [constants.json_type], constants.boat_attr, True)
        if is_valid:
            boat.update({"name": content["name"], "type": content["type"], "length": content["length"]})
            client.put(boat)
            self_link = helpers.make_self_url(constants.boats, request.url_root, id)
            return make_response("", status.SEE_OTHER, {"Location": self_link, "Content-Type": constants.json_type})
        else:
            return make_response(json.dumps(content), code, {"Content-Type": constants.json_type})
    elif request.method == 'PATCH':
        is_valid, content, code = helpers.is_valid_request_body(request, [constants.json_type], constants.boat_attr, False)
        if is_valid:
            for attribute in constants.boat_attr:
                if attribute in content:
                    boat.update({attribute: content[attribute]})
            client.put(boat)
            return make_response(json.dumps(helpers.from_datastore(boat, constants.boats, request.url_root)),
                                 status.OK, {"Content-Type": constants.json_type})
        else:
            return make_response(json.dumps(content), code, {"Content-Type": constants.json_type})
    elif request.method == 'DELETE':
        client.delete(boat.key)
        return make_response("", status.NO_CONTENT, {"Content-Type": constants.json_type})
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), status.METHOD_NOT_ALLOWED, {"Content-Type": constants.json_type})