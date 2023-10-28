import json
from functools import wraps
from os import environ as env
from urllib.request import urlopen

from dotenv import load_dotenv, find_dotenv
from flask import request
from jose import jwt

ENV_FILE = find_dotenv()
if ENV_FILE:
    load_dotenv(ENV_FILE)

AUTH0_DOMAIN = env.get("AUTH0_DOMAIN")
ALGORITHMS = env.get("ALGORITHMS")
API_AUDIENCE = env.get("API_AUDIENCE")


class AuthError(Exception):
    """
    AuthError Exception
    A standardized way to communicate auth failure modes
    """

    def __init__(self, error, status_code):
        self.error = error
        self.status_code = status_code

    def __repr__(self):
        print(f"Error: {self.error}\nStatus Code: {self.status_code}")


# Auth Header
def get_token_auth_header():
    auth_header = request.headers['Authorization']

    if not auth_header:
        raise AuthError("Missing Authorization Header", 401)

    if len(auth_header.split(' ')) != 2:
        raise AuthError("Header is malformed", 401)
    elif auth_header.split(' ')[0].lower() != "bearer":
        raise AuthError("Header is malformed", 401)

    return auth_header.split(' ')[1]


# Check permission
def check_permissions(permission, payload):
    if "permissions" not in payload:
        raise AuthError("Token Malformed", 401)

    if permission not in payload["permissions"]:
        raise AuthError("Authentication Error", 403)

    return True


def verify_decode_jwt(token):
    jsonurl = urlopen(f"https://{AUTH0_DOMAIN}/.well-known/jwks.json")
    jwks = json.loads(jsonurl.read())  # get jwt
    jwt_header = jwt.get_unverified_header(token)  # get unverified header

    print(f"\n\n{jsonurl}\n\n{jwks}\n\n{jwt_header}")

    if "kid" not in jwt_header:
        raise AuthError({
            'code': 'invalid_header',
            'description': 'Authorization malformed.'
        }, 401)

    rsa_key = {}

    for key in jwks['keys']:
        if key["kid"] == jwt_header["kid"]:
            rsa_key = {'kty': key['kty'],
                       'kid': key['kid'],
                       'use': key['use'],
                       'n': key['n'],
                       'e': key['e']
                       }

    print(f"\n\n{rsa_key}")

    if rsa_key:
        try:
            print(f"\n\n{ALGORITHMS}")
            payload = jwt.decode(token,
                                 key=rsa_key,
                                 algorithms=ALGORITHMS,
                                 audience=API_AUDIENCE,
                                 issuer=f"https://{AUTH0_DOMAIN}/"
                                 )

            return payload
        except jwt.ExpiredSignatureError:
            raise AuthError({
                "code": "token_expired",
                "description": "Your authorization time has been reached, authorize again."
            }, 401)
        except jwt.JWTClaimsError:
            raise AuthError({
                "code": "invalid_claims",
                "description": "Invalid Claims."
            }, 401)
        except Exception:
            raise AuthError({
                "code": "invalid_header",
                "description": "Invalid Header."
            }, 401)

    raise AuthError({
        "code": "invalid_header",
        "description": "Unable to find appropriate key."
    }, 401)


def requires_auth(permission=''):
    def requires_auth_decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            token = get_token_auth_header()
            payload = verify_decode_jwt(token)
            check_permissions(permission, payload)

            return f(payload, *args, **kwargs)

        return wrapper

    return requires_auth_decorator
