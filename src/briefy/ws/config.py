# config.py
from prettyconf import config

# JWT
JWT_EXPIRATION = config('JWT_EXPIRATION', default='84600')
JWT_SECRET = config('JWT_SECRET', default='e68d4ffb-d621-4d17-a33e-00183e9553e1')


# USER SERVICE
USER_SERVICE_BASE = config(
    'USER_SERVICE_BASE',
    default='http://briefy-rolleiflex.briefy-rolleiflex/internal'
)
USER_SERVICE_TIMEOUT = config(
    'USER_SERVICE_TIMEOUT',
    default=24 * 60  # 24 hours
)
