#!/usr/bin/env python3
# coding=utf-8

import logging
import os
import yaml
import json
from cerberus import Validator
from cerberus.schema import SchemaError
from .sensor_types import *

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'

class NoSensorFoundException(Exception):
    pass

class Sensors():
    def __init__(self, wlanthermo, sensors_dir=None):
        self.logger = logging.getLogger(__name__)
        self.wlanthermo = wlanthermo
        self.sensors_dir = os.path.join(self.wlanthermo.app.config['WLANTHERMO_CONFIG_DIR'], 'sensors')
        self.logger.info('Reading sensor config from {sensors_dir}'.format(sensors_dir=self.sensors_dir))
        if not os.path.exists(self.sensors_dir):
            self.logger.fatal('Sensors config path could not be found ({sensors_dir})'.format(
                sensors_dir=self.sensors_dir))
            raise FileNotFoundError
        self.sensors = dict()
        self.scan_sensors()

    def scan_sensors(self):
        sensors = dict()
        v_sensor = Validator('sensor')
        v_sensor.allow_unknown = True
        for entry_name in sorted(os.listdir(self.sensors_dir)):
            entry_path = os.path.join(self.sensors_dir, entry_name)
            if os.path.isfile(entry_path) and entry_name.endswith('.yaml'):
                self.logger.debug('Loading sensor file "{entry_name}" from "{entry_path}"'.format(
                    entry_name=entry_name,
                    entry_path=entry_path))
                with open(entry_path, 'r') as sensor_file:
                    sensor = yaml.load(sensor_file)
                # Check basic parameters
                if not v_sensor.validate(sensor):
                    self.logger.warning(
                        '"{entry_name}" is not a sensor file, please check format, message: {message}'.format(
                            entry_name=entry_name,
                            message=v_sensor.errors))
                    continue
                try:
                    # Check format matching sensor file
                    sensor_type = sensor['type']
                    type_validator = Validator('sensor_' + sensor_type)
                    type_validator.allow_unknown = True
                    if not type_validator.validate(sensor):
                        self.logger.warning(
                            'Invalid sensor file "{entry_name}" - check parameters! Message: {message}'.format(
                            entry_name=entry_name,
                            message=v_sensor.errors,
                            )
                        )
                        continue
                except SchemaError:
                    # Schema not found
                    self.logger.error('Can´t verify sensor file "{entry_name}" - no matching schema found, skipping!'.format(
                            entry_name=entry_name))
                    continue
                sensors[sensor['name']] = sensor
                self.logger.info('Added sensor "{sensor_name}" of type "{sensor_type}" to list'.format(
                    sensor_name=sensor['name'],
                    sensor_type=sensor['type']))
            else:
                continue

        if not sensors:
            self.logger.fatal('No valid sensor definition found')
            raise NoSensorFoundException('No valid sensor definition found in {sensors_dir}'.format(sensors_dir=self.sensors_dir))

        self.sensors = sensors

    def by_type(self, type):
        retval = {sensor_name: sensor for (sensor_name, sensor) in self.sensors.items() if sensor['type'] == type}
        return retval

    def types(self, types=None):
        if types is None:
            return self.sensors.keys()
        else:
            return [key for key in self.sensors.keys() if key in types]
