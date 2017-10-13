#!/usr/bin/env python3
# coding=utf-8

import logging
import os
import yaml
import collections
import threading
import sqlalchemy
from copy import copy, deepcopy
from wlanthermo.database.tables import *

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'


class Settings:
    def __init__(self, wlanthermo, scope):
        self.logger = logging.getLogger(__name__)
        self.wlanthermo = wlanthermo
        self.app = wlanthermo.app
        self.db = wlanthermo.db
        self.scope = scope

    def get(self, key):
        try:
            row = self.db.session.query(SettingsTable).filter_by(scope=self.scope, key=key).one()
        except sqlalchemy.orm.exc.NoResultFound:
            self.logger.error('Config key {key} not found in scope {scope}!'.format(key=key, scope=self.scope))
            return None
        except sqlalchemy.orm.exc.MultipleResultsFound:
            self.logger.error('Multiple keys {key} found in scope {scope}!'.format(key=key, scope=self.scope))
            return None
        return row.value

    def set(self, key, value):
        try:
            entry = self.db.session.query(SettingsTable).filter_by(scope=self.scope, key=key).one()
            entry.value = value
        except sqlalchemy.orm.exc.NoResultFound:
            entry = SettingsTable(
                scope=self.scope,
                key=key,
                value=value
            )
            self.db.session.add(entry)
        self.db.session.commit()
        return value


class SystemSettings:
    class GlobalSettings:
        def __init__(self, wlanthermo, config_dir=None):
            self.app = wlanthermo.app
            self.logger = logging.getLogger(__name__)
            self.config_dir = self.app.config['WLANTHERMO_CONFIG_DIR']
            self._configuration = dict()
            self._configuration_lock = threading.Lock()
            self.load()

        def set(self, scope, config):
            """Update module config with given config
            """
            self.logger.info('Updating configuration scope: "{scope}" with "{config}"'.format(scope=scope, config=config))
            try:
                self._update_dict(self._configuration[scope], config)
            except KeyError:
                self._configuration[scope] = config

            self.save(scope)

        def _update_dict(self, source, update):
            """Update a nested dictionary or similar mapping.

            Modify ``source`` in place.
            """
            for key, value in update.items():
                if isinstance(value, collections.Mapping) and value:
                    returned = self._update_dict(source.get(key, {}), value)
                    source[key] = returned
                else:
                    source[key] = update[key]
            return source

        def _defaults_dict(self, source, defaults):
            """Set default values to a nested dictionary or similar mapping.

            Modify ``source`` in place.
            a = {'a':1,'b':2,'c':3}
            b = {'a':2,'d':4}
            _defaults_dict(a, b)
            {'a': 1, 'b': 2, 'c': 3, 'd': 4}
            """
            for key, value in defaults.items():
                if isinstance(value, collections.Mapping) and value:
                    returned = self._defaults_dict(source.get(key), value)
                    source[key] = returned
                elif key not in source:
                    source[key] = defaults[key]
            return source

        def get(self, scope=None):
            if scope is None:
                return self._configuration
            else:
                try:
                    return self._configuration[scope]
                except KeyError:
                    self._configuration[scope] = dict()
                    return self._configuration[scope]

        def save(self, scope=None):
            """Save config to disk
            """
            if scope is None:
                for scope, config in self._configuration.items():
                    filename = os.path.join(self.config_dir, scope + '.yaml')
                    self.logger.info('Saving scope "{scope}" to "{filename}"'.format(scope=scope, filename=filename))
                    with open(filename, 'w') as config_file:
                        contents = yaml.dump(self._configuration[scope])
                        config_file.write(contents)
            else:
                try:
                    filename = os.path.join(self.config_dir, scope + '.yaml')
                    self.logger.info('Saving scope "{scope}" to "{filename}"'.format(scope=scope, filename=filename))
                    with open(filename, 'w') as config_file:
                        contents = yaml.dump(self._configuration[scope])
                        config_file.write(contents)
                except NameError:
                    self.logger.warning('Scope "{scope}" not in configuration'.format(scope=scope))

        def load(self, scope=None):
            """
            Load config from disk
            :param scope: 
            :return: 
            """
            if scope is None:
                for entry in os.scandir(self.config_dir):
                    if entry.is_file() and entry.name.endswith('.yaml'):
                        scope = entry.name[:-5]
                        self.logger.info('Loading scope "{scope}" from "{entry_path}"'.format(
                            scope=scope,
                            entry_path=entry.path))
                        with open(entry.path, 'r') as config_file:
                            contents = config_file.read()
                        self._configuration[scope] = yaml.load(contents)
                        
                    else:
                        continue
            else:
                filename = os.path.join(self.config_dir, scope + '.yaml')
                if os.path.isfile(filename):
                    self.logger.info('Loading scope "{scope}" from "{filename}"'.format(scope=scope, filename=filename))
                    with open(filename, 'r') as config_file:
                        contents = config_file.read()
                    self._configuration[scope] = yaml.load(contents)
        
        def on_set_config(self, client, userdata, msg):
            topic = re.search('.*\/(.*)\/', msg.topic).group(1)
            self.logger.info('Received new config for "{topic}".'.format(topic=topic))
        
    global_settings = None
    global_settings_lock = threading.Lock()

    def __init__(self, wlanthermo, scope):
        self.logger = logging.getLogger(__name__)
        if not SystemSettings.global_settings:
            with SystemSettings.global_settings_lock:
                SystemSettings.global_settings = SystemSettings.GlobalSettings(wlanthermo)
        self.scope = scope
        self.wlanthermo = wlanthermo

    def __getitem__(self, key):
        """
        Getting the configuration is easy, setting requires asyncio
        """
        with SystemSettings.global_settings_lock:
            value = deepcopy(self.global_settings.get(self.scope)[key])
        return self.global_settings.get(self.scope)[key]

    def __repr__(self):
        return str(self.global_settings.get(self.scope))

    def set(self, config):
        setting = self.global_settings.set(self.scope, deepcopy(config))
        return setting
