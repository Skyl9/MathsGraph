# logging_config.py
from logging.config import dictConfig


def setup_logging():
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {"format": "[%(correlation_id)s] %(asctime)s - %(name)s - %(levelname)s - %(message)s"}
            },
            "filters": {
                "correlation_id": {
                    "()": "asgi_correlation_id.CorrelationIdFilter",
                    "uuid_length": 32,
                    "default_value": "-",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "level": "DEBUG",
                    "filters": ["correlation_id"],
                },
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
