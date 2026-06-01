# logging_config.py
from logging.config import dictConfig


def setup_logging():
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "standard", "level": "DEBUG"},
            },
            "loggers": {
                "": {  # logger racine
                    "handlers": ["console"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "uvicorn.error": {"level": "INFO", "handlers": ["console"], "propagate": False},
                "uvicorn.access": {"level": "INFO", "handlers": ["console"], "propagate": False},
            },
        }
    )
