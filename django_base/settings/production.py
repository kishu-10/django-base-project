from datetime import timedelta
import os
from decouple import config
from .base import *

STATIC_ROOT = os.path.join(BASE_DIR / "static_cdn")
STATIC_URL = "api/static/"

DEBUG = False

ALLOWED_HOSTS = config("ALLOWED_HOSTS")

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=12),
}

# Logs
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": "ocas.log",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file"],
            "propagate": True,
            "level": "INFO",
        },
        "MYAPP": {
            "handlers": ["file"],
            "level": "INFO",
        },
    },
}
