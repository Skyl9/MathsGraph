# logging_config.py
from logging.config import dictConfig


def setup_logging():
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
            "handlers": {
                "console": {"class": "logging.StreamHandler", "formatter": "standard", "level": "INFO"},
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "standard",
                    "level": "DEBUG",
                    "filename": "app.log",
                    "maxBytes": 10_000_000,
                    "backupCount": 5,
                    "encoding": "utf8",
                },
            },
            "loggers": {
                "": {  # logger racine
                    "handlers": ["console", "file"],
                    "level": "DEBUG",
                    "propagate": False,
                },
                "uvicorn.error": {"level": "WARNING"},
            },
        }
    )
