from google.cloud import datastore
import status
import json
import constants

client = datastore.Client()


# Returns the entity with id if exists, else None
def get_from_store(data_type, id_str):
    ent_key = client.key(data_type, int(id_str))
    return client.get(key=ent_key)


# Returns JSON of all entities of type data_type after appending id and self attributes
def get_all_from_store_json(data_type, url_root, q_limit, q_offset):
    query = client.query(kind=data_type)
    g_iterator = query.fetch(limit=q_limit, offset=q_offset)
    results = list(next(g_iterator.pages))
    next_url = None
    if g_iterator.next_page_token:
        next_offset = q_offset + q_limit
        next_url = f"{url_root}{data_type}?limit={q_limit}&offset={next_offset}"
    all_entities = list()
    for e in results:
        all_entities.append(from_datastore(e, data_type, url_root))
    output = {data_type: all_entities}
    if next_url:
        output.update({"next": next_url})
    return json.dumps(output)


# Returns self URL
def make_self_url(data_type, url_root, id):
    return f"{url_root}{data_type}/{id}"


# Returns entity with id and self attributes
def from_datastore(e, data_type, url_root):
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
def is_valid_request_body(request, accept_types, attributes, required):
    # 415 check if request body is proper mimetype
    # if request.mimetype and request.mimetype != 'application/json':
    if not request.is_json:
        return False, {"Error": "The service does not support the request media type"}, status.UNSUPPORTED_MEDIA
    # 406 check if requested response mimetype supported
    if not has_acceptable_mimetype(request.accept_mimetypes, accept_types):
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
    # 403 - check for unique name
    elif "name" in attributes and "name" in content and not is_unique("name", content["name"]):
        return False, {"Error": "The specified name is already in use"}, status.FORBIDDEN
    else:
        return True, content, -1


def has_acceptable_mimetype(request_accept, app_accept):
    match = False
    for mimetype in app_accept:
        if mimetype in request_accept:
            match = True
    return match


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
            if constants.type_map[key] == str:
                updated_value = value.strip().lower()
                content[key] = updated_value
                if len(updated_value) > constants.max_str_length:
                    print("exceeds max string length")
                    return None
                # isalnum returns False for empty string
                elif not updated_value.isalnum():
                    print("string is not alphanumeric")
                    return None
            # int - check within min and max values
            elif constants.type_map[key] == int:
                if value <= 0 or value > constants.max_boat_length:
                    print("int is not in valid range")
                    return None
    return content


def is_unique(attribute, value):
    data_type = constants.boats
    query = client.query(kind=data_type)
    results = list(query.fetch())
    for e in results:
        if e.get(attribute) == value:
            return False
    return True
