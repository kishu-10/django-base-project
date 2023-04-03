from decouple import config

if config('ENVIRONMENT_TYPE') == 'production':
    from .production import *
else:
    from .development import *
