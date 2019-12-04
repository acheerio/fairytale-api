from google.cloud import datastore
from flask import Blueprint, request
import json
import constants
import status
import helpers

client = datastore.Client()
bp = Blueprint('loads', __name__, url_prefix='/loads')

# POST /loads given weight, content, and delivery_date, creates a load and returns it
# GET /loads returns a list of loads
@bp.route('/', methods=['POST', 'GET'], strict_slashes=False)
def loads_get_post():
    if request.method == 'POST':
        content = request.get_json()
        if "weight" not in content or "content" not in content or "delivery_date" not in content:
            return json.dumps({"Error": "The request object is missing at least one of the required attributes"}), \
                   status.BAD_REQUEST
        else:
            data = {"weight": content["weight"], "content": content["content"], "delivery_date": content["delivery_date"],
                    "carrier": None}
            load = helpers.add_to_store(constants.loads, data)
            return json.dumps(helpers.from_datastore(load, constants.loads, request.url_root)), status.CREATED
    elif request.method == 'GET':
        q_limit = int(request.args.get('limit', '3'))
        q_offset = int(request.args.get('offset', '0'))
        return helpers.get_all_from_store_json(constants.loads, request.url_root, q_limit, q_offset), status.OK
    else:
        return 'Method not recognized'


# GET /loads/<id> returns a list of loads
# DELETE /loads/<id> deletes slip
@bp.route('/<id>', methods=['GET', 'DELETE'])
def loads_get_delete(id):
    load = helpers.get_from_store(constants.loads, id)
    if not load:
        return json.dumps({"Error": "No load with this load_id exists"}), status.NOT_FOUND
    if request.method == 'GET':
        return json.dumps(helpers.from_datastore(load, constants.loads, request.url_root)), status.OK
    elif request.method == 'DELETE':
        carrier_id = None
        if load["carrier"]:
            carrier_id = load["carrier"]["id"]
        helpers.remove_load(carrier_id, id)
        client.delete(load.key)
        return '', status.NO_CONTENT
    else:
        return 'Method not recognized'
