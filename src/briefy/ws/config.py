# config.py
from prettyconf import config

# JWT
JWT_EXPIRATION = config('JWT_EXPIRATION', default='84600')
JWT_SECRET = config('JWT_SECRET', default='e68d4ffb-d621-4d17-a33e-00183e9553e1')
