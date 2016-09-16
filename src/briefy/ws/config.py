# config.py
from prettyconf import config

# JWT
JWT_EXPIRATION = config('JWT_EXPIRATION')
JWT_SECRET = config('JWT_SECRET')
