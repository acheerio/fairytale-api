import status
import json

blessings = "blessings"
users = "users"
unicorns = "unicorns"
json_type = "application/json"
json_header = {"Content-Type": json_type}
html_type = "text/html"
type_map = {"name": str, "color": str, "magic": int, "habitat": str, "description": str}
max_str_length = 100
max_magic = 20
unicorns_attr = {"name", "color", "magic"}
blessings_attr = {"name", "habitat", "description"}
field_map = {'name': ['givenName', 'familyName'], 'email': ['value']}
CLIENT_SECRETS_FILE = "client_secret.json"
SCOPES = ['https://www.googleapis.com/auth/userinfo.profile', 'https://www.googleapis.com/auth/userinfo.email', 'openid']
invalid_jwt = json.dumps({"Error": "Missing or invalid JWT"}), status.UNAUTHORIZED, {"Content-Type": json_type}
