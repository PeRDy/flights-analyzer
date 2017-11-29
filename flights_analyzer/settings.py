"""Settings module.
"""
import os

__all__ = ['Settings']


class Settings:
    # Logging
    logging = {
        'version': 1,
        'disable_existing_loggers': True,
        'formatters': {
            'plain': {
                'format': '[%(asctime)s.%(msecs)dZ] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
                'datefmt': '%Y-%m-%dT%H:%M:%S',
            },
        },
        'handlers': {
            'console': {
                'level': 'INFO',
                'class': 'logging.StreamHandler',
                'formatter': 'plain'
            },
            'root_file': {
                'level': 'INFO',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': '/srv/apps/flights-analyzer/logs/root.log',
                'formatter': 'plain',
                'when': 'midnight',
                'backupCount': 30,
                'utc': True
            },
            'base_file': {
                'level': 'INFO',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': '/srv/apps/flights-analyzer/logs/base.log',
                'formatter': 'plain',
                'when': 'midnight',
                'backupCount': 30,
                'utc': True
            },
        },
        'loggers': {
            'tasks': {
                'handlers': ['console', 'base_file'],
                'level': 'INFO',
                'propagate': False,
            },
        },
        'root': {
            'handlers': ['console', 'root_file'],
            'level': 'INFO',
        },
    }

    # Health check
    health_check_providers = {
        'health': (
            ('ping', 'health_check.providers.health.ping', None, None),
        ),
    }

    # Kafka settings
    kafka = {
        'default': {
            'BOOTSTRAP_SERVERS': [
                {
                    'HOST': 'kafka',
                    'PORT': 9002,
                }
            ],
        },
    }

    root_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    schemas_path = os.path.join(root_path, 'schemas')
