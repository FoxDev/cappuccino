#  This file is part of cappuccino.
#
#  cappuccino is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  cappuccino is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with cappuccino.  If not, see <https://www.gnu.org/licenses/>.

import logging
from logging.config import dictConfig

import yaml

DEFAULT_CONFIG = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)-5s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level': 'INFO',
            'formatter': 'standard',
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',  # Default is stderr
        },
    },
    'root': {
        'handlers': ['default'],
        'level': 'INFO',
    },
    'loggers': {
        'irc3': {
            'handlers': ['default'],
            'propagate': False
        },
        'raw': {
            'handlers': ['default'],
            'propagate': False
        },
        'cappuccino': {
            'handlers': ['default'],
            'level': 'INFO',
            'propagate': False
        },
    }
}


def setup_logging():
    try:
        with open('logging.yml', 'r') as fd:
            dictConfig(yaml.safe_load(fd))
            logging.getLogger(__name__).info('Using logging.yml for logging config.')

    except FileNotFoundError:
        dictConfig(DEFAULT_CONFIG)
        logging.getLogger(__name__).info('logging.yml not found, using default logging config.')
    except yaml.YAMLError as exc:
        dictConfig(DEFAULT_CONFIG)
        logging.getLogger(__name__).exception(exc)


setup_logging()
