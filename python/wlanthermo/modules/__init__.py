#!/usr/bin/python3
# coding=utf-8

# Copyright (c) 2017 Björn Schrader
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from collections import namedtuple
import logging
from wlanthermo.database.tables import *
from flask import jsonify, request

__author__ = 'Björn Schrader <wlanthermo@bjoern-schrader.de>'
__license__ = 'GNU General Public License http://www.gnu.org/licenses/gpl.html'
__copyright__ = 'Copyright (C) 2017 by WLANThermo Project - Released under terms of the GPLv3 License'


class WrongSensorError(Exception):
    pass


class TempCalcError(Exception):
    pass


class NoChannelError(Exception):
    pass


class UnknownSpiModeError(Exception):
    pass


class ResultState(Enum):
    OK = 1
    NONE = 2
    ERR_LO = 3
    ERR_HI = 4
    ERR = 5
    ERR_NOSENSOR = 6
    ERR_NOSUPPT = 7


ChannelResult = namedtuple('ChannelResult',
                           ('module', 'channel', 'state', 'value', 'unit'))


def bytearray_to_int(bytelist):
    """Returns the value of bytelist as if it where a large integer represented as a list of bytes

    >>> bytearray_to_int([0, 1])
    1
    >>> bytearray_to_int([1, 0])
    256
    """
    result = 0
    for byte in bytelist:
        result *= 256
        result += byte
    return result


class Modules():
    def __init__(self, wlanthermo):
        self.wlanthermo = wlanthermo
        self.app = wlanthermo.app
        self.db = wlanthermo.db
        self.logger = logging.getLogger(__name__)

    def register_api(self):
        self.app.add_url_rule('/api/modules/<int:module_id>',
                              view_func=self.get_modules_api)
        self.app.add_url_rule('/api/modules',
                              view_func=self.get_modules_api)
        self.app.add_url_rule('/api/modules',
                              methods=['POST'],
                              view_func=self.register_modules_api)
        self.app.add_url_rule('/api/modules/<int:module_id>/sensors',
                              view_func=self.get_sensor_api)

    def register_modules_api(self):
        content = request.get_json() or request.form
        return jsonify(self.register(content['name'], content.getlist('sensor_types')))

    def register(self, name, sensor_types):
        self.logger.info('Registering module "{name}" to database'.format(name=name))
        module = self.db.session.query(ModulesTable).filter_by(name=name).first()
        if module is None:
            module = ModulesTable(
                name=name,
                sensor_types=sensor_types)
            self.db.session.add(module)
            self.db.session.commit()
            self.logger.debug('Added module "{name}" with id {id} to database'.format(
                name=name,
                id=module.id))
        else:
            self.logger.debug('Found module "{module}" with id {module_id}'.format(
                module=name,
                module_id=module.id))
            module.sensor_types = sensor_types
            module.last_seen = datetime.datetime.utcnow()
            self.db.session.commit()

        return module.id


    def get_modules_api(self, module_id=None):
        return jsonify(self.get(module_id))


    def get(self, module_id=None):
        query = self.db.session.query(ModulesTable)
        if module_id is not None:
            query = query.filter(ModulesTable.id == module_id)
            modules = query.first()
            return modules._asdict()
        else:
            db_result = query.order_by(ModulesTable.id).all()
            result = dict()
            for modules in db_result:
                result[modules.id] = modules._asdict()
            return result


    def get_sensor_api(self, module_id):
        return jsonify(self.get_sensors(module_id))


    def get_sensors(self, module_id):
        module = self.db.session.query(ModulesTable).filter(ModulesTable.id == module_id).first()
        sensors = []
        for sensor_type in module.sensor_types:
            sensors.extend(self.wlanthermo.sensors.by_type(sensor_type).keys())
        return sensors

