import os
from datetime import timedelta

from decouple import config
from .base import *

# SECURITY WARNING: don't run with debug turned on in production!

STATICFILES_DIRS = [os.path.join(os.path.dirname('settings'), 'static')]


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True
}
