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
                'filename': '/srv/apps/knockout-assignment/logs/root.log',
                'formatter': 'plain',
                'when': 'midnight',
                'backupCount': 30,
                'utc': True
            },
            'base_file': {
                'level': 'INFO',
                'class': 'logging.handlers.TimedRotatingFileHandler',
                'filename': '/srv/apps/knockout-assignment/logs/base.log',
                'formatter': 'plain',
                'when': 'midnight',
                'backupCount': 30,
                'utc': True
            },
        },
        'loggers': {
            'core': {
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
