#!/usr/bin/env python3
# coding=utf-8

import enum
from flask import Flask, appcontext_tearing_down, appcontext_pushed
from flask.json import JSONEncoder
from flask_sqlalchemy import SQLAlchemy
from wlanthermo.channels import *
from wlanthermo.settings import *
from wlanthermo.sensors import *
from wlanthermo.website import *
from wlanthermo.modules import Modules
from multiprocessing import Process, Queue
from wlanthermo.modules.fake import *

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'

logger = None


class CustomJSONEncoder(JSONEncoder):

    def default(self, obj):
        try:
            if isinstance(obj, enum.Enum):
                return obj.name
            iterable = iter(obj)
        except TypeError:
            pass
        else:
            return list(iterable)
        return JSONEncoder.default(self, obj)


def logger_thread(q):
    while True:
        record = q.get()
        if record is None:
            break
        logger = logging.getLogger(record.name)
        logger.handle(record)


class Wlanthermo:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.runapp = True
        self.startapp = threading.Event()
        self.app = Flask(__name__)
        self.app.json_encoder = CustomJSONEncoder

        self.set_config_dir()
        self.set_database_uri()
        self.db = SQLAlchemy(self.app)
        Base.metadata.create_all(self.db.engine)

        self.channels = None

        #lp = threading.Thread(target=logger_thread, args=(q,))
        #lp.start()

        #q = Queue()
        # And now tell the logging thread to finish up, too
        #q.put(None)
        #lp.join()

    def set_database_uri(self):
        settings = SystemSettings(self, 'database')
        while True:
            try:
                host = settings['host']
                database = settings['database']
                user = settings['user']
                password = settings['password']
                port = settings['port']
            except KeyError as error:
                failed_key = error.args[0]
                self.logger.error('Database configuration is missing, adding key "{failed_key}" to config file.'.format(
                    failed_key=failed_key))
                settings.set({failed_key: ''})
            else:
                break

        dialect = 'mysql+pymysql'
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        self.logger.debug('Trying to connect to {dialect} database "{database}" as "{user}".'.format(
            dialect=dialect,
            database=database,
            user=user))
        self.app.config['SQLALCHEMY_DATABASE_URI'] = '{dialect}://{user}:{password}@{host}:{port}/{database}'.format(
            dialect=dialect,
            user=user,
            password=password,
            host=host,
            port=port,
            database=database)

    def set_config_dir(self):
        """
        Try to find the right path for configuration files
        The following directories are tried:
          1. Directory given by app configuration 'WLANTHERMO_CONFIG_DIR'
          2. Directory given by enviroment variable 'WLANTHERMO_CONFIG_DIR'
          3. Current working directory
        The directory is created if it doesn´t exist yet.
        """
        try:
            config_dir = self.app.config['WLANTHERMO_CONFIG_DIR']
            self.logger.info('Config path is global {config_dir}')
        except KeyError:
            config_dir = os.environ.get('WLANTHERMO_CONFIG_DIR')
            if config_dir is not None:
                self.logger.info('Config path is "{config_dir}" from enviroment'.format(config_dir=config_dir))
            else:
                config_dir = os.path.join(os.getcwd(), 'config')
                self.logger.info(
                    'Config path is in current working directory ({config_dir})'.format(config_dir=config_dir))
            self.app.config['WLANTHERMO_CONFIG_DIR'] = config_dir

        if not os.path.exists(config_dir):
            self.logger.info('Creating config path ({config_dir})'.format(config_dir=config_dir))
            try:
                os.makedirs(config_dir)
            except OSError:
                self.logger.fatal('Config path could not be created ({config_dir})'.format(config_dir=config_dir))
                raise

        return config_dir

    def start(self):
        """
        Starts the Application
        :return:
        """
        appcontext_tearing_down.connect(self.stop, self.app)
        appcontext_pushed.connect(self.app_pushed, self.app)

        self.fake_module = Thread(target=run_fake_module, args=(self.startapp, self.runapp))

        self.channels = Channels(self)
        self.channels.register_api()

        self.sensors = Sensors(self)
        # self.sensors.register_api()

        self.modules = Modules(self)
        self.modules.register_api()

        self.website = Website(self)
        self.website.register_url()

    def run(self):
        self.fake_module.start()
        self.app.run()

    def stop(self, sender, **kwarg):
        self.runapp = False

    def app_pushed(self, sender, **kwarg):
        self.startapp.set()


def main():
    init_logging()

    wlanthermo = Wlanthermo()
    wlanthermo.start()
    wlanthermo.run()


def init_logging():
    global logger
    log_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'log')
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(os.path.join(log_dir, 'wlanthermo.log'))
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)
    logger.info('Logging started!')


if __name__ == "__main__":
    main()