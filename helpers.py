from google.auth.transport import requests
from google.oauth2 import id_token
from google.cloud import datastore
import status
import json
import credentials
import constants

client = datastore.Client()


# Returns the entity with id if exists, else None
def get_from_store(data_type, id_str):
    ent_key = client.key(data_type, int(id_str))
    return client.get(key=ent_key)


# Returns the user entity with Google id id_str if exists, else None
def get_user_by_gid(id_str):
    query = client.query(kind=constants.users)
    results = list(query.fetch())
    for u in results:
        if u.get('gid') == id_str:
            return u
    return None


# Returns JSON of all entities of type data_type after appending id and self attributes
def get_all_from_store_json(data_type, url_root, q_limit, q_offset):
    query = client.query(kind=data_type)
    count = len(list(query.fetch()))
    g_iterator = query.fetch(limit=q_limit, offset=q_offset)
    results = list(next(g_iterator.pages))
    next_url = None
    if g_iterator.next_page_token:
        next_offset = q_offset + q_limit
        next_url = f"{url_root}{data_type}?limit={q_limit}&offset={next_offset}"
    all_entities = list()
    for e in results:
        all_entities.append(from_datastore(e, data_type, url_root))
    output = {data_type: all_entities, 'count': count}
    if next_url:
        output.update({"next": next_url})
    return json.dumps(output)


# Returns JSON of all entities of type data_type affiliated with user
def get_all_by_user_from_store(uid, data_type, base_url):
    query = client.query(kind=data_type)
    unfiltered = list(query.fetch())
    results = list()
    for e in unfiltered:
        owner = e.get('friend')
        if not owner:
            owner = e.get('founder')
        if not owner:
            continue
        elif owner['id'] == uid:
            results.append(from_datastore(e, data_type, base_url))
    obj = {data_type: results}
    return json.dumps(obj)


# Returns self URL
def make_self_url(data_type, url_root, id):
    return f"{url_root}{data_type}/{id}"


# Returns entity with id and self attributes
def from_datastore(e, data_type, url_root):
    if data_type == constants.unicorns:
        e['friend'].update({"self": make_self_url(constants.users, url_root, e['friend']['id'])})
        if e['blessing']:
            e['blessing'].update({"self": make_self_url(constants.blessings, url_root, e['blessing']['id'])})
    elif data_type == constants.blessings:
        e['founder'].update({"self": make_self_url(constants.users, url_root, e['founder']['id'])})
        for unicorn in e['unicorns']:
            unicorn.update({"self": make_self_url(constants.unicorns, url_root, unicorn['id'])})
    e.update({"id": str(e.key.id), "self": make_self_url(data_type, url_root, str(e.key.id))})
    return e


# Returns new entity of specified type with provided data
def add_to_store(data_type, data):
    ent = datastore.Entity(client.key(data_type))
    ent.update(data)
    client.put(ent)
    return ent


# Parameters: request, accept_types, attributes, required
# request - request object
# accept_types - list of accepted mimetypes
# attributes - set of possible attributes, e.g. name, length, key
# required - boolean, whether all of the attributes are required (if False, only one is required)
# Returns: boolean, content, code
# boolean - whether request body is valid or not
# content - body of response as dictionary
# code - status code
def is_valid_request_body(request, attributes, required):
    # 415 check if request body is proper mimetype
    # if request.mimetype and request.mimetype != 'application/json':
    if not request.is_json:
        return False, {"Error": "The service does not support the request media type"}, status.UNSUPPORTED_MEDIA
    # 406 check if requested response mimetype supported
    if not has_acceptable_mimetype(request.accept_mimetypes):
        return False, {"Error": "The service does not support the specified response media type(s)"}, \
               status.NOT_ACCEPTABLE
    # 400 request format
    error_400 = False, {"Error": "The request body is empty or invalid"}, \
                status.BAD_REQUEST
    content = request.get_json(silent=True)
    # 400 - empty body, invalid json
    if not content:
        print("empty json body")
        return error_400
    # 400 - does not contain the required attributes
    elif not has_expected_attributes(attributes, required, content):
        print("does not have expected attributes")
        return error_400
    # remove extra spaces, convert to lowercase
    # 400 - check for character limit, invalid chars, invalid data types
    content = validate(content, attributes)
    if not content:
        print("did not validate correctly")
        return error_400
    else:
        return True, content, -1


def has_acceptable_mimetype(request_accept):
    if constants.json_type in request_accept:
        return True
    return False


# attributes - set of possible attributes, e.g. name, length, key
# required - boolean, whether all of the attributes are required (if False, only one is required)
# content - dictionary to check for attributes
def has_expected_attributes(attributes, required, content):
    # 400 - all attributes are required, does not contain all of them
    if required:
        for attribute in attributes:
            if attribute not in content:
                print(f'{attribute} missing')
                return False
        return True
    # 400 - does not contain at least one attribute
    else:
        has_one_attribute = False
        for attribute in attributes:
            if attribute in content:
                has_one_attribute = True
        return has_one_attribute


# content is a dictionary, attributes is a set
# checks max_len, empty string, invalid chars
# returns None if content invalid
# returns updated obj (stripped, lowercase) if valid
def validate(content, attributes):
    for key, value in content.items():
        # ignore extraneous attributes
        if key in attributes:
            # check data type
            if not isinstance(content[key], constants.type_map[key]):
                print("attribute has wrong data type")
                return None
            # string - strip, lowercase and check length, alphanumeric
            if constants.type_map.get(key) == str:
                value = value.strip()
                content[key] = value
                if not is_valid_str(value):
                    return None
            # int - check within min and max values
            elif constants.type_map[key] == int:
                if value <= 0 or value > constants.max_magic:
                    print("int is not in valid range")
                    return None
    return content


def is_valid_str(s):
    if not s:
        return False
    if len(s) > constants.max_str_length:
        print("exceeds max string length")
        return False
    for c in s:
        if not c.isalnum() and c != ' ':
            return False
    return True


def is_unique(attribute, value):
    data_type = constants.unicorns
    query = client.query(kind=data_type)
    results = list(query.fetch())
    for e in results:
        if e.get(attribute) == value:
            return False
    return True


def get_field(all_fields, type):
    result = []
    for field in all_fields:
        if field["metadata"].get("primary"):
            for f in constants.field_map[type]:
                result.append(field[f])
    return ' '.join(result)


# Returns user entity if valid and exists in database
# Else, returns None
def verify(auth_header):
    if not auth_header:
        print("No authorization header")
        return None
    auth = auth_header.split(' ')
    if len(auth) != 2:
        print("authorization header wrong length")
        return None
    jwt = auth[1]
    req = requests.Request()
    try:
        id_info = id_token.verify_oauth2_token(jwt, req, credentials.oauth_client_id)
    except ValueError as err:
        print(f"{err}")
        return None
    else:
        return get_user_by_gid(id_info.get('sub'))


# Removes a unicorn from the unicorns array in a blessing
def remove_unicorn(blessing_id, unicorn_id):
    if blessing_id:
        blessing = get_from_store(constants.blessings, blessing_id)
        blessing["unicorns"].remove({"id": unicorn_id})
        client.put(blessing)

