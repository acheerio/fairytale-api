from flask import Flask, make_response, redirect, render_template, request, session, url_for
from googleapiclient.discovery import build
from googleapiclient.errors import Error
from google.cloud import datastore
import google.oauth2.credentials
import google_auth_oauthlib.flow
import json
# files
import constants
import helpers
import unicorns
import blessings
import users


app = Flask(__name__)
app.secret_key = b'U#4sUR<JBit7$ug%Ku!gUTd^*8^diYv'
client = datastore.Client()
app.register_blueprint(unicorns.bp)
app.register_blueprint(blessings.bp)
app.register_blueprint(users.bp)


@app.route('/', methods=['GET'])
def index():
    if 'credentials' in session:
        return redirect(url_for('profile'))
    else:
        return render_template('home.html')


@app.route('/auth', methods=['GET'])
def auth():
    if request.method == 'GET':
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(constants.CLIENT_SECRETS_FILE,
                                                                       constants.SCOPES)
        flow.redirect_uri = request.url_root + 'callback'
        authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true')
        session['state'] = state
        return redirect(authorization_url)
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), 405,
                             {"Content-Type": constants.json_type})


@app.route('/callback', methods=['GET'])
def callback():
    if request.method == 'GET':

        state = session['state']
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(constants.CLIENT_SECRETS_FILE, scopes=constants.SCOPES, state=state)
        flow.redirect_uri = url_for('callback', _external=True)

        # Fetch the OAuth 2.0 tokens.
        authorization_response = request.url
        flow.fetch_token(authorization_response=authorization_response)

        # Store credentials in the session.
        credentials = flow.credentials
        session['credentials'] = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': credentials.scopes
        }
        session['jwt'] = credentials.id_token

        return redirect(url_for('profile'))
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), 405,
                             {"Content-Type": constants.json_type})


@app.route('/profile', methods=['GET'])
def profile():
    if request.method == 'GET':
        if 'credentials' in session:
            # Load credentials from the session.
            try:
                credentials = google.oauth2.credentials.Credentials(**session['credentials'])
                people_service = build('people', 'v1', credentials=credentials)
                user_info = people_service.people().get(resourceName='people/me', personFields='names,emailAddresses').execute()
            except Error:
                return redirect(url_for('logout'))
            else:
                _, session['gid'] = user_info['resourceName'].split('/')
                session['name'] = helpers.get_field(user_info["names"], 'name')
                session['email'] = helpers.get_field(user_info["emailAddresses"], 'email')
                data = {'gid': session['gid'], 'name': session['name'], 'email': session['email']}
                # check if existing
                user = helpers.get_user_by_gid(session['gid'])
                # if existing, update fields
                if not user:
                    helpers.add_to_store(constants.users, data)
                else:
                    user.update(data)
                    client.put(user)
                return render_template('profile.html'), 200
        else:
            return redirect(url_for('index'))
    else:
        return make_response(json.dumps({"Error": "Method not allowed"}), 405,
                             {"Content-Type": constants.json_type})


@app.route('/logout')
def logout():
    session.pop('credentials', None)
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)