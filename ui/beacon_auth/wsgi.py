#!/usr/bin/env python3
"""ELIXIR AAI client API for storing access token to be used in beacon-aggregator."""

from flask import Flask, abort, request, redirect
from uuid import uuid4
import os
import logging
import requests
import requests.auth
import urllib.parse

# ELIXIR AAI configuration
CLIENT_ID = os.environ.get('CLIENT_ID', None)
CLIENT_SECRET = os.environ.get('CLIENT_SECRET', None)
CALLBACK_URL = os.environ.get('CALLBACK_URL', None)
BONA_FIDE_URL = os.environ.get('BONA_FIDE_URL', 'http://www.ga4gh.org/beacon/bonafide/ver1.0')

# Logging
FORMAT = '[%(asctime)s][%(name)s][%(process)d %(processName)s][%(levelname)-8s] (L:%(lineno)s) %(funcName)s: %(message)s'
logging.basicConfig(format=FORMAT, datefmt='%Y-%m-%d %H:%M:%S')
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)


def user_agent():
    """Indicate request source."""
    return "ELIXIR Beacon Login"


def base_headers():
    """Initialize headers."""
    return {"User-Agent": user_agent()}


# Initialize web app
application = Flask(__name__)


@application.route('/app')
def homepage():
    """Redirect to ELIXIR AAI upon loading endpoint."""
    return redirect(make_authorization_url())


def make_authorization_url():
    """Generate URL for redirection to ELIXIR AAI."""
    # Generate state for anti-hijacking
    state = str(uuid4())
    save_created_state(state)  # UNUSED
    params = {"client_id": CLIENT_ID,
              "response_type": "code",
              "state": state,
              "redirect_uri": CALLBACK_URL,
              "duration": "temporary",
              "scope": 'openid bona_fide_status permissions_rems'}
    url = "https://login.elixir-czech.org/oidc/authorize?" + urllib.parse.urlencode(params)
    return url


def save_created_state(state):
    """Save anti-hijacking state to memcache."""
    # This function is not currently used
    pass


def is_valid_state(state):
    """Validate state from memcache."""
    # This function is not currently used
    return True


@application.route('/')
def elixir_callback():
    """Receive callback from ELIXIR AAI, create cookies and redirect to Beacon UI."""
    # Handle errors from ELIXIR AAI
    error = request.args.get('error', '')
    if error:
        return "Error: " + error
    state = request.args.get('state', '')
    # Check if session has been hijacked (currently inoperable)
    if not is_valid_state(state):
        abort(403)

    # Fetch code item from ELIXIR AAI callback to generate authorized access token
    code = request.args.get('code')
    access_token = get_token(code)

    try:
        # Create a redirection to Beacon UI with access token stored in cookies
        response = application.make_response(redirect(os.environ.get('REDIRECT_URL', None)))
        response.set_cookie('access_token',
                            access_token,
                            max_age=int(os.environ.get('COOKIE_AGE', 3600)),
                            secure=os.environ.get('COOKIE_SECURE', True),
                            domain=os.environ.get('COOKIE_DOMAIN', None))
        if get_bona_fide_status(access_token):
            # If user has bona fide status, add a cookie for this
            response.set_cookie('bona_fide_status',
                                BONA_FIDE_URL,
                                max_age=int(os.environ.get('COOKIE_AGE', 3600)),
                                secure=os.environ.get('COOKIE_SECURE', True),
                                domain=os.environ.get('COOKIE_DOMAIN', None))
    except Exception as e:
        LOG.error(str(e))

    return response


def get_token(code):
    """Request access token from ELIXIR AAI using the provided code item."""
    client_auth = requests.auth.HTTPBasicAuth(CLIENT_ID, CLIENT_SECRET)
    post_data = {"grant_type": "authorization_code",
                 "code": code,
                 "redirect_uri": CALLBACK_URL}
    headers = base_headers()
    response = requests.post("https://login.elixir-czech.org/oidc/token",
                             auth=client_auth,
                             headers=headers,
                             data=post_data)
    token_json = response.json()
    return token_json['access_token']


def get_bona_fide_status(access_token):
    """Request Bona Fide status for user from ELIXIR AAI."""
    headers = base_headers()
    headers.update({"Authorization": "Bearer " + access_token})
    response = requests.get("https://login.elixir-czech.org/oidc/userinfo",
                            headers=headers)
    try:
        if 'bona_fide_status' in response.json():
            return True
    except KeyError as ke:
        LOG.error(ke)
        pass


def main():
    """Start the web server."""
    application.secret_key = os.environ.get('COOKIE_SECRET', None)
    application.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', True)
    application.run(host=os.environ.get('APP_HOST', 'localhost'),
                    port=os.environ.get('APP_PORT', 8080),
                    debug=os.environ.get('APP_DEBUG', True))


if __name__ == '__main__':
    main()
